from typing import Optional

from fastapi import APIRouter, Depends, Query

from api.dependencies import validate_token
from bd.crud.resumen import get_resumen_mensual, get_resumen_rango, get_resumenes_anual, recalcular_todos
from bd.models.user import User

router = APIRouter(prefix="/resumen", tags=["Resumen"])


def _serializar_resumen(resumen, incluir_deudas: bool) -> dict:
    ingresos_deuda = 0.0 if incluir_deudas else resumen.total_ingresos_deuda
    gastos_deuda = 0.0 if incluir_deudas else resumen.total_gastos_deuda
    total_ingresos = resumen.total_ingresos - ingresos_deuda
    total_gastos = resumen.total_gastos - gastos_deuda
    return {
        "id": resumen.id,
        "user_id": resumen.user_id,
        "cuenta_id": resumen.cuenta_id,
        "anio": resumen.anio,
        "mes": resumen.mes,
        "total_ingresos": total_ingresos,
        "total_gastos": total_gastos,
        "neto": total_ingresos - total_gastos,
        "total_ingresos_deuda": resumen.total_ingresos_deuda,
        "total_gastos_deuda": resumen.total_gastos_deuda,
    }


@router.get("/anual")
def resumen_anual(
    anio: int = Query(default_factory=lambda: 2026),
    moneda_id: Optional[int] = None,
    incluir_deudas: bool = True,
    user: User = Depends(validate_token),
):
    return [
        _serializar_resumen(r, incluir_deudas)
        for r in get_resumenes_anual(user, anio, moneda_id=moneda_id)
    ]


@router.get("/mensual")
def resumen_mensual(
    anio: int,
    mes: int,
    moneda_id: Optional[int] = None,
    incluir_deudas: bool = True,
    user: User = Depends(validate_token),
):
    return [
        _serializar_resumen(r, incluir_deudas)
        for r in get_resumen_mensual(user, anio, mes, moneda_id=moneda_id)
    ]


@router.get("/rango")
def resumen_rango(
    desde: str,
    hasta: str,
    moneda_id: Optional[int] = None,
    incluir_deudas: bool = True,
    user: User = Depends(validate_token),
):
    ds = desde.split("-")
    hs = hasta.split("-")
    resultados = get_resumen_rango(
        user, int(ds[0]), int(ds[1]), int(hs[0]), int(hs[1]), moneda_id=moneda_id
    )
    return [_serializar_resumen(r, incluir_deudas) for r in resultados]


@router.post("/recalcular")
def recalcular(user: User = Depends(validate_token)):
    count = recalcular_todos(user)
    return {"message": f"Resumen recalculado para {count} meses"}
