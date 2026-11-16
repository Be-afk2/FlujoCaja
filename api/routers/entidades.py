from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import validate_token
from bd.crud.entidad import (
    crear_entidad,
    editar_entidad,
    eliminar_entidad,
    listar_entidades,
    obtener_entidad,
)
from bd.crud.exceptions import RecursoNoEncontradoError
from bd.models.user import User

from .deudasMensuales import deuda_mensual_detalle_response
from .dtos.entidadDto import (
    EntidadCreate,
    EntidadDetailResponse,
    EntidadListItem,
    EntidadResponse,
    EntidadUpdate,
)

router = APIRouter(prefix="/entidades", tags=["Entidades"])


def _entidad_base(entidad) -> dict:
    return {
        "id": entidad.id,
        "nombre": entidad.nombre,
        "tipo": entidad.tipo,
        "descripcion": entidad.descripcion,
    }


def _saldos(saldos) -> list[dict]:
    return [
        {
            "moneda_id": saldo.moneda_id,
            "a_favor": saldo.a_favor,
            "en_contra": saldo.en_contra,
            "neto": saldo.neto,
        }
        for saldo in saldos
    ]


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


def _deuda_detalle(item: dict) -> dict:
    deuda = item["deuda"]
    return {
        **_deuda_base(deuda),
        "total_abonos": item["total_abonos"],
        "pendiente": item["pendiente"],
        "estado": item["estado"],
        "pagos": [
            {
                "id": pago.id,
                "deuda_id": pago.deuda_id,
                "monto": pago.monto,
                "fecha": pago.fecha,
                "cuenta_id": pago.cuenta_id,
                "movimiento_id": pago.movimiento_id,
                "descripcion": pago.descripcion,
            }
            for pago in item.get("pagos", [])
        ],
    }


def _error(exc: ValueError) -> HTTPException:
    if isinstance(exc, RecursoNoEncontradoError):
        return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=400, detail=str(exc))


@router.get("/", response_model=list[EntidadListItem], summary="Listar entidades con saldos por moneda")
def listar(user: User = Depends(validate_token)):
    return [
        {
            **_entidad_base(item["entidad"]),
            "saldos": _saldos(item["saldos"]),
            "deudas_pendientes": item["deudas_pendientes"],
            "proximo_vencimiento": item["proximo_vencimiento"],
        }
        for item in listar_entidades(user)
    ]


@router.post("/", status_code=201, response_model=EntidadResponse, summary="Crear una entidad")
def crear(datos: EntidadCreate, user: User = Depends(validate_token)):
    try:
        return crear_entidad(
            user,
            datos.nombre,
            datos.tipo,
            datos.descripcion,
        )
    except ValueError as e:
        raise _error(e) from e


@router.get(
    "/{entidad_id}",
    response_model=EntidadDetailResponse,
    summary="Obtener entidad con sus deudas y pagos",
)
def detalle(entidad_id: int, user: User = Depends(validate_token)):
    try:
        item = obtener_entidad(user, entidad_id)
    except ValueError as e:
        raise _error(e) from e

    return {
        **_entidad_base(item["entidad"]),
        "saldos": _saldos(item["saldos"]),
        "deudas_pendientes": item["deudas_pendientes"],
        "proximo_vencimiento": item["proximo_vencimiento"],
        "deudas": [_deuda_detalle(deuda) for deuda in item["deudas"]],
        "deudas_mensuales": [
            deuda_mensual_detalle_response(deuda, user)
            for deuda in item["deudas_mensuales"]
        ],
    }


@router.put("/{entidad_id}", response_model=EntidadResponse, summary="Actualizar una entidad")
def actualizar(
    entidad_id: int,
    datos: EntidadUpdate,
    user: User = Depends(validate_token),
):
    try:
        return editar_entidad(
            user,
            entidad_id,
            nombre=datos.nombre,
            tipo=datos.tipo,
            descripcion=datos.descripcion,
        )
    except ValueError as e:
        raise _error(e) from e


@router.delete("/{entidad_id}", summary="Eliminar una entidad sin deudas")
def eliminar(entidad_id: int, user: User = Depends(validate_token)):
    try:
        eliminar_entidad(user, entidad_id)
    except ValueError as e:
        raise _error(e) from e
    return {"message": "Entidad eliminada"}
