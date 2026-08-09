from fastapi import APIRouter, Depends, HTTPException
from typing import List

from bd.crud.tipo import get_tipos_bd, crear_tipo_bd, update_tipo_bd, delete_tipo_bd

from .dtos.paguinador import PaguinadorDto
from .dtos.tipos import TipoCreateDto, TipoListResponse, TipoUpdate


router = APIRouter(prefix="/tipos", tags=["Tipos"])

@router.get("/", response_model=List[TipoListResponse])
def get_tipos(paguinador: PaguinadorDto = Depends()):
    return get_tipos_bd(paguinador.pagina or 1, paguinador.cantidad or 10)

@router.post("/", status_code=201, response_model=TipoListResponse)
def crear_tipo(tipoNew: TipoCreateDto):
    return crear_tipo_bd(tipoNew.nombre, tipoNew.descripcion)

@router.put("/{tipo_id}", response_model=TipoListResponse)
def actualizar_tipo(tipo_id: int, datos: TipoUpdate):
    tipo = update_tipo_bd(tipo_id, datos.nombre, datos.descripcion)
    if not tipo:
        raise HTTPException(status_code=404, detail="Tipo no encontrado")
    return tipo

@router.delete("/{tipo_id}")
def eliminar_tipo(tipo_id: int):
    try:
        ok = delete_tipo_bd(tipo_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not ok:
        raise HTTPException(status_code=404, detail="Tipo no encontrado")
    return {"message": "Tipo eliminado"}
