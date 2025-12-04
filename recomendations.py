from sqlalchemy.orm import Session
import dao

"""
Sexual Orientation ID Convention:
0: Hombre hetero
1: Hombre homo
2: Hombre Bi
3: Mujer hetero
4: Mujer homo
5: Mujer Bi
"""


def jaccard_similarity(interests_a: list, interests_b: list) -> float:
    """Calculate Jaccard similarity between two lists of interests."""
    set_a = set(interests_a)
    set_b = set(interests_b)

    if not set_a and not set_b:
        return 0.0

    intersection = len(set_a & set_b)
    union = len(set_a | set_b)

    return intersection / union


async def get_recommendable_users(db: Session, user_id: int) -> list:
    """
    Get list of user IDs that can be recommended to a given user
    based on their sexual orientation.
    
    Maps sexual_orientation_id to the appropriate DAO function to retrieve candidates.
    
    Returns:
        List of candidate user IDs from the user service
    """
    # Get the user profile from user service
    user = await dao.get_user(db, user_id)
    
    if not user:
        # If user not found, return empty list
        return []

    sexual_orientation_id = user.get("sexual_orientation_id")

    # Map sexual_orientation_id to matching function
    if sexual_orientation_id == 0:  # Hombre hetero
        return await dao.list_user_masc_hetero(db)
    elif sexual_orientation_id == 1:  # Hombre homo
        return await dao.list_user_masc_homo(db)
    elif sexual_orientation_id == 2:  # Hombre Bi
        return await dao.list_user_masc_bi(db)
    elif sexual_orientation_id == 3:  # Mujer hetero
        return await dao.list_user_fem_hete(db)
    elif sexual_orientation_id == 4:  # Mujer homo
        return await dao.list_user_fem_homo(db)
    elif sexual_orientation_id == 5:  # Mujer Bi
        return await dao.list_user_fem_bi(db)

    # In case of error/unknown orientation
    return await dao.list_all_users(db)


async def recommend_users(db: Session, user_id: int, exclude: set = None, limit: int = None) -> list:
    """
    Recommend users based on interest similarity.
    
    Args:
        db: Database session
        user_id: The ID of the user to get recommendations for
        exclude: Set of user IDs to exclude from recommendations (e.g., already recommended, blocked)
        limit: Maximum number of recommendations to return (None = no limit)
    
    Returns:
        List of user IDs ordered from highest to lowest interest similarity
    """
    if exclude is None:
        exclude = set()

    # Get the interests of the target user
    user_interests = await dao.get_user_interests(db, user_id)

    # Get candidate users based on sexual orientation compatibility
    candidates = await get_recommendable_users(db, user_id)

    # Filter out: the user itself
    candidates = [cid for cid in candidates if cid != user_id]

    # Filter out: excluded users (already recommended, blocked, etc.)
    if exclude:
        candidates = [cid for cid in candidates if cid not in exclude]

    # Calculate similarity scores for each candidate
    similarities = []
    for cid in candidates:
        interests_c = await dao.get_user_interests(db, cid)
        score = jaccard_similarity(user_interests, interests_c)
        similarities.append((cid, score))

    # Sort by similarity score (highest first)
    similarities.sort(key=lambda x: x[1], reverse=True)

    # Extract just the user IDs
    recommended_ids = [cid for cid, score in similarities]

    # Apply limit if specified
    if limit is not None:
        recommended_ids = recommended_ids[:limit]

    return recommended_ids

