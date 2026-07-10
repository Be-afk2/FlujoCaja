import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer

from bd.crud.user import login_user, crear_usuario
from bd.crud.sesion import guardar_sesion_bd, eliminar_sesion_bd, obtener_usuario_por_token

from .dtos.userDto import UserDTO, UserLogin, UserPublic, UserWithToken

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/auth")


@router.get("/users")
def users():
    return {"users": []}

@router.post("/create", response_model=UserPublic)
def create_user(newUser: UserDTO):
    logger.debug("Creando usuario: %s", newUser)
    return crear_usuario(newUser.name, newUser.apellido, newUser.passw)

@router.post("/login", response_model=UserPublic)
def login(user: UserLogin):
    userLogin = login_user(user.name, user.passw)
    if userLogin:
        if user.recordar:
            guardar_sesion_bd(userLogin.id)
        return userLogin
    raise HTTPException(status_code=404, detail="Usuario no encontrado")

@router.get("", response_model=UserWithToken)
def getSesion(credentials=Depends(HTTPBearer())):
    usuario = obtener_usuario_por_token(credentials.credentials)
    if not usuario:
        raise HTTPException(status_code=404, detail="No hay sesión activa")
    return {"user": usuario, "token": credentials.credentials}

@router.delete("")
def borrar_sesion():
    return eliminar_sesion_bd()

@router.get("/life/server")
def life():
    return {"message": "alive"}

@router.get("/life/token")
def life_token(token: str):
    usuario = obtener_usuario_por_token(token)
    if not usuario:
        raise HTTPException(status_code=401, detail="Token inválido o expirado")
    return {"message": "Token válido", "status": "true"}
