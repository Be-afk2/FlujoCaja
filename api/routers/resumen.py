from fastapi import APIRouter, Depends, Query

from bd.crud.resumen import get_resumenes_anual, get_resumen_mensual, get_resumen_rango, recalcular_todos
from bd.models.user import User
from api.dependencies import validate_token

router = APIRouter(prefix="/resumen")


@router.get("/anual")
def resumen_anual(anio: int = Query(default_factory=lambda: 2026), user: User = Depends(validate_token)):
    return get_resumenes_anual(user, anio)


@router.get("/mensual")
def resumen_mensual(anio: int, mes: int, user: User = Depends(validate_token)):
    return get_resumen_mensual(user, anio, mes)


@router.get("/rango")
def resumen_rango(desde: str, hasta: str, user: User = Depends(validate_token)):
    ds = desde.split("-")
    hs = hasta.split("-")
    resultados = get_resumen_rango(user, int(ds[0]), int(ds[1]), int(hs[0]), int(hs[1]))
    return resultados


@router.post("/recalcular")
def recalcular(user: User = Depends(validate_token)):
    count = recalcular_todos(user)
    return {"message": f"Resumen recalculado para {count} meses"}
