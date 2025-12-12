from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class PotentialMatchProfile(BaseModel):
    """A potential match candidate"""
    id: int
    username: str
    age: int
    sexual_orientation_id:int
    interests: list[str]


class PotentialMatchesResponse(BaseModel):
    """List of potential matches"""
    profiles: list[PotentialMatchProfile]
    count: int


class SwipeData(BaseModel):
    """Data related to the ignored user by current"""
    user_id: int
    is_like: bool
    date: datetime

    
class SwipeResponse(BaseModel):
    """Uninterest user for the current one"""
    sender_user_id: int
    reciever_user_id: int
    swiped_at: datetime
    is_match: bool
    
    class Config:
        from_attributes = True


class RelationshipCheckResponse(BaseModel):
    """Respuesta al verificar si existe una relación entre dos usuarios"""
    exists: bool
    relationship_id: Optional[int] = None
    user1_id: Optional[int] = None
    user2_id: Optional[int] = None
    state: Optional[str] = None
    creation_date: Optional[int] = None


class ActiveRelationshipResponse(BaseModel):
    """Respuesta con la relación activa de un usuario"""
    has_active_match: bool
    relationship_id: Optional[int] = None
    user1_id: Optional[int] = None
    user2_id: Optional[int] = None
    partner_id: Optional[int] = None
    state: Optional[str] = None
    creation_date: Optional[int] = None

