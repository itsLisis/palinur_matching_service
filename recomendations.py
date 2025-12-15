from sqlalchemy.orm import Session
import dao

def jaccard_similarity(interests_a: list, interests_b: list) -> float:
    set_a = set(interests_a)
    set_b = set(interests_b)

    if not set_a and not set_b:
        return 0.0

    intersection = len(set_a & set_b)
    union = len(set_a | set_b)

    return intersection / union


def get_recommendable_users(db: Session, user_id: int) -> list:

    user = dao.get_user(db, user_id)

    genero = user.gender.lower()            # "male" / "female"
    orient = user.orientation.lower()       # "hetero" / "homo" / "bi"

    if genero == "male":
        if orient == "hetero":
            return dao.list_user_masc_hetero(db)
        elif orient == "homo":
            return dao.list_user_masc_homo(db)
        elif orient == "bi":
            return dao.list_user_masc_bi(db)

    if genero == "female":
        if orient == "hetero":
            return dao.list_user_fem_hete(db)
        elif orient == "homo":
            return dao.list_user_fem_homo(db)
        elif orient == "bi":
            return dao.list_user_fem_bi(db)

    # en caso de error
    return dao.list_all_users(db)


def recommend_users(db: Session, user_id: int, exclude: set = None, limit: int = None) -> list:

    if exclude is None:
        exclude = set()

    user_interests = dao.get_user_interests(db, user_id)

    candidates = get_recommendable_users(db, user_id)

    candidates = [cid for cid in candidates if cid != user_id]

    if exclude:
        candidates = [cid for cid in candidates if cid not in exclude]

    similarities = []

    for cid in candidates:
        interests_c = dao.get_user_interests(db, cid)
        score = jaccard_similarity(user_interests, interests_c)
        similarities.append((cid, score))

    similarities.sort(key=lambda x: x[1], reverse=True)

    recommended_ids = [cid for cid, score in similarities]

    if limit is not None:
        recommended_ids = recommended_ids[:limit]

    return recommended_ids