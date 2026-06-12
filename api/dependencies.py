from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer
from pygments import console

from bd.crud.sesion import obtener_sesion, obtener_sesion_db, obtener_session_bd, validar_token, validar_token

security = HTTPBearer()


def validate_token(credentials = Depends(security)) -> str:
    """
    Decorator para validar el token en cada petición.
    
    Extrae el token del header Authorization (formato: Bearer <token>)
    y lo valida. Si es válido, continúa con la petición.
    Si falla, retorna un error 401 Unauthorized.
    
    Args:
        credentials: Las credenciales del header Authorization
        
    Returns:
        str: El token validado
        
    Raises:
        HTTPException: 401 si el token es inválido o expirado
    """
    token = credentials.credentials
    
    # TODO: Implementar la lógica de validación del token
    # Ejemplo de flujo esperado:
    # 1. Decodificar el token (JWT, sesión, etc.)
    # 2. Verificar que el token sea válido
    # 3. Verificar que el token no haya expirado
    # 4. Si falla cualquier validación, lanzar excepción
    
    is_valid = validar_token(token)
    
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return token


async def validate_token_logic(token: str) -> bool:
    """
    Lógica para validar el token.
    
    Rellena esta función con tu lógica de validación específica.
    Por ejemplo: decodificar JWT, consultar BD, validar fecha expiración, etc.
    
    Args:
        token: El token a validar
        
    Returns:
        bool: True si el token es válido, False en caso contrario
    """



    return False  # Placeholder, reemplaza con la lógica real


# EJEMPLO DE USO EN LAS RUTAS:
# 
# from fastapi import APIRouter, Depends
# from api.dependencies import validate_token
#
# router = APIRouter()
#
# @router.get("/ruta-protegida")
# async def ruta_protegida(token: str = Depends(validate_token)):
#     return {"mensaje": "Acceso permitido", "token": token}
#
# @router.post("/otra-ruta")
# async def otra_ruta(token: str = Depends(validate_token)):
#     return {"mensaje": "Operación exitosa"}
