from fastapi import APIRouter

from bd.crud.tipo import get_one_tipo, get_tipos_bd, crear_tipo_bd

from .dtos.paguinador import PaguinadorDto
from .dtos.tipos import OneId, TipoCreateDto


router = APIRouter(prefix="/tipos")

@router.get("/")
def get_tipos(paguinador: PaguinadorDto):
    return get_tipos_bd(paguinador.pagina, paguinador.cantidad)

@router.post("/", status_code=201)
def crear_tipo(tipoNew: TipoCreateDto):
    return crear_tipo_bd(tipoNew.nombre, tipoNew.descripcion)
