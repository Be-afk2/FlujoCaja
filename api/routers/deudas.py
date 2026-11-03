from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import validate_token
from bd.crud.deuda import (
    crear_deuda,
    editar_deuda,
    editar_pago,
    eliminar_deuda,
    eliminar_pago,
    listar_deudas,
    moneda_distinta,
    registrar_pago,
)
from bd.crud.exceptions import RecursoNoEncontradoError
from bd.models.user import User

from .dtos.deudaDto import (
    DeudaCreate,
    DeudaListItem,
    DeudaResponse,
    DeudaUpdate,
    PagoDeudaCreate,
    PagoDeudaResponse,
    PagoDeudaUpdate,
)

router = APIRouter(prefix="/deudas", tags=["Deudas"])


def _deuda_base(deuda) -> dict:
    return {
        "id": deuda.id,
        "entidad_id": deuda.entidad_id,
        "direccion": deuda.direccion,
        "monto_original": deuda.monto_original,
        "moneda_id": deuda.moneda_id,
        "descripcion": deuda.descripcion,
        "fecha": deuda.fecha,
        "vencimiento": deuda.vencimiento,
        "movimiento_inicial_id": deuda.movimiento_inicial_id,
    }


def _pago_response(pago, user: User) -> dict:
    return {
        "id": pago.id,
        "deuda_id": pago.deuda_id,
        "monto": pago.monto,
        "fecha": pago.fecha,
        "cuenta_id": pago.cuenta_id,
        "movimiento_id": pago.movimiento_id,
        "descripcion": pago.descripcion,
        "moneda_distinta": moneda_distinta(user, pago.deuda_id, pago.cuenta_id),
    }


def _error(exc: ValueError) -> HTTPException:
    if isinstance(exc, RecursoNoEncontradoError):
        return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=400, detail=str(exc))


@router.get("/", response_model=list[DeudaListItem], summary="Listar deudas con filtros")
def listar(
    entidad_id: Optional[int] = None,
    direccion: Optional[str] = None,
    estado: Optional[str] = None,
    user: User = Depends(validate_token),
):
    try:
        filas = listar_deudas(
            user,
            entidad_id=entidad_id,
            direccion=direccion,
            estado=estado,
        )
    except ValueError as e:
        raise _error(e) from e

    return [
        {
            **_deuda_base(fila["deuda"]),
            "total_abonos": fila["total_abonos"],
            "pendiente": fila["pendiente"],
            "estado": fila["estado"],
        }
        for fila in filas
    ]


@router.post("/", status_code=201, response_model=DeudaResponse, summary="Crear una deuda")
def crear(datos: DeudaCreate, user: User = Depends(validate_token)):
    try:
        return crear_deuda(
            user,
            entidad_id=datos.entidad_id,
            direccion=datos.direccion,
            monto_original=datos.monto_original,
            moneda_id=datos.moneda_id,
            descripcion=datos.descripcion,
            fecha=datos.fecha,
            vencimiento=datos.vencimiento,
            cuenta_inicial_id=datos.cuenta_inicial_id,
        )
    except ValueError as e:
        raise _error(e) from e


@router.put("/{deuda_id}", response_model=DeudaResponse, summary="Actualizar una deuda")
def actualizar(
    deuda_id: int,
    datos: DeudaUpdate,
    user: User = Depends(validate_token),
):
    try:
        return editar_deuda(
            user,
            deuda_id,
            descripcion=datos.descripcion,
            vencimiento=datos.vencimiento,
            fecha=datos.fecha,
            monto_original=datos.monto_original,
            moneda_id=datos.moneda_id,
            direccion=datos.direccion,
        )
    except ValueError as e:
        raise _error(e) from e


@router.delete("/{deuda_id}", summary="Eliminar una deuda y sus movimientos")
def eliminar(deuda_id: int, user: User = Depends(validate_token)):
    try:
        eliminar_deuda(user, deuda_id)
    except ValueError as e:
        raise _error(e) from e
    return {"message": "Deuda eliminada"}


@router.post(
    "/{deuda_id}/pagos",
    status_code=201,
    response_model=PagoDeudaResponse,
    summary="Registrar un pago, cobro o abono",
)
def registrar_pago_deuda(
    deuda_id: int,
    datos: PagoDeudaCreate,
    user: User = Depends(validate_token),
):
    try:
        pago = registrar_pago(
            user,
            deuda_id,
            monto=datos.monto,
            cuenta_id=datos.cuenta_id,
            fecha=datos.fecha,
            descripcion=datos.descripcion,
        )
    except ValueError as e:
        raise _error(e) from e

    return _pago_response(pago, user)


@router.put(
    "/{deuda_id}/pagos/{pago_id}",
    response_model=PagoDeudaResponse,
    summary="Actualizar un pago o abono",
)
def actualizar_pago(
    deuda_id: int,
    pago_id: int,
    datos: PagoDeudaUpdate,
    user: User = Depends(validate_token),
):
    try:
        pago = editar_pago(
            user,
            deuda_id,
            pago_id,
            monto=datos.monto,
            cuenta_id=datos.cuenta_id,
            fecha=datos.fecha,
            descripcion=datos.descripcion,
        )
    except ValueError as e:
        raise _error(e) from e

    return _pago_response(pago, user)


@router.delete("/{deuda_id}/pagos/{pago_id}", summary="Eliminar un pago o abono")
def eliminar_pago_deuda(
    deuda_id: int,
    pago_id: int,
    user: User = Depends(validate_token),
):
    try:
        eliminar_pago(user, deuda_id, pago_id)
    except ValueError as e:
        raise _error(e) from e
    return {"message": "Pago eliminado"}
