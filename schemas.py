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
    # Add photo URLs, distance, etc. later

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


