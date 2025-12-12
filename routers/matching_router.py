from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime

from db import get_db
import models, schemas

router = APIRouter(prefix="/matching", tags=["Matching"])

@router.get("/excluded-users/{current_user_id}")
def get_excluded_users(
    current_user_id: int,
    db: Session = Depends(get_db)
):
    """
    Retorna los IDs de usuarios que el usuario actual ya ha swipeado.
    El API Gateway usará esto para filtrar.
    """
    # Get list of users already swiped on
    already_swiped = db.query(models.Swiped_Users.swiped_user_fk).filter(
        models.Swiped_Users.current_user_fk == current_user_id
    ).all()
    
    already_swiped_ids = [profile[0] for profile in already_swiped]
    excluded_ids = already_swiped_ids + [current_user_id]
    
    return {"excluded_ids": excluded_ids}

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
    
    # Verificar si ya hizo swipe a este usuario
    existing_swipe = db.query(models.Swiped_Users).filter(
        models.Swiped_Users.current_user_fk == current_user_id,
        models.Swiped_Users.swiped_user_fk == swipe.user_id
    ).first()
        
    if existing_swipe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already swiped on this user"
        )
    
    # Guardar el swipe
    new_swipe = models.Swiped_Users(
        current_user_fk=current_user_id,
        swiped_user_fk=swipe.user_id,
        is_like=swipe.is_like,
        swipe_date = datetime.today()
    )
    
    db.add(new_swipe)
    db.commit()
    
    # Verificar si hay MATCH (el otro usuario también dio like)
    is_match = False
    
    if swipe.is_like:  # Solo verificar match si este usuario dio like
        other_user_swipe = db.query(models.Swiped_Users).filter(
            models.Swiped_Users.current_user_fk == swipe.user_id,
            models.Swiped_Users.swiped_user_fk == current_user_id,
            models.Swiped_Users.is_like == True
        ).first()
        
        if other_user_swipe:
            # ¡HAY MATCH! Crear la relación
            is_match = True
            
            # Obtener o crear el estado "matched"
            matched_state = db.query(models.Relationship_State).filter(
                models.Relationship_State.state == "matched"
            ).first()
            
            if not matched_state:
                matched_state = models.Relationship_State(state="matched")
                db.add(matched_state)
                db.commit()
                db.refresh(matched_state)
            
            # Crear la relación de pareja
            new_relationship = models.Couple_Relationship(
                first_user_fk=current_user_id,
                second_user_fk=swipe.user_id,
                state_fk=matched_state.id,
                creation_date=int(datetime.now().timestamp())
            )
            db.add(new_relationship)
            db.commit()
    
    response = schemas.SwipeResponse(
        sender_user_id=current_user_id,
        reciever_user_id=swipe.user_id,
        swiped_at=datetime.today(),
        is_match=is_match
    )
    return response


@router.get("/relationships/check", response_model=schemas.RelationshipCheckResponse)
def check_relationship(
    user1_id: int = Query(..., description="ID del primer usuario"),
    user2_id: int = Query(..., description="ID del segundo usuario"),
    db: Session = Depends(get_db)
):
    """
    Verifica si existe una relación (match) entre dos usuarios.
    """
    # Buscar relación en ambas direcciones
    relationship = db.query(models.Couple_Relationship).filter(
        or_(
            and_(
                models.Couple_Relationship.first_user_fk == user1_id,
                models.Couple_Relationship.second_user_fk == user2_id
            ),
            and_(
                models.Couple_Relationship.first_user_fk == user2_id,
                models.Couple_Relationship.second_user_fk == user1_id
            )
        )
    ).first()
    
    if not relationship:
        return schemas.RelationshipCheckResponse(exists=False)
    
    # Obtener el estado
    state = db.query(models.Relationship_State).filter(
        models.Relationship_State.id == relationship.state_fk
    ).first()
    
    return schemas.RelationshipCheckResponse(
        exists=True,
        relationship_id=relationship.id,
        user1_id=relationship.first_user_fk,
        user2_id=relationship.second_user_fk,
        state=state.state if state else "unknown",
        creation_date=relationship.creation_date
    )


@router.get("/relationships/user/{user_id}/active", response_model=schemas.ActiveRelationshipResponse)
def get_active_relationship(
    user_id: int,
    db: Session = Depends(get_db)
):
    """
    Obtiene la relación activa (match) de un usuario.
    Un usuario solo puede tener un match activo a la vez.
    """
    # Obtener el estado "matched"
    matched_state = db.query(models.Relationship_State).filter(
        models.Relationship_State.state == "matched"
    ).first()
    
    if not matched_state:
        return schemas.ActiveRelationshipResponse(has_active_match=False)
    
    # Buscar relación activa
    relationship = db.query(models.Couple_Relationship).filter(
        or_(
            models.Couple_Relationship.first_user_fk == user_id,
            models.Couple_Relationship.second_user_fk == user_id
        ),
        models.Couple_Relationship.state_fk == matched_state.id
    ).first()
    
    if not relationship:
        return schemas.ActiveRelationshipResponse(has_active_match=False)
    
    # Determinar quién es el partner
    partner_id = (
        relationship.second_user_fk 
        if relationship.first_user_fk == user_id 
        else relationship.first_user_fk
    )
    
    return schemas.ActiveRelationshipResponse(
        has_active_match=True,
        relationship_id=relationship.id,
        user1_id=relationship.first_user_fk,
        user2_id=relationship.second_user_fk,
        partner_id=partner_id,
        state="matched",
        creation_date=relationship.creation_date
    )