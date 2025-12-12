from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime
import httpx

from db import get_db
import models, schemas
from config import settings

router = APIRouter(prefix="/matching", tags=["Matching"])

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
            
            if response.status_code == 200:
                profiles_data = response.json()
                filtered_profiles = [profile for profile in profiles_data if not profile["id"] in excluded_ids]
                next_recomendation = [filtered_profiles[0]]
                return schemas.PotentialMatchesResponse(
                    profiles=[schemas.PotentialMatchProfile(**p) for p in next_recomendation],
                    count=len(profiles_data)
                )
    except httpx.RequestError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Profile service unavailable"
        )
    
    # Fallback empty response
    return schemas.PotentialMatchesResponse(profiles=[], count=0)

@router.post("/swipe", response_model=schemas.SwipeResponse, status_code=status.HTTP_201_CREATED)
def swipe_user(
    swipe: schemas.SwipeData,
    current_user_id: int = Query(..., description="ID of user that ignored other"),
    db : Session = Depends(get_db)
):
    if current_user_id == swipe.user_id:
        # Raise an HTTP 400 Bad Request error
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
    ).all()
    
    
    # if swiped_user_like: is_match = swipe.is_like and swiped_user_like[0]
    is_match = False
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