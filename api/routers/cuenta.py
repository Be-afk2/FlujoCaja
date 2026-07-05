from fastapi import APIRouter, Depends
router = APIRouter()
router = APIRouter(prefix="/cuenta")
from bd.models.user import User
from api.dependencies import validate_token
from api.routers.dtos.cuentaDto import CuentaDTO, SubCuentaDTO
from bd.crud.cuenta import get_cuentas, crear_cuenta, get_tipos_cuenta, create_tipo_cuenta

@router.get("/test")
def get_test():
    return "hola"

@router.get("/")
def get_cuentas_api(user: User = Depends(validate_token)):
    return get_cuentas(user)

@router.post("/create")
def crear_cuenta_api(newCuenta:CuentaDTO, user: User = Depends(validate_token)):
    return crear_cuenta(newCuenta.nombre, newCuenta.descripcion, newCuenta.tipo, newCuenta.moneda, user)

@router.post("/sub/create")
def crear_cuenta_api(newCuenta:SubCuentaDTO):
    return create_tipo_cuenta(newCuenta.nombre, newCuenta.descripcion)

@router.get("/sub")
def get_sub_cuenta_api():
    return get_tipos_cuenta()