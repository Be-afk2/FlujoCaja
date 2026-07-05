from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

from bd.crud.sesion import obtener_usuario_por_token
from bd.models.user import User

security = HTTPBearer()


def validate_token(credentials = Depends(security)) -> User:
    """Valida el Bearer token y retorna el User autenticado."""
    token = credentials.credentials
    usuario = obtener_usuario_por_token(token)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return usuario
