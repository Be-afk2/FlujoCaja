from typing import List

from fastapi import APIRouter, HTTPException

from api.routers.dtos.moneda import MonedaDTO, MonedaResponse
from bd.crud.moneda import actualizar_moneda, crear_moneda, eliminar_moneda, get_monedas, get_one_moneda

router = APIRouter(prefix="/monedas", tags=["Monedas"])

@router.get("/", response_model=List[MonedaResponse])
def listar_monedas():
    return get_monedas()

@router.post("/", status_code=201, response_model=MonedaResponse)
def crear_moneda_nueva(moneda: MonedaDTO):
    return crear_moneda(moneda.nombre, moneda.simbolo)

@router.get("/{moneda_id}", response_model=MonedaResponse)
def obtener_moneda(moneda_id: int):
    moneda = get_one_moneda(moneda_id)
    if not moneda:
        raise HTTPException(status_code=404, detail="Moneda no encontrada")
    return moneda

@router.put("/{moneda_id}", response_model=MonedaResponse)
def actualizar_moneda_existente(moneda_id: int, moneda: MonedaDTO):
    actualizada = actualizar_moneda(moneda_id, moneda.nombre, moneda.simbolo)
    if not actualizada:
        raise HTTPException(status_code=404, detail="Moneda no encontrada")
    return actualizada

@router.delete("/{moneda_id}")
def eliminar_moneda_existente(moneda_id: int):
    try:
        ok = eliminar_moneda(moneda_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not ok:
        raise HTTPException(status_code=404, detail="Moneda no encontrada")
    return {"message": "Moneda eliminada"}
