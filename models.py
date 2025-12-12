from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from db import Base


class Couple_Relationship(Base):
    __tablename__ = "Couple_Relationship"
    
    id = Column(Integer, primary_key=True, index=True)
    first_user_fk =  Column(Integer, nullable=False)
    second_user_fk = Column(Integer, nullable=False)
    state_fk = Column(Integer, ForeignKey('Relationship_State.id'), nullable=False)
    update = Column(DateTime, onupdate=func.now())
    creation_date = Column(Integer)
    

class Relationship_State(Base):
    __tablename__ = "Relationship_State"
    
    id = Column(Integer, primary_key=True, index=True)
    state = Column(String(10), nullable=False)
    
class Swiped_Users(Base):
    __tablename__ = "Swiped_Users"
    
    current_user_fk = Column(Integer, primary_key=True, index=True)
    swiped_user_fk = Column(Integer, primary_key=True, index=True)
    is_like = Column(Boolean, nullable=False)
    swipe_date = Column(DateTime, nullable=False)
