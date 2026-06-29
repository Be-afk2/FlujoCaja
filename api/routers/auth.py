import sys
import os
import logging

from sqlmodel import false

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from fastapi import APIRouter, HTTPException

from bd.crud.user import login_user,crear_usuario
from bd.crud.sesion import guardar_sesion_bd, obtener_sesion, eliminar_sesion_bd, validar_token

from .dtos.userDto import UserDTO,UserLogin, UserPublic, UserWithToken

logger = logging.getLogger(__name__)


router = APIRouter()


router = APIRouter(prefix="/auth")
@router.get("/users")
def users():
    return {"users": []}

@router.post("/create")
def create_user(newUser:UserDTO):
    logger.debug("Creando usuario: %s", newUser)
    return crear_usuario(newUser.name,newUser.apellido,newUser.passw)
 
@router.post("/login",response_model=UserPublic)
def login(user:UserLogin):
    userLogin= login_user(user.name,user.passw)
    if(userLogin):
        if(user.recordar):
            guardar_sesion_bd(userLogin.id)
        return userLogin
    else:
       raise HTTPException(status_code=404, detail="Usuario no encontrado")
@router.get("",response_model=UserWithToken)
def getSesion():
    result = obtener_sesion()
    if not result:
        raise HTTPException(status_code=404, detail="No hay sesión activa")
    user, token = result
    return {"user": user, "token": token}

@router.delete("")
def borrar_sesion():
    return eliminar_sesion_bd()

@router.get("/life/server")
def life():
    return {"message":"alive"}

@router.get("/life/token")
def life_token(token:str):
        result = validar_token(token)
        if  result == false:
            raise HTTPException(status_code=401, detail="Token inválido o expirado")
        return {"message":"Token válido","status":"true"}
