from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session

from db import SessionLocal
import models


def create_couple_relationship(db: Session, first_user_fk: int, second_user_fk: int, state_fk: int, creation_date: Optional[int] = None) -> models.Couple_Relationship:
    creation_date_val = creation_date if creation_date is not None else int(datetime.timestamp())
    db_obj = models.Couple_Relationship(
        first_user_fk=first_user_fk,
        second_user_fk=second_user_fk,
        state_fk=state_fk,
        creation_date=creation_date_val,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_couple_relationship(db: Session, rel_id: int) -> Optional[models.Couple_Relationship]:
    return db.query(models.Couple_Relationship).filter(models.Couple_Relationship.id == rel_id).first()


def list_couple_relationships(db: Session, skip: int = 0, limit: int = 100) -> List[models.Couple_Relationship]:
    return db.query(models.Couple_Relationship).offset(skip).limit(limit).all()


def get_relationships_for_user(db: Session, user_id: int) -> List[models.Couple_Relationship]:
    return db.query(models.Couple_Relationship).filter(
        (models.Couple_Relationship.first_user_fk == user_id) | (models.Couple_Relationship.second_user_fk == user_id)
    ).all()


def update_couple_relationship_state(db: Session, rel_id: int, new_state_fk: int) -> Optional[models.Couple_Relationship]:
    obj = get_couple_relationship(db, rel_id)
    if not obj:
        return None
    obj.state_fk = new_state_fk
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def delete_couple_relationship(db: Session, rel_id: int) -> bool:
    obj = get_couple_relationship(db, rel_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


def create_relationship_state(db: Session, state: str) -> models.Relationship_State:
    db_obj = models.Relationship_State(state=state)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_relationship_state(db: Session, state_id: int) -> Optional[models.Relationship_State]:
    return db.query(models.Relationship_State).filter(models.Relationship_State.id == state_id).first()


def get_relationship_state_by_name(db: Session, state_name: str) -> Optional[models.Relationship_State]:
    return db.query(models.Relationship_State).filter(models.Relationship_State.state == state_name).first()


def list_relationship_states(db: Session, skip: int = 0, limit: int = 100) -> List[models.Relationship_State]:
    return db.query(models.Relationship_State).offset(skip).limit(limit).all()


def delete_relationship_state(db: Session, state_id: int) -> bool:
    obj = get_relationship_state(db, state_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


def create_like(db: Session, sender_user_fk: int, liked_user_fk: int, link_date: Optional[datetime] = None) -> models.Liked_Users:
    link_date_val = link_date if link_date is not None else datetime.utcnow()
    db_obj = models.Liked_Users(sender_user_fk=sender_user_fk, liked_user_fk=liked_user_fk, link_date=link_date_val)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


def get_like(db: Session, like_id: int) -> Optional[models.Liked_Users]:
    return db.query(models.Liked_Users).filter(models.Liked_Users.id == like_id).first()


def find_like(db: Session, sender_user_fk: int, liked_user_fk: int) -> Optional[models.Liked_Users]:
    return db.query(models.Liked_Users).filter(
        models.Liked_Users.sender_user_fk == sender_user_fk,
        models.Liked_Users.liked_user_fk == liked_user_fk,
    ).first()


def list_likes_by_sender(db: Session, sender_user_fk: int) -> List[models.Liked_Users]:
    return db.query(models.Liked_Users).filter(models.Liked_Users.sender_user_fk == sender_user_fk).all()


def list_likes_for_user(db: Session, liked_user_fk: int) -> List[models.Liked_Users]:
    return db.query(models.Liked_Users).filter(models.Liked_Users.liked_user_fk == liked_user_fk).all()


def delete_like(db: Session, like_id: int) -> bool:
    obj = get_like(db, like_id)
    if not obj:
        return False
    db.delete(obj)
    db.commit()
    return True


__all__ = [
    "create_couple_relationship",
    "get_couple_relationship",
    "list_couple_relationships",
    "get_relationships_for_user",
    "update_couple_relationship_state",
    "delete_couple_relationship",
    "create_relationship_state",
    "get_relationship_state",
    "get_relationship_state_by_name",
    "list_relationship_states",
    "delete_relationship_state",
    "create_like",
    "get_like",
    "find_like",
    "list_likes_by_sender",
    "list_likes_for_user",
    "delete_like",
]
