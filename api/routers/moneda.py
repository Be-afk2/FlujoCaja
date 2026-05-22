from fastapi import APIRouter
router = APIRouter()
router = APIRouter(prefix="/moneda")
from api.routers.dtos.moneda import MonedaDTO
from bd.crud.moneda import get_monedas, crear_moneda

@router.get("/")
def get_monedas_api():
    return get_monedas()

@router.post("/create")
def crear_moneda_api(moneda: MonedaDTO):
    return crear_moneda(moneda.nombre, moneda.simbolo)