from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime
import httpx

from db import get_db
import models, schemas
from config import settings

router = APIRouter(prefix="/matching", tags=["Matching"])

async def are_compatible(current_profile, other_profile):
    try:
        async with httpx.AsyncClient() as client:
            genders_data = await client.get(
                f"{settings.USER_SERVICE_URL}/genders_data",
                timeout=10.0
            )
            sexual_orientations_data = await client.get(
                f"{settings.USER_SERVICE_URL}/sexual_orientations_data",
                timeout=10.0
            )
    except httpx.RequestError:
        raise HTTPException (
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="User Microservice is unavailable"
        )
    
    # for gender in genders_data.json():
    #     if current_profile["gender_id"] == gender["id"]:
    #         current_user_gender = gender["gender_name"]
    #     if other_profile["gender_id"] == gender["id"]:
    #         other_profile_gender = gender["gender_name"]
    
    # for sexual_orientation in sexual_orientations_data.json():
    #     if current_profile["sexual_orientation_id"] == sexual_orientation["id"]:
    #         current_user_orientation = sexual_orientation["orientation_name"]
    #     if other_profile["sexual_orientation_id"] == sexual_orientation["id"]:
    #         other_user_orientation = sexual_orientation["orientation_name"]
    
    # match current_user_orientation:
    #     case "hetero":
    #         if current_user_gender == "Masculino":
    return True
    
    
@router.get("/potential", response_model=schemas.PotentialMatchesResponse)
async def get_potential_matches(
    current_user_id: int = Query(..., description="ID of the user"),
    db: Session = Depends(get_db)
):
    """
    Get potential matches for a user
    - Excludes already swiped users
    - Excludes blocked users
    - Excludes existing matches
    """
    
    # Get list of users already swiped on
    already_swiped = db.query(models.Swiped_Users.swiped_user_fk).filter(
        models.Swiped_Users.current_user_fk == current_user_id
    ).all()
    
    already_swiped_ids = [profile[0] for profile in already_swiped]
    excluded_ids = set(already_swiped_ids + 
                       [current_user_id])
    
    # Fetch profiles from User Service
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.USER_SERVICE_URL}/user/profiles",
                timeout=10.0
            )
            
            if not response.status_code == 200: 
                return schemas.PotentialMatchesResponse(profiles=[], count=0)
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Profiles service unavailable"
        )
    current_profile_response = None
    try:
        async with httpx.AsyncClient() as client:
            current_profile_response = await client.get(
                f"{settings.USER_SERVICE_URL}/user/profile",
                timeout=100.
            )
            if not current_profile_response: raise ValueError("No found profile")
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Profile service unavailable"
        )
    
    profiles_data = response.json()
    current_profile_data = current_profile_response.json()
    
    filtered_profiles = []
    for profile in profiles_data:
        if profile["id"] not in excluded_ids and await are_compatible(current_profile_data, profile):
            filtered_profiles.append(profile)
        
    next_recomendation = [filtered_profiles[0]]
    return schemas.PotentialMatchesResponse(
        profiles=[schemas.PotentialMatchProfile(**p) for p in next_recomendation],
        count=len(profiles_data)
    )
    

@router.post("/swipe", response_model=schemas.SwipeResponse, status_code=status.HTTP_201_CREATED)
def swipe_user(
    swipe: schemas.SwipeData,
    current_user_id: int = Query(..., description="ID of user that ignored other"),
    db : Session = Depends(get_db)
):
    if current_user_id == swipe.user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot swipe on yourself"
        )
    
    existing_swipe = db.query(models.Swiped_Users).filter(
        models.Swiped_Users.current_user_fk == current_user_id,
        models.Swiped_Users.swiped_user_fk == swipe.user_id
    ).first()
        
    if existing_swipe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already swiped on this user"
        )
        
    swiped_user_like = db.query(models.Swiped_Users.is_like).filter(
        models.Swiped_Users.current_user_fk==swipe.user_id,
        models.Swiped_Users.swiped_user_fk==current_user_id
    ).first()
    
    is_match = False
    if swiped_user_like: is_match = swipe.is_like and swiped_user_like[0]
    
    new_swipe = models.Swiped_Users(
        current_user_fk=current_user_id,
        swiped_user_fk=swipe.user_id,
        is_like=swipe.is_like,
        swipe_date = datetime.today()
    )
    
    db.add(new_swipe)
    db.commit()
    db.refresh(new_swipe)
    
    response = schemas.SwipeResponse(
        sender_user_id=current_user_id,
        reciever_user_id=swipe.user_id,
        swiped_at=datetime.today(),
        is_match=is_match
    )
    return response

@router.post("/change_match_state", status_code=status.HTTP_200_OK)
def change_match_state(
    match_id: int,
    state:str,
    db: Session = Depends(get_db)
):
    state_id = db.query(models.Relationship_State.id).filter(
        models.Relationship_State.state == state
    ).first()
    
    if not state_id: raise ValueError(f"No such match state {state}")
    else: state_id = state_id[0]
    
    target_match = db.query(models.Couple_Relationship).filter(
        models.Relationship_State.id == match_id
    ).first()
    
    if not target_match: raise ValueError(f"No such present relationship {match_id}")
    else: target_match.state_fk = state_id
    
    db.add(target_match)
    db.commit()
    db.refresh(target_match)
    
    return {
        "message":"Match state chagned",
        "new match state": state_id
    }

@router.get("/get_match_state")
def get_match_state(
    match_id: int,
    db: Session = Depends(get_db)
):
    match_state_id = db.query(models.Couple_Relationship.state_fk).filter(
        models.Couple_Relationship.id == match_id
    ).first()
    
    if not match_state_id: return None
    else: match_state_id = match_state_id[0]
    
    state_name = db.query(models.Relationship_State.state).filter(
        models.Relationship_State.id == match_state_id
    ).first()
    
    if not state_name: raise ValueError(f"No relationship state found with id: {match_state_id}")
    return state_name[0]

@router.post("/save_match", status_code=status.HTTP_201_CREATED)
def save_match(
    first_user_id: int,
    second_user_id: int,
    db: Session = Depends(get_db)
):
    active_id = db.query(models.Relationship_State.id).filter(
        models.Relationship_State.state == "active"
    ).first()
    
    if active_id: active_id = active_id[0]
    else: raise KeyError("No found active relationship state id")
    
    new_match = models.Couple_Relationship(
        first_user_fk=first_user_id,
        second_user_fk=second_user_id,
        state_fk=active_id,
        creation_date=datetime.today()
    )
    
    db.add(new_match)
    db.commit()
    db.refresh(new_match)
    
    return {
        "message": "New match created succesfully",
        "first_user_fk": first_user_id,
        "second_user_fk": second_user_id,
        "state_id":active_id
    }