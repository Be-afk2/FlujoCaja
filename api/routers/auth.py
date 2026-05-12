import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from fastapi import APIRouter, HTTPException

from bd.crud.user import login_user,crear_usuario
from bd.crud.sesion import guardar_sesion_bd,get_sesion,eliminar_sesion_bd

from .dtos.userDto import UserDTO,UserLogin, UserPublic


router = APIRouter()


router = APIRouter(prefix="/auth")
@router.get("/users")
def users():
    return {"users": []}

@router.post("/create")
def create_user(newUser:UserDTO):
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
@router.get("",response_model=UserPublic)
def getSesion():
    return get_sesion()

@router.delete("")
def borrar_sesion():
    return eliminar_sesion_bd()

@router.get("/life")
def life():
    return {"message":"alive"}