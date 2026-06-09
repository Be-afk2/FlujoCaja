import logging
from uuid import UUID, uuid4
from sqlmodel import Session, select
from bd.database import engine
from bd.models.sesion import Sesion
from bd.models.user import User

# Configurar logger
logger = logging.getLogger(__name__)


# ==================== UTILIDADES ====================

def generar_token() -> str:
    """
    Genera un token único usando UUID4.
    
    Returns:
        str: Token UUID convertido a string
    """
    return str(uuid4())


def obtener_session_bd() -> Session:
    """
    Obtiene una sesión de base de datos.
    
    Returns:
        Session: Sesión de SQLModel
    """
    return Session(engine)


# ==================== OPERACIONES CRUD ====================

def guardar_sesion_bd(user_id: str) -> bool:
    """
    Guarda una nueva sesión de usuario. Si existe una sesión anterior, la elimina.
    
    Args:
        user_id (str): ID del usuario
        
    Returns:
        bool: True si se guardó correctamente, False en caso contrario
    """
    try:
        with obtener_session_bd() as session:
            # Eliminar sesión antigua si existe
            sesion_antigua = obtener_sesion_db(session)
            if sesion_antigua:
                session.delete(sesion_antigua)
                logger.info("✓ Sesión antigua eliminada")

            # Crear nueva sesión
            nueva_sesion = Sesion(
                idUser=str(user_id),
                token=generar_token()
            )
            session.add(nueva_sesion)
            session.commit()
            logger.info(f"✓ Sesión creada para usuario: {user_id}")
            return True
    except Exception as e:
        logger.error(f"✗ Error al guardar sesión: {e}")
        return False


def actualizar_token_bd() -> str | None:
    """
    Actualiza el token de la sesión actual.
    
    Returns:
        str | None: El nuevo token si se actualizó correctamente, None en caso contrario
    """
    try:
        with obtener_session_bd() as session:
            sesion = obtener_sesion_db(session)
            
            if not sesion:
                logger.warning("⚠ No hay sesión activa para actualizar")
                return None
            
            nuevo_token = generar_token()
            sesion.token = nuevo_token
            session.add(sesion)
            session.commit()
            session.refresh(sesion)
            logger.info("✓ Token actualizado")
            return nuevo_token
    except Exception as e:
        logger.error(f"✗ Error al actualizar token: {e}")
        return None


def validar_token(token: str) -> bool:
    """
    Valida si un token es válido y pertenece a la sesión activa.
    
    Args:
        token (str): Token a validar
        
    Returns:
        bool: True si el token es válido, False en caso contrario
    """
    try:
        with obtener_session_bd() as session:
            sesion = obtener_sesion_db(session)
            
            if not sesion:
                logger.warning("⚠ No hay sesión activa")
                return False
            
            if sesion.token == token:
                logger.info("✓ Token válido")
                return True
            else:
                logger.warning("⚠ Token inválido o expirado")
                return False
    except Exception as e:
        logger.error(f"✗ Error validando token: {e}")
        return False


def obtener_sesion() -> tuple[User, str] | None:
    """
    Obtiene la sesión activa con la información del usuario y el token.
    
    Returns:
        tuple[User, str] | None: Tupla (usuario, token) si existe sesión, None en caso contrario
    """
    try:
        with obtener_session_bd() as session:
            sesion = obtener_sesion_db(session)
            
            if not sesion:
                logger.info("ℹ No hay sesión activa")
                return None
            
            # Convertir user_id a UUID y obtener usuario
            user_id = UUID(sesion.idUser)
            usuario = session.get(User, user_id)
            
            if not usuario:
                logger.warning("⚠ Usuario no encontrado")
                return None
            
            # Actualizar token
            nuevo_token = actualizar_token_bd()
            token = nuevo_token if nuevo_token else sesion.token
            
            logger.info("✓ Sesión obtenida")
            return usuario, token
    except Exception as e:
        logger.error(f"✗ Error al obtener sesión: {e}")
        return None


def eliminar_sesion_bd() -> bool:
    """
    Elimina la sesión activa del usuario.
    
    Returns:
        bool: True si se eliminó correctamente, False en caso contrario
    """
    try:
        with obtener_session_bd() as session:
            sesion = obtener_sesion_db(session)
            
            if not sesion:
                logger.info("ℹ No hay sesión para eliminar")
                return True
            
            session.delete(sesion)
            session.commit()
            logger.info("✓ Sesión eliminada")
            return True
    except Exception as e:
        logger.error(f"✗ Error al eliminar sesión: {e}")
        return False


# ==================== FUNCIONES AUXILIARES ====================

def obtener_sesion_db(session: Session) -> Sesion | None:
    """
    Obtiene el registro de sesión de la base de datos.
    
    Args:
        session (Session): Sesión de SQLModel
        
    Returns:
        Sesion | None: El registro de sesión si existe, None en caso contrario
    """
    try:
        stmt = select(Sesion)
        return session.exec(stmt).first()
    except Exception as e:
        logger.error(f"✗ Error obteniendo sesión de BD: {e}")
        return None

