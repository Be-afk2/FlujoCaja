from fastapi import APIRouter, Depends
from typing import List

from bd.crud.tipo import get_tipos_bd, crear_tipo_bd

from .dtos.paguinador import PaguinadorDto
from .dtos.tipos import TipoCreateDto, TipoListResponse


router = APIRouter(prefix="/tipos", tags=["Tipos"])

@router.get("/", response_model=List[TipoListResponse])
def get_tipos(paguinador: PaguinadorDto = Depends()):
    return get_tipos_bd(paguinador.pagina or 1, paguinador.cantidad or 10)

@router.post("/", status_code=201, response_model=TipoListResponse)
def crear_tipo(tipoNew: TipoCreateDto):
    return crear_tipo_bd(tipoNew.nombre, tipoNew.descripcion)
