import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer

from bd.crud.user import login_user, crear_usuario
from bd.crud.sesion import guardar_sesion_bd, eliminar_sesion_bd, obtener_usuario_por_token

from .dtos.userDto import UserDTO, UserLogin, UserPublic, UserWithToken

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=201, response_model=UserPublic, summary="Registrar nuevo usuario")
def register(newUser: UserDTO):
    logger.debug("Creando usuario: %s", newUser)
    return crear_usuario(newUser.name, newUser.apellido, newUser.passw)

@router.post("/login", response_model=UserWithToken, summary="Iniciar sesión")
def login(user: UserLogin):
    userLogin = login_user(user.name, user.passw)
    if userLogin:
        token = guardar_sesion_bd(userLogin.id)
        if not token:
            raise HTTPException(status_code=500, detail="No se pudo iniciar sesión")
        return {"user": userLogin, "token": token}
    raise HTTPException(status_code=401, detail="Credenciales inválidas", headers={"WWW-Authenticate": "Bearer"})

@router.get("", response_model=UserWithToken, summary="Obtener sesión actual")
def getSesion(credentials=Depends(HTTPBearer())):
    usuario = obtener_usuario_por_token(credentials.credentials)
    if not usuario:
        raise HTTPException(status_code=401, detail="No hay sesión activa", headers={"WWW-Authenticate": "Bearer"})
    return {"user": usuario, "token": credentials.credentials}

@router.delete("")
def borrar_sesion():
    return eliminar_sesion_bd()
