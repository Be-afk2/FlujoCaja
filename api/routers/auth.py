import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer

from api.dependencies import validate_token
from bd.crud.user import login_user, crear_usuario, actualizar_perfil, cambiar_contrasena
from bd.crud.sesion import guardar_sesion_bd, eliminar_sesion_bd, obtener_usuario_por_token
from bd.models.user import User

from .dtos.userDto import (
    UserDTO,
    UserLogin,
    UserPublic,
    UserWithToken,
    MeResponse,
    UserProfileUpdate,
    PasswordChange,
)

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

@router.get("/me", response_model=MeResponse, summary="Obtener perfil del usuario autenticado")
def obtener_perfil(user: User = Depends(validate_token)):
    return user


@router.put("/me", response_model=MeResponse, summary="Actualizar nombre y apellido")
def actualizar_datos(
    datos: UserProfileUpdate,
    user: User = Depends(validate_token),
):
    if not datos.name and not datos.apellido:
        raise HTTPException(status_code=400, detail="Debe enviarse al menos un campo a actualizar")

    actualizado = actualizar_perfil(
        user_id=str(user.id),
        name=datos.name,
        apellido=datos.apellido,
    )
    if not actualizado:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return actualizado


@router.put("/me/password", summary="Cambiar la contraseña del usuario")
def cambiar_password(
    datos: PasswordChange,
    user: User = Depends(validate_token),
):
    ok = cambiar_contrasena(
        user_id=str(user.id),
        passw_actual=datos.passw_actual,
        passw_nueva=datos.passw_nueva,
    )
    if not ok:
        raise HTTPException(status_code=400, detail="La contraseña actual no es correcta")
    return {"message": "Contraseña actualizada"}


@router.delete("")
def borrar_sesion():
    return eliminar_sesion_bd()
