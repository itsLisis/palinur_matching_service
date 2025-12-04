from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db import get_db
import models, schemas
from config import settings
import httpx
import recomendations

router = APIRouter(prefix="/matching", tags=["Matching"])

@router.get("/users")
async def list_all_users():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{settings.USER_SERVICE_URL}/user/profiles")

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to fetch users"
            )

        profiles = response.json()
        # Expecting a list of profile dicts containing an 'id' field
        return [user.get("id") for user in profiles]

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"User service unavailable: {str(e)}"
        )

@router.get("/recommend/male-hetero")
async def list_user_masc_hetero():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.USER_SERVICE_URL}/user/profiles/recommend/male-hetero"
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to fetch recommendations"
            )

        return response.json()

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"User service unavailable: {str(e)}"
        )

@router.get("/recommend/male-homo")
async def list_user_masc_homo():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.USER_SERVICE_URL}/user/profiles/recommend/male-homo"
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to fetch recommendations"
            )

        return response.json()

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"User service unavailable: {str(e)}"
        )

@router.get("/recommend/male-bi")
async def list_user_masc_bi():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{settings.USER_SERVICE_URL}/user/profiles/recommend/male-bi"
            )

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to fetch recommendations"
            )

        return response.json()

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"User service unavailable: {str(e)}"
        )

@router.get("/user/{user_id}/interests")
async def get_user_interests(user_id: int):
    """Fetch interests for a given user id from the user service."""
    try:
        async with httpx.AsyncClient() as client:
            # Prefer RESTful path: /user/{user_id}/interests
            response = await client.get(f"{settings.USER_SERVICE_URL}/user/{user_id}/interests")

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail="Failed to get user interests"
            )

        return response.json()

    except httpx.RequestError as e:
        raise HTTPException(
            status_code=503,
            detail=f"User service unavailable: {str(e)}"
        )


@router.get("/recommendations/{user_id}")
async def get_recommendations(
    user_id: int,
    exclude: str = "",
    limit: int = None,
    db: Session = Depends(get_db)
):
    """
    Get personalized recommendations for a user based on sexual orientation and interest similarity.
    
    Args:
        user_id: The ID of the user to get recommendations for
        exclude: Comma-separated list of user IDs to exclude from recommendations
        limit: Maximum number of recommendations to return
        db: Database session
    
    Returns:
        List of recommended user IDs ordered by interest similarity (highest first)
    """
    try:
        # Parse exclude parameter
        exclude_set = set()
        if exclude:
            exclude_set = set(int(uid.strip()) for uid in exclude.split(",") if uid.strip())
        
        # Get recommendations using the recomendations module
        recommended_ids = await recomendations.recommend_users(
            db=db,
            user_id=user_id,
            exclude=exclude_set,
            limit=limit
        )
        
        return {
            "user_id": user_id,
            "recommendations": recommended_ids,
            "count": len(recommended_ids)
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating recommendations: {str(e)}"
        )

