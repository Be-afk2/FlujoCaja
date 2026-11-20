import logging
import threading
import time
from uuid import UUID, uuid4

from sqlmodel import Session, select

from bd.database import engine
from bd.models.sesion import Sesion
from bd.models.user import User

logger = logging.getLogger(__name__)

# Cache token -> User para no hacer 2 SELECT en cada peticion autenticada.
# Es por proceso (Uvicorn usa un solo worker) y se invalida en login, logout,
# rotacion de token y cambios de perfil.
TTL_CACHE_AUTH = 5.0

_cache_auth: dict[str, tuple[float, User]] = {}
_lock_cache_auth = threading.Lock()


def invalidar_cache_auth(token: str | None = None) -> None:
    """Limpia todo el cache de autenticacion o solo la entrada del token."""
    with _lock_cache_auth:
        if token is None:
            _cache_auth.clear()
        else:
            _cache_auth.pop(token, None)


def _leer_cache_auth(token: str) -> User | None:
    with _lock_cache_auth:
        entrada = _cache_auth.get(token)
        if entrada is None:
            return None

        expira_en, usuario = entrada
        if expira_en <= time.monotonic():
            _cache_auth.pop(token, None)
            return None
        return usuario


def _guardar_cache_auth(token: str, usuario: User) -> None:
    with _lock_cache_auth:
        _cache_auth[token] = (time.monotonic() + TTL_CACHE_AUTH, usuario)


# ==================== UTILIDADES ====================

def generar_token() -> str:
    return str(uuid4())


def crear_session_sqlmodel() -> Session:
    return Session(engine)


# ==================== OPERACIONES DB ====================

def guardar_sesion_bd(user_id: str) -> str | None:
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
            session.refresh(nueva_sesion)
            # El login elimina la sesion anterior: los tokens viejos dejan de
            # ser validos y no deben sobrevivir en el cache.
            invalidar_cache_auth()
            return nueva_sesion.token
    except Exception as e:
        logger.error("Error al guardar sesion: %s", e)
        return None


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
            # El token viejo ya no vale: se descarta todo el cache.
            invalidar_cache_auth()
            return nuevo_token
    except Exception as e:
        logger.error("Error al actualizar token: %s", e)
        return None


def obtener_usuario_por_token(token: str, *, usar_cache: bool = True) -> User | None:
    """Busca la sesion por token y devuelve el User asociado. NO rota el token."""
    if usar_cache:
        cacheado = _leer_cache_auth(token)
        if cacheado is not None:
            return cacheado

    try:
        with crear_session_sqlmodel() as session:
            sesion = obtener_sesion_db(session)
            if not sesion or sesion.token != token:
                return None

            user_id = UUID(sesion.idUser)
            usuario = session.get(User, user_id)
            if usuario is not None and usar_cache:
                _guardar_cache_auth(token, usuario)
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
                invalidar_cache_auth()
                return True

            session.delete(sesion)
            session.commit()
            invalidar_cache_auth()
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

