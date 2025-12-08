from typing import List, Optional
from datetime import datetime

from sqlalchemy.orm import Session
import dao


def like_user(db: Session, sender_user_fk: int, liked_user_fk: int, link_date: Optional[datetime] = None):
    
    like = dao.create_like(Session, sender_user_fk, liked_user_fk, link_date)

    if check_like_exists(db, liked_user_fk, sender_user_fk):
        create_match(db, sender_user_fk, liked_user_fk) 

    return like is not None

def check_like_exists(db: Session, sender_user_fk: int, liked_user_fk: int) -> bool:
    like = dao.find_like(db, sender_user_fk, liked_user_fk)
    return like is not None

def create_match(db: Session, user1_fk: int, user2_fk: int):
    relacionship_state = dao.create_relationship_state(db, "matched")
    relacionship = dao.create_couple_relationship(db, user1_fk, user2_fk, relacionship_state.id, datetime.now())

    return relacionship is not None

def break_match(db: Session, user1_fk: int, user2_fk: int):

    relacionship = dao.get_couple_relationship_between_users(db, user1_fk, user2_fk)

    if relacionship:
        state = dao.update_relationship_state(db, relacionship.state_fk, "broken")
        return state is not None
    
    return False