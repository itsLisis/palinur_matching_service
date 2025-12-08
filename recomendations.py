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
    """
    - exclude es conjunto de IDs a excluir (usuarios ya recomendados, por lo que de4beria ser una query a la lisat de usuarios ya recomendados)      
    - limit es número máximo de recomendaciones (None = sin límite, establecer un limite)
    Retorna una lista ordenada de IDs de mayor similitud → menor similitud.
    """

    if exclude is None:
        exclude = set()

    user_interests = dao.get_user_interests(db, user_id)

    candidates = get_recommendable_users(db, user_id)

    #Para no recomendarse a si mismo
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

    #Aplicar límite
    if limit is not None:
        recommended_ids = recommended_ids[:limit]

    return recommended_ids


"""
Querys a implementar: TO DO
  - dao.get_user(db, user_id): Para obtener el usuario por su ID
  - dao.list_all_users(db): Devuelve una lista de los ids de todos los usuarios sin importar su orientación sexual.  
  - dao.list_user_masc_hetero(db): Devuelve una lista de los ids de usuarios que se le pueden recomendar a un hombre heterosexual (Mujeres hetero, mujeres bi).
  - dao.list_user_masc_homo(db): Devuelve una lista de los ids de usuarios que se le pueden recomendar a un hombre homosexual (Hombres bi, hombre homo). 
  - dao.list_user_masc_bi(db): Devuelve una lista de los ids de usuarios que se le pueden recomendar a un hombre bisexual (Mujeres hetero, mujeres bi, Hombres bi, hombre homo).
  - dao.list_user_fem_hete(db): Devuelve una lista de los ids de usuarios que se le pueden recomendar a una mujer heterosexual.
  - dao.list_user_fem_homo(db): Devuelve una lista de los ids de usuarios que se le pueden recomendar a una mujer heterosexual.
  - dao.list_user_fem_bi(db): Devuelve una lista de los ids de usuarios que se le pueden recomendar a una mujer heterosexual.
 
  - dao.get_user_interests(db, user_id): Obtiene el arreglo de intereses de un usuario
"""