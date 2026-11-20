from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

from bd.crud.sesion import obtener_usuario_por_token
from bd.models.user import User

security = HTTPBearer()


def validate_token(credentials = Depends(security)) -> User:
    """Valida el Bearer token y retorna el User autenticado.

    `obtener_usuario_por_token` cachea token → User durante 5 s, asi una
    rafaga de peticiones hace como maximo 2 SELECT en vez de 2 por request.
    """
    token = credentials.credentials
    usuario = obtener_usuario_por_token(token)

    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return usuario
