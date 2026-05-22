from fastapi import APIRouter
router = APIRouter()
router = APIRouter(prefix="/cuenta")
from api.routers.dtos.cuentaDto import SubCuentaDTO
from bd.crud.cuenta import get_cuentas, crear_cuenta, get_tipos_cuenta, create_tipo_cuenta

@router.get("/test")
def get_test():
    return "hola"

@router.get("/")
def get_cuentas_api():
    return  get_cuentas()

@router.post("/create")
def crear_cuenta_api(newCuenta:CuentaDTO):
    return crear_cuenta(newCuenta.nombre, newCuenta.descripcion, newCuenta.tipo)

@router.post("/sub/create")
def crear_cuenta_api(newCuenta:SubCuentaDTO):
    return create_tipo_cuenta(newCuenta.nombre, newCuenta.descripcion)