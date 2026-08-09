from fastapi import APIRouter, Depends
from typing import List
from bd.models.user import User
from api.dependencies import validate_token
from api.routers.dtos.cuentaDto import CuentaDTO, SubCuentaDTO, CuentaResponse, TipoCuentaResponse
from bd.crud.cuenta import get_cuentas, crear_cuenta, get_tipos_cuenta, create_tipo_cuenta

router = APIRouter(prefix="/cuentas", tags=["Cuentas"])

@router.get("/", response_model=List[CuentaResponse])
def listar_cuentas(user: User = Depends(validate_token)):
    return get_cuentas(user)

@router.post("/", status_code=201, response_model=CuentaResponse)
def crear_cuenta_nueva(newCuenta: CuentaDTO, user: User = Depends(validate_token)):
    return crear_cuenta(newCuenta.nombre, newCuenta.descripcion, newCuenta.tipo, newCuenta.moneda, user)

@router.get("/tipos-cuenta", response_model=List[TipoCuentaResponse])
def listar_tipos_cuenta():
    return get_tipos_cuenta()

@router.post("/tipos-cuenta", status_code=201, response_model=TipoCuentaResponse)
def crear_tipo_cuenta_nuevo(newCuenta: SubCuentaDTO):
    return create_tipo_cuenta(newCuenta.nombre, newCuenta.descripcion)
