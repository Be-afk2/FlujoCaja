import logging
from uuid import UUID, uuid4
from sqlmodel import Session, select
from bd.database import engine
from bd.models.sesion import Sesion
from bd.models.user import User

logger = logging.getLogger(__name__)


# ==================== UTILIDADES ====================

def generar_token() -> str:
    return str(uuid4())


def crear_session_sqlmodel() -> Session:
    return Session(engine)


# ==================== OPERACIONES DB ====================

def guardar_sesion_bd(user_id: str) -> bool:
    try:
        with crear_session_sqlmodel() as session:
            sesion_antigua = obtener_sesion_db(session)
            if sesion_antigua:
                session.delete(sesion_antigua)

            nueva_sesion = Sesion(
                idUser=str(user_id),
                token=generar_token()
            )
            session.add(nueva_sesion)
            session.commit()
            return True
    except Exception as e:
        logger.error("Error al guardar sesion: %s", e)
        return False


def actualizar_token_bd() -> str | None:
    try:
        with crear_session_sqlmodel() as session:
            sesion = obtener_sesion_db(session)
            if not sesion:
                return None

            nuevo_token = generar_token()
            sesion.token = nuevo_token
            session.add(sesion)
            session.commit()
            return nuevo_token
    except Exception as e:
        logger.error("Error al actualizar token: %s", e)
        return None


def obtener_usuario_por_token(token: str) -> User | None:
    """Busca la sesion por token y devuelve el User asociado. NO rota el token."""
    try:
        with crear_session_sqlmodel() as session:
            sesion = obtener_sesion_db(session)
            if not sesion or sesion.token != token:
                return None

            user_id = UUID(sesion.idUser)
            usuario = session.get(User, user_id)
            return usuario
    except Exception as e:
        logger.error("Error obteniendo usuario por token: %s", e)
        return None


def obtener_sesion(actualizar: bool = False) -> tuple[User, str] | None:
    """Obtiene la sesion activa con el usuario y el token.
    Solo rota el token si actualizar=True (ej: en login).
    Deprecada para uso en CRUDs - usar obtener_usuario_por_token() en su lugar."""
    try:
        with crear_session_sqlmodel() as session:
            sesion = obtener_sesion_db(session)
            if not sesion:
                return None

            user_id = UUID(sesion.idUser)
            usuario = session.get(User, user_id)
            if not usuario:
                return None

            if actualizar:
                nuevo_token = actualizar_token_bd()
                token = nuevo_token if nuevo_token else sesion.token
            else:
                token = sesion.token

            return usuario, token
    except Exception as e:
        logger.error("Error al obtener sesion: %s", e)
        return None


def eliminar_sesion_bd() -> bool:
    try:
        with crear_session_sqlmodel() as session:
            sesion = obtener_sesion_db(session)
            if not sesion:
                return True

            session.delete(sesion)
            session.commit()
            return True
    except Exception as e:
        logger.error("Error al eliminar sesion: %s", e)
        return False


# ==================== FUNCIONES AUXILIARES ====================

def obtener_sesion_db(session: Session) -> Sesion | None:
    try:
        stmt = select(Sesion)
        return session.exec(stmt).first()
    except Exception as e:
        logger.error("Error obteniendo sesion de BD: %s", e)
        return None

