from fastapi import APIRouter
from api.routers.dtos.moneda import MonedaDTO
from bd.crud.moneda import get_monedas, crear_moneda

router = APIRouter(prefix="/monedas")

@router.get("/")
def listar_monedas():
    return get_monedas()

@router.post("/", status_code=201)
def crear_moneda_nueva(moneda: MonedaDTO):
    return crear_moneda(moneda.nombre, moneda.simbolo)
