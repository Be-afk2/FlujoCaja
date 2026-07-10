from fastapi import APIRouter
from typing import List
from api.routers.dtos.moneda import MonedaDTO, MonedaResponse
from bd.crud.moneda import get_monedas, crear_moneda

router = APIRouter(prefix="/monedas", tags=["Monedas"])

@router.get("/", response_model=List[MonedaResponse])
def listar_monedas():
    return get_monedas()

@router.post("/", status_code=201, response_model=MonedaResponse)
def crear_moneda_nueva(moneda: MonedaDTO):
    return crear_moneda(moneda.nombre, moneda.simbolo)
