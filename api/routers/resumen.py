from typing import Optional

from fastapi import APIRouter, Depends, Query

from api.dependencies import validate_token
from bd.crud.resumen import get_resumen_mensual, get_resumen_rango, get_resumenes_anual, recalcular_todos
from bd.models.user import User

router = APIRouter(prefix="/resumen", tags=["Resumen"])


@router.get("/anual")
def resumen_anual(
    anio: int = Query(default_factory=lambda: 2026),
    moneda_id: Optional[int] = None,
    user: User = Depends(validate_token),
):
    return get_resumenes_anual(user, anio, moneda_id=moneda_id)


@router.get("/mensual")
def resumen_mensual(
    anio: int, mes: int, moneda_id: Optional[int] = None, user: User = Depends(validate_token)
):
    return get_resumen_mensual(user, anio, mes, moneda_id=moneda_id)


@router.get("/rango")
def resumen_rango(
    desde: str, hasta: str, moneda_id: Optional[int] = None, user: User = Depends(validate_token)
):
    ds = desde.split("-")
    hs = hasta.split("-")
    resultados = get_resumen_rango(user, int(ds[0]), int(ds[1]), int(hs[0]), int(hs[1]), moneda_id=moneda_id)
    return resultados


@router.post("/recalcular")
def recalcular(user: User = Depends(validate_token)):
    count = recalcular_todos(user)
    return {"message": f"Resumen recalculado para {count} meses"}
