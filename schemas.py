from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class PotentialMatchProfile(BaseModel):
    id: int
    username: str
    age: int
    sexual_orientation_id:int
    interests: list[str]


class PotentialMatchesResponse(BaseModel):
    profiles: list[PotentialMatchProfile]
    count: int


class SwipeData(BaseModel):
    user_id: int
    is_like: bool
    date: datetime

    
class SwipeResponse(BaseModel):
    sender_user_id: int
    reciever_user_id: int
    swiped_at: datetime
    is_match: bool
    
    class Config:
        from_attributes = True


class RelationshipCheckResponse(BaseModel):
    exists: bool
    relationship_id: Optional[int] = None
    user1_id: Optional[int] = None
    user2_id: Optional[int] = None
    state: Optional[str] = None
    creation_date: Optional[datetime] = None


class ActiveRelationshipResponse(BaseModel):
    has_active_match: bool
    relationship_id: Optional[int] = None
    user1_id: Optional[int] = None
    user2_id: Optional[int] = None
    partner_id: Optional[int] = None
    state: Optional[str] = None
    creation_date: Optional[datetime] = None

