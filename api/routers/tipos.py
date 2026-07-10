from fastapi import APIRouter
from typing import List

from bd.crud.tipo import get_tipos_bd, crear_tipo_bd

from .dtos.paguinador import PaguinadorDto
from .dtos.tipos import TipoCreateDto, TipoListResponse


router = APIRouter(prefix="/tipos", tags=["Tipos"])

@router.get("/", response_model=List[TipoListResponse])
def get_tipos(paguinador: PaguinadorDto):
    return get_tipos_bd(paguinador.pagina, paguinador.cantidad)

@router.post("/", status_code=201, response_model=TipoListResponse)
def crear_tipo(tipoNew: TipoCreateDto):
    return crear_tipo_bd(tipoNew.nombre, tipoNew.descripcion)
