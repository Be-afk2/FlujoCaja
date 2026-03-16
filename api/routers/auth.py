import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from fastapi import APIRouter

from bd.crud.user import login_user,crear_usuario

from .dtos.userDto import UserDTO,UserLogin


router = APIRouter()


router = APIRouter(prefix="/auth")
@router.get("/users")
def users():
    return {"users": []}

@router.post("/create")
def create_user(newUser:UserDTO):
    return crear_usuario(newUser.name,newUser.apellido,newUser.passw)
 
@router.post("/login")
def login(user:UserLogin):
    return login_user(user.name,user.passw)