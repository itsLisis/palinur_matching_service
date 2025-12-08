from datetime import datetime
from unittest.mock import MagicMock

import pytest

import match
import dao


def test_like_user_triggers_match_when_reverse_like_exists(monkeypatch):
    db = MagicMock()
    sender = 1
    liked = 2

    # create_like returns a truthy object on success
    monkeypatch.setattr(dao, "create_like", lambda db_arg, s, l, link_date=None: {"id": 10})

    # find_like returns a value only when checking reverse like (liked -> sender)
    def fake_find_like(db_arg, s, l):
        if s == liked and l == sender:
            return {"id": 11}
        return None

    monkeypatch.setattr(dao, "find_like", fake_find_like)

    # Capture that relationship creation is triggered
    called = {"relationship_created": False}

    def fake_create_relationship_state(db_arg, state):
        return MagicMock(id=5)

    def fake_create_couple_relationship(db_arg, u1, u2, state_id, link_date):
        called["relationship_created"] = True
        # verify link_date is a datetime
        assert isinstance(link_date, datetime)
        return MagicMock(id=20)

    monkeypatch.setattr(dao, "create_relationship_state", fake_create_relationship_state)
    monkeypatch.setattr(dao, "create_couple_relationship", fake_create_couple_relationship)

    result = match.like_user(db, sender, liked)
    assert result is True
    assert called["relationship_created"] is True


def test_create_match_returns_true_and_uses_timestamp(monkeypatch):
    db = MagicMock()

    monkeypatch.setattr(dao, "create_relationship_state", lambda db_arg, s: MagicMock(id=1))

    captured = {}

    def fake_create_couple_relationship(db_arg, u1, u2, state_id, link_date):
        captured["link_date"] = link_date
        return MagicMock(id=2)

    monkeypatch.setattr(dao, "create_couple_relationship", fake_create_couple_relationship)

    assert match.create_match(db, 1, 2) is True
    assert isinstance(captured["link_date"], datetime)


def test_break_match_updates_state_when_relationship_exists(monkeypatch):
    db = MagicMock()

    relationship = MagicMock(state_fk=99)
    monkeypatch.setattr(dao, "get_couple_relationship_between_users", lambda db_arg, u1, u2: relationship)
    monkeypatch.setattr(dao, "update_relationship_state", lambda db_arg, state_fk, new_state: MagicMock(id=1))

    assert match.break_match(db, 1, 2) is True


def test_break_match_returns_false_when_no_relationship(monkeypatch):
    db = MagicMock()
    monkeypatch.setattr(dao, "get_couple_relationship_between_users", lambda db_arg, u1, u2: None)
    assert match.break_match(db, 1, 2) is False
