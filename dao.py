from typing import List, Optional
from datetime import datetime
import httpx
from sqlalchemy.orm import Session
from config import settings

from db import SessionLocal
import models


# ============================================================================
# User Service Integration Functions (for recomendations.py)
# ============================================================================

async def get_user(db: Session, user_id: int):
    """Fetch user profile from user service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.USER_SERVICE_URL}/user/profiles")
        if response.status_code != 200:
            return None
        profiles = response.json()
        # Find the profile with matching user_id
        for profile in profiles:
            if profile.get("id") == user_id:
                return profile
        return None
    except Exception:
        return None


async def list_all_users(db: Session) -> List[int]:
    """Get all user IDs from user service"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.USER_SERVICE_URL}/user/profiles")
        if response.status_code != 200:
            return []
        profiles = response.json()
        return [user.get("id") for user in profiles if user.get("id")]
    except Exception:
        return []


async def list_user_masc_hetero(db: Session) -> List[int]:
    """Get user IDs recommendable to heterosexual males"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.USER_SERVICE_URL}/user/profiles/recommend/male-hetero")
        if response.status_code != 200:
            return []
        return response.json()
    except Exception:
        return []


async def list_user_masc_homo(db: Session) -> List[int]:
    """Get user IDs recommendable to homosexual males"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.USER_SERVICE_URL}/user/profiles/recommend/male-homo")
        if response.status_code != 200:
            return []
        return response.json()
    except Exception:
        return []


async def list_user_masc_bi(db: Session) -> List[int]:
    """Get user IDs recommendable to bisexual males"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.USER_SERVICE_URL}/user/profiles/recommend/male-bi")
        if response.status_code != 200:
            return []
        return response.json()
    except Exception:
        return []


async def list_user_fem_hete(db: Session) -> List[int]:
    """Get user IDs recommendable to heterosexual females"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.USER_SERVICE_URL}/user/profiles/recommend/female-hetero")
        if response.status_code != 200:
            return []
        return response.json()
    except Exception:
        return []


async def list_user_fem_homo(db: Session) -> List[int]:
    """Get user IDs recommendable to homosexual females"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.USER_SERVICE_URL}/user/profiles/recommend/female-homo")
        if response.status_code != 200:
            return []
        return response.json()
    except Exception:
        return []


async def list_user_fem_bi(db: Session) -> List[int]:
    """Get user IDs recommendable to bisexual females"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.USER_SERVICE_URL}/user/profiles/recommend/female-bi")
        if response.status_code != 200:
            return []
        return response.json()
    except Exception:
        return []


async def get_user_interests(db: Session, user_id: int) -> List[int]:
    """Get interest IDs for a user"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.USER_SERVICE_URL}/user/{user_id}/interests")
        if response.status_code != 200:
            return []
        data = response.json()
        return data.get("interest_ids", [])
    except Exception:
        return []


# ============================================================================
# Couple Relationship Management Functions (existing code)
# ============================================================================

def create_couple_relationship(db: Session, first_user_fk: int, second_user_fk: int, state_fk: int, creation_date: Optional[int] = None) -> models.Couple_Relationship:
    """Create a new Couple_Relationship and return it."""
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


def get_couple_relationship_between_users(db: Session, user1_fk: int, user2_fk: int) -> Optional[models.Couple_Relationship]:
    return db.query(models.Couple_Relationship).filter(
        ((models.Couple_Relationship.first_user_fk == user1_fk) & (models.Couple_Relationship.second_user_fk == user2_fk)) |
        ((models.Couple_Relationship.first_user_fk == user2_fk) & (models.Couple_Relationship.second_user_fk == user1_fk))
    ).first()


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

def update_relationship_state(db: Session, state_id: int, new_state: str):
    obj = get_relationship_state(db, state_id)
    if not obj:
        return None
    obj.state = new_state
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj

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
