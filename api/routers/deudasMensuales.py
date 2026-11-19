from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from api.dependencies import validate_token
from bd.crud.deudaMensual import (
    cancelar_deuda_mensual,
    crear_deuda_mensual,
    editar_deuda_mensual,
    editar_pago,
    eliminar_deuda_mensual,
    eliminar_pago,
    listar_deudas_mensuales,
    moneda_distinta,
    monedas_por_cuenta,
    obtener_deuda_mensual,
    pagar_cuota,
    pagar_cuotas,
    proximas_cuotas,
    resumen_deudas_mensuales,
    sincronizar_deudas_mensuales,
)
from bd.crud.exceptions import RecursoNoEncontradoError
from bd.domain.deuda import monedas_distintas
from bd.models.user import User

from .dtos.deudaMensualDto import (
    DeudaMensualCreate,
    DeudaMensualDetailResponse,
    DeudaMensualListItem,
    DeudaMensualResponse,
    DeudaMensualUpdate,
    PagarCuotasMensualesCreate,
    PagoCuotaMensualCreate,
    PagoCuotaMensualResponse,
    ProximaCuotaItem,
    ResumenDeudasMensuales,
)

router = APIRouter(prefix="/deudas-mensuales", tags=["Deudas mensuales"])


@router.post(
    "/sincronizar",
    summary="Generar cuotas mensuales faltantes",
)
def sincronizar(user: User = Depends(validate_token)):
    """Sincroniza las cuotas activas fuera de los endpoints de lectura."""
    return {"cuotas_creadas": sincronizar_deudas_mensuales(user)}


def _deuda_mensual_base(deuda) -> dict:
    return {
        "id": deuda.id,
        "entidad_id": deuda.entidad_id,
        "tipo_id": deuda.tipo_id,
        "subtipo_id": deuda.subtipo_id,
        "moneda_id": deuda.moneda_id,
        "descripcion": deuda.descripcion,
        "modalidad": deuda.modalidad,
        "monto_modo": deuda.monto_modo,
        "monto_cuota": deuda.monto_cuota,
        "monto_total": deuda.monto_total,
        "cuotas_totales": deuda.cuotas_totales,
        "dia_aparicion": deuda.dia_aparicion,
        "dia_limite": deuda.dia_limite,
        "fecha_inicio": deuda.fecha_inicio,
        "estado": deuda.estado,
        "fecha_cancelacion": deuda.fecha_cancelacion,
        "cuenta_pago_default_id": deuda.cuenta_pago_default_id,
        "created_at": deuda.created_at,
    }


def _pago_response(
    pago,
    user: User,
    *,
    moneda_deuda: Optional[int] = None,
    monedas_cuentas: Optional[dict[int, int]] = None,
) -> dict:
    # En las respuestas de detalle el mapa de monedas ya viene precargado:
    # evita abrir una sesion por cada pago (N+1).
    if moneda_deuda is not None and monedas_cuentas is not None:
        distinta = monedas_distintas(
            moneda_deuda,
            monedas_cuentas.get(pago.cuenta_id, moneda_deuda),
        )
    else:
        distinta = moneda_distinta(user, pago.cuota_id, pago.cuenta_id)

    return {
        "id": pago.id,
        "cuota_id": pago.cuota_id,
        "monto": pago.monto,
        "fecha": pago.fecha,
        "cuenta_id": pago.cuenta_id,
        "movimiento_id": pago.movimiento_id,
        "descripcion": pago.descripcion,
        "moneda_distinta": distinta,
    }


def _cuota_response(
    cuota,
    user: User,
    pagos=None,
    *,
    moneda_deuda: Optional[int] = None,
    monedas_cuentas: Optional[dict[int, int]] = None,
) -> dict:
    return {
        "id": cuota.id,
        "deuda_mensual_id": cuota.deuda_mensual_id,
        "numero": cuota.numero,
        "anio": cuota.anio,
        "mes": cuota.mes,
        "fecha_aparicion": cuota.fecha_aparicion,
        "fecha_limite": cuota.fecha_limite,
        "monto": cuota.monto,
        "estado": cuota.estado,
        "estado_pago": cuota.estado_pago,
        "pagos": [
            _pago_response(
                pago,
                user,
                moneda_deuda=moneda_deuda,
                monedas_cuentas=monedas_cuentas,
            )
            for pago in (pagos or [])
        ],
    }


def _deuda_mensual_list_item(item: dict, user: User) -> dict:
    proxima = item.get("proxima")
    return {
        **_deuda_mensual_base(item["deuda_mensual"]),
        "pendiente": item["pendiente"],
        "pagado": item["pagado"],
        "vencidas": item["vencidas"],
        "vencidas_monto": item["vencidas_monto"],
        "proxima": _cuota_response(proxima, user) if proxima else None,
    }


def deuda_mensual_detalle_response(
    item: dict,
    user: User,
    *,
    monedas_cuentas: Optional[dict[int, int]] = None,
) -> dict:
    """Serializa el detalle para el router de entidades y el propio."""
    deuda_mensual = item["deuda_mensual"]
    moneda_deuda = deuda_mensual.moneda_id
    cuotas = []
    for entry in item.get("cuotas", []):
        if isinstance(entry, dict):
            cuota = entry["cuota"]
            pagos = entry.get("pagos", [])
        else:
            cuota = entry
            pagos = []
        cuotas.append(
            _cuota_response(
                cuota,
                user,
                pagos,
                moneda_deuda=moneda_deuda,
                monedas_cuentas=monedas_cuentas,
            )
        )

    proxima = item.get("proxima")
    return {
        **_deuda_mensual_base(deuda_mensual),
        "pendiente": item["pendiente"],
        "pagado": item["pagado"],
        "vencidas": item["vencidas"],
        "vencidas_monto": item["vencidas_monto"],
        "proxima": (
            _cuota_response(
                proxima,
                user,
                moneda_deuda=moneda_deuda,
                monedas_cuentas=monedas_cuentas,
            )
            if proxima
            else None
        ),
        "cuotas": cuotas,
    }


def _error(exc: ValueError) -> HTTPException:
    if isinstance(exc, RecursoNoEncontradoError):
        return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=400, detail=str(exc))


@router.get(
    "/",
    response_model=list[DeudaMensualListItem],
    summary="Listar deudas mensuales con filtros",
)
def listar(
    moneda_id: Optional[int] = None,
    tipo_id: Optional[int] = None,
    estado: Optional[str] = None,
    modalidad: Optional[str] = None,
    busqueda: Optional[str] = None,
    user: User = Depends(validate_token),
):
    try:
        filas = listar_deudas_mensuales(
            user,
            moneda_id=moneda_id,
            tipo_id=tipo_id,
            estado=estado,
            modalidad=modalidad,
            busqueda=busqueda,
        )
    except ValueError as e:
        raise _error(e) from e

    return [_deuda_mensual_list_item(fila, user) for fila in filas]


@router.post(
    "/",
    status_code=201,
    response_model=DeudaMensualResponse,
    summary="Crear una deuda mensual y sus cuotas",
)
def crear(datos: DeudaMensualCreate, user: User = Depends(validate_token)):
    try:
        deuda = crear_deuda_mensual(user, **datos.model_dump())
    except ValueError as e:
        raise _error(e) from e
    return _deuda_mensual_base(deuda)


@router.get(
    "/proximas",
    response_model=list[ProximaCuotaItem],
    summary="Cuotas vencidas y proximas a vencer",
)
def proximas(
    dias: int = 7,
    moneda_id: Optional[int] = None,
    user: User = Depends(validate_token),
):
    try:
        items = proximas_cuotas(user, dias=dias, moneda_id=moneda_id)
    except ValueError as e:
        raise _error(e) from e

    return [
        {
            "cuota_id": item["cuota"].id,
            "deuda_mensual_id": item["deuda_mensual"].id,
            "descripcion": item["deuda_mensual"].descripcion,
            "moneda_id": item["deuda_mensual"].moneda_id,
            "entidad_id": item["deuda_mensual"].entidad_id,
            "tipo_id": item["deuda_mensual"].tipo_id,
            "numero": item["cuota"].numero,
            "anio": item["cuota"].anio,
            "mes": item["cuota"].mes,
            "fecha_aparicion": item["cuota"].fecha_aparicion,
            "fecha_limite": item["cuota"].fecha_limite,
            "monto": item["cuota"].monto,
            "estado": item["cuota"].estado,
            "dias_restantes": item["dias_restantes"],
            "vencida": item["vencida"],
        }
        for item in items
    ]


@router.get(
    "/resumen",
    response_model=ResumenDeudasMensuales,
    summary="Resumen de deudas mensuales",
)
def resumen(
    moneda_id: Optional[int] = None,
    user: User = Depends(validate_token),
):
    try:
        return resumen_deudas_mensuales(user, moneda_id=moneda_id)
    except ValueError as e:
        raise _error(e) from e


@router.post(
    "/pagar-lote",
    status_code=201,
    response_model=list[PagoCuotaMensualResponse],
    summary="Pagar varias cuotas en una sola transaccion",
)
def pagar_lote(
    datos: PagarCuotasMensualesCreate,
    user: User = Depends(validate_token),
):
    try:
        pagos = pagar_cuotas(
            user,
            datos.cuota_ids,
            cuenta_id=datos.cuenta_id,
            fecha=datos.fecha,
            descripcion=datos.descripcion,
        )
    except ValueError as e:
        raise _error(e) from e
    return [_pago_response(pago, user) for pago in pagos]


@router.get(
    "/{deuda_mensual_id}",
    response_model=DeudaMensualDetailResponse,
    summary="Obtener una deuda mensual con cuotas y pagos",
)
def detalle(
    deuda_mensual_id: int,
    user: User = Depends(validate_token),
):
    try:
        item = obtener_deuda_mensual(user, deuda_mensual_id)
    except ValueError as e:
        raise _error(e) from e
    return deuda_mensual_detalle_response(
        item, user, monedas_cuentas=monedas_por_cuenta(user)
    )


@router.put(
    "/{deuda_mensual_id}",
    response_model=DeudaMensualResponse,
    summary="Actualizar una deuda mensual",
)
def actualizar(
    deuda_mensual_id: int,
    datos: DeudaMensualUpdate,
    user: User = Depends(validate_token),
):
    try:
        deuda = editar_deuda_mensual(
            user, deuda_mensual_id, **datos.model_dump()
        )
    except ValueError as e:
        raise _error(e) from e
    return _deuda_mensual_base(deuda)


@router.post(
    "/{deuda_mensual_id}/cancelar",
    response_model=DeudaMensualResponse,
    summary="Cancelar una deuda mensual conservando su historial",
)
def cancelar(
    deuda_mensual_id: int,
    user: User = Depends(validate_token),
):
    try:
        deuda = cancelar_deuda_mensual(user, deuda_mensual_id)
    except ValueError as e:
        raise _error(e) from e
    return _deuda_mensual_base(deuda)


@router.delete(
    "/{deuda_mensual_id}",
    summary="Eliminar una deuda mensual, sus cuotas, pagos y movimientos",
)
def eliminar(
    deuda_mensual_id: int,
    user: User = Depends(validate_token),
):
    try:
        eliminar_deuda_mensual(user, deuda_mensual_id)
    except ValueError as e:
        raise _error(e) from e
    return {"message": "Deuda mensual eliminada"}


@router.post(
    "/cuotas/{cuota_id}/pagar",
    status_code=201,
    response_model=PagoCuotaMensualResponse,
    summary="Pagar una cuota mensual",
)
def pagar(
    cuota_id: int,
    datos: PagoCuotaMensualCreate,
    user: User = Depends(validate_token),
):
    try:
        pago = pagar_cuota(user, cuota_id, **datos.model_dump())
    except ValueError as e:
        raise _error(e) from e
    return _pago_response(pago, user)


@router.put(
    "/cuotas/{cuota_id}/pagos/{pago_id}",
    response_model=PagoCuotaMensualResponse,
    summary="Actualizar un pago de cuota",
)
def actualizar_pago(
    cuota_id: int,
    pago_id: int,
    datos: PagoCuotaMensualCreate,
    user: User = Depends(validate_token),
):
    try:
        pago = editar_pago(
            user, cuota_id, pago_id, **datos.model_dump()
        )
    except ValueError as e:
        raise _error(e) from e
    return _pago_response(pago, user)


@router.delete(
    "/cuotas/{cuota_id}/pagos/{pago_id}",
    summary="Eliminar un pago y devolver la cuota a pendiente",
)
def eliminar_pago_cuota(
    cuota_id: int,
    pago_id: int,
    user: User = Depends(validate_token),
):
    try:
        eliminar_pago(user, cuota_id, pago_id)
    except ValueError as e:
        raise _error(e) from e
    return {"message": "Pago eliminado"}
