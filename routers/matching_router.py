from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func
from datetime import datetime
from typing import List, Dict, Any
import logging
import random

from db import get_db
import models, schemas

# Use uvicorn logger so logs show up in docker-compose logs reliably
logger = logging.getLogger("uvicorn.error")

router = APIRouter(prefix="/matching", tags=["Matching"])

@router.get("/excluded-users/{current_user_id}")
def get_excluded_users(
    current_user_id: int,
    only_recent: bool = Query(default=True, description="Solo excluir swipes recientes"),
    db: Session = Depends(get_db)
):
    query = db.query(models.Swiped_Users.swiped_user_fk).filter(
        models.Swiped_Users.current_user_fk == current_user_id
    ).order_by(models.Swiped_Users.swipe_date.desc())
    
    if only_recent:
        already_swiped = query.limit(10).all()
    else:
        already_swiped = query.all()
    
    already_swiped_ids = [profile[0] for profile in already_swiped]
    
    excluded_ids = already_swiped_ids + [current_user_id]
    
    active_state = db.query(models.Relationship_State).filter(
        models.Relationship_State.state == "active"
    ).first()
    
    if active_state:
        active_matches = db.query(models.Couple_Relationship).filter(
            or_(
                models.Couple_Relationship.first_user_fk == current_user_id,
                models.Couple_Relationship.second_user_fk == current_user_id
            ),
            models.Couple_Relationship.state_fk == active_state.id
        ).all()
        
        for match in active_matches:
            partner_id = match.second_user_fk if match.first_user_fk == current_user_id else match.first_user_fk
            if partner_id not in excluded_ids:
                excluded_ids.append(partner_id)
    
    return {"excluded_ids": excluded_ids}


def jaccard_similarity(interests_a: List[str], interests_b: List[str]) -> float:
    """Calcula la similitud de Jaccard entre dos listas de intereses"""
    set_a = set(interests_a)
    set_b = set(interests_b)
    
    if not set_a and not set_b:
        return 0.0
    
    if not set_a or not set_b:
        return 0.0
    
    intersection = len(set_a & set_b)
    union = len(set_a | set_b)
    
    return intersection / union if union > 0 else 0.0


@router.post("/filter-compatible")
def filter_compatible_profiles(
    data: Dict[str, Any] = Body(...)
):

    current_user = data.get("current_user")
    profiles = data.get("profiles", [])
    excluded_ids = data.get("excluded_ids", [])
    allow_recycling = data.get("allow_recycling", True)  # Permitir usuarios ya vistos
    
    if not current_user:
        raise HTTPException(status_code=400, detail="current_user es requerido")
    
    user_id = current_user.get("id")
    user_gender = current_user.get("gender")
    user_gender_id = current_user.get("gender_id")
    user_sexual_orientation = current_user.get("sexual_orientation")
    user_sexual_orientation_id = current_user.get("sexual_orientation_id")
    user_interests = current_user.get("interests", [])

    # En el frontend ya se asume este mapeo (ver Ajustes.jsx): 1=hombre, 2=mujer, resto="Otro"
    MALE_ID = 1
    FEMALE_ID = 2

    def _normalize_str(v: Any) -> str:
        return str(v).strip().lower() if v is not None else ""

    def target_gender_ids_for_user() -> set[int] | None:
        """
        Versión robusta basada en `gender_id` (numérico), para no depender de strings.
        En este proyecto, `sexual_orientation_id` representa la preferencia de a quién ver:
        0=Hombres, 1=Mujeres, 2=No binarixs.
        """
        if not isinstance(user_sexual_orientation_id, int):
            return None

        # Preferencia: Hombres
        if user_sexual_orientation_id == 0:
            return {MALE_ID}
        # Preferencia: Mujeres
        if user_sexual_orientation_id == 1:
            return {FEMALE_ID}
        # Preferencia: No binarixs -> NO tenemos un id fijo, así que lo tratamos como "no (1 o 2)"
        # y lo resolvemos en el filtro con una regla especial.
        if user_sexual_orientation_id == 2:
            return set()

        return None

    target_gender_ids = target_gender_ids_for_user()

    def is_compatible(profile: Dict[str, Any]) -> bool:
        pid = profile.get("id")
        if pid is None:
            return False

        if pid == user_id:
            return False

        # Filtro fuerte por género objetivo (basado en sexual_orientation_id):
        # - target_gender_ids == {1} => solo hombres
        # - target_gender_ids == {2} => solo mujeres
        # - target_gender_ids == set() => "no binarixs": todo lo que NO sea 1 o 2
        if target_gender_ids is not None:
            pgid = profile.get("gender_id")
            if not isinstance(pgid, int):
                return False

            # No binarixs: aceptar cualquier id distinto a 1/2
            if user_sexual_orientation_id == 2:
                if pgid in {MALE_ID, FEMALE_ID}:
                    return False
            else:
                if pgid not in target_gender_ids:
                    return False

        return True
    
    all_other_users = [p for p in profiles if p["id"] != user_id]
    
    logger.info(
        f"[filter-compatible] user_id={user_id} total={len(profiles)} others={len(all_other_users)} "
        f"excluded={len(excluded_ids)} user_gender_id={user_gender_id} user_so_id={user_sexual_orientation_id} "
        f"user_gender={user_gender} user_so={user_sexual_orientation}"
    )
    
    compatible_profiles = [profile for profile in all_other_users if is_compatible(profile)]
    logger.info(
        f"[filter-compatible] compatible={len(compatible_profiles)} "
        f"(target_gender_ids={sorted(list(target_gender_ids)) if target_gender_ids is not None else None} "
        f"user_preference_so_id={user_sexual_orientation_id} user_preference_so={_normalize_str(user_sexual_orientation)})"
    )

    # Nunca hacer fallback a perfiles incompatibles por género.
    if not compatible_profiles:
        return {"profiles": [], "count": 0, "is_recycled": False}
    
    new_compatible = [p for p in compatible_profiles if p["id"] not in excluded_ids]
    recycled_compatible = [p for p in compatible_profiles if p["id"] in excluded_ids]
    
    if new_compatible:
        profiles_to_rank = new_compatible
        is_recycled = False
    elif recycled_compatible and allow_recycling:
        profiles_to_rank = recycled_compatible
        is_recycled = True
    else:
        profiles_to_rank = []
        is_recycled = False
    
    profiles_with_score = []
    for profile in profiles_to_rank:
        profile_interests = profile.get("interests", [])
        similarity_score = jaccard_similarity(user_interests, profile_interests)
        # Add a small random jitter so profiles with same score don't always keep the same order
        profiles_with_score.append((profile, similarity_score, random.random()))
    
    profiles_with_score.sort(key=lambda x: (x[1], x[2]), reverse=True)
    
    ranked_profiles = [profile for profile, score, _ in profiles_with_score]
    
    return {
        "profiles": ranked_profiles,
        "count": len(ranked_profiles),
        "is_recycled": is_recycled
    }


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
        existing_swipe.is_like = swipe.is_like
        existing_swipe.swipe_date = datetime.today()
        db.commit()
    else:
        new_swipe = models.Swiped_Users(
            current_user_fk=current_user_id,
            swiped_user_fk=swipe.user_id,
            is_like=swipe.is_like,
            swipe_date=datetime.today()
        )
        
        db.add(new_swipe)
        db.commit()
    
    is_match = False
    
    if swipe.is_like: 
        other_user_swipe = db.query(models.Swiped_Users).filter(
            models.Swiped_Users.current_user_fk == swipe.user_id,
            models.Swiped_Users.swiped_user_fk == current_user_id,
            models.Swiped_Users.is_like == True
        ).first()
        
        if other_user_swipe:
            is_match = True
            
            active_state = db.query(models.Relationship_State).filter(
                models.Relationship_State.state == "active"
            ).first()
            
            if not active_state:
                raise HTTPException(
                    status_code=500,
                    detail="Estado 'active' no encontrado en la base de datos"
                )
            
            new_relationship = models.Couple_Relationship(
                first_user_fk=current_user_id,
                second_user_fk=swipe.user_id,
                state_fk=active_state.id
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

    active_state = db.query(models.Relationship_State).filter(
        models.Relationship_State.state == "active"
    ).first()
    
    if not active_state:
        return schemas.ActiveRelationshipResponse(has_active_match=False)
    
    relationship = db.query(models.Couple_Relationship).filter(
        or_(
            models.Couple_Relationship.first_user_fk == user_id,
            models.Couple_Relationship.second_user_fk == user_id
        ),
        models.Couple_Relationship.state_fk == active_state.id
    ).first()
    
    if not relationship:
        return schemas.ActiveRelationshipResponse(has_active_match=False)
    
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


@router.post("/relationships/{relationship_id}/dismatch")
def dismatch_relationship(
    relationship_id: int,
    current_user_id: int = Query(..., description="ID del usuario que rompe el match"),
    db: Session = Depends(get_db),
):

    relationship = db.query(models.Couple_Relationship).filter(
        models.Couple_Relationship.id == relationship_id
    ).first()
    if not relationship:
        raise HTTPException(status_code=404, detail="Relationship not found")

    if current_user_id not in (relationship.first_user_fk, relationship.second_user_fk):
        raise HTTPException(status_code=403, detail="You are not part of this relationship")

    inactive_state = db.query(models.Relationship_State).filter(
        models.Relationship_State.state == "inactive"
    ).first()
    if not inactive_state:
        raise HTTPException(status_code=500, detail="Estado 'inactive' no encontrado en la base de datos")

    relationship.state_fk = inactive_state.id

    user_a = relationship.first_user_fk
    user_b = relationship.second_user_fk

    db.query(models.Swiped_Users).filter(
        or_(
            and_(
                models.Swiped_Users.current_user_fk == user_a,
                models.Swiped_Users.swiped_user_fk == user_b,
            ),
            and_(
                models.Swiped_Users.current_user_fk == user_b,
                models.Swiped_Users.swiped_user_fk == user_a,
            ),
        )
    ).delete(synchronize_session=False)

    db.commit()

    return {
        "success": True,
        "relationship_id": relationship.id,
        "state": "inactive",
        "user1_id": relationship.first_user_fk,
        "user2_id": relationship.second_user_fk,
        "removed_swipes_between": [user_a, user_b],
    }


@router.get("/connections/{user_id}")
def get_connections_history(
    user_id: int,
    db: Session = Depends(get_db),
):

    relationships = db.query(models.Couple_Relationship).filter(
        or_(
            models.Couple_Relationship.first_user_fk == user_id,
            models.Couple_Relationship.second_user_fk == user_id,
        )
    ).order_by(models.Couple_Relationship.creation_date.desc()).all()

    partners: list[int] = []
    seen: set[int] = set()
    for rel in relationships:
        partner_id = rel.second_user_fk if rel.first_user_fk == user_id else rel.first_user_fk
        if partner_id not in seen:
            seen.add(partner_id)
            partners.append(partner_id)

    return {"partners": partners, "count": len(partners)}


@router.delete("/internal/users/delete")
def delete_user_data_internal(
    user_id: int = Query(...),
    db: Session = Depends(get_db),
):

    swipes_deleted = db.query(models.Swiped_Users).filter(
        or_(
            models.Swiped_Users.current_user_fk == user_id,
            models.Swiped_Users.swiped_user_fk == user_id,
        )
    ).delete(synchronize_session=False)

    relationships_deleted = db.query(models.Couple_Relationship).filter(
        or_(
            models.Couple_Relationship.first_user_fk == user_id,
            models.Couple_Relationship.second_user_fk == user_id,
        )
    ).delete(synchronize_session=False)

    db.commit()
    return {
        "success": True,
        "user_id": user_id,
        "swipes_deleted": swipes_deleted,
        "relationships_deleted": relationships_deleted,
    }