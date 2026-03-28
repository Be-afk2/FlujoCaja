from fastapi import APIRouter

from api.routers.dtos.tipos import SubTipoCreate
from bd.crud.subTipo import crear_subTipo_bd
router = APIRouter()
router = APIRouter(prefix="/subTipos")


@router.post("/create")
def crear_tipo(tipoNew:SubTipoCreate):
    return crear_subTipo_bd(tipoNew.nombre,tipoNew.descripcion,tipoNew.tipo) 