from fastapi import APIRouter, Query, HTTPException
from api.routers.dtos.tipos import SubTipoCreate, SubtipoResponse, SubtipoUpdate, TipoDetailResponse
from bd.crud.subTipo import crear_subTipo_bd, update_subtipo_bd, delete_subtipo_bd
from bd.crud.tipo import get_sub_tipos

router = APIRouter(prefix="/subtipos", tags=["Subtipos"])

@router.get("/", response_model=TipoDetailResponse)
def listar_subtipos(tipo_id: int = Query(description="ID del tipo para filtrar subtipos")):
    return get_sub_tipos(tipo_id)

@router.post("/", status_code=201, response_model=SubtipoResponse)
def crear_subtipo(tipoNew: SubTipoCreate):
    return crear_subTipo_bd(tipoNew.nombre, tipoNew.tipo)

@router.put("/{subtipo_id}", response_model=SubtipoResponse)
def actualizar_subtipo(subtipo_id: int, datos: SubtipoUpdate):
    subtipo = update_subtipo_bd(subtipo_id, datos.nombre)
    if not subtipo:
        raise HTTPException(status_code=404, detail="Subtipo no encontrado")
    return subtipo

@router.delete("/{subtipo_id}")
def eliminar_subtipo(subtipo_id: int):
    try:
        ok = delete_subtipo_bd(subtipo_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not ok:
        raise HTTPException(status_code=404, detail="Subtipo no encontrado")
    return {"message": "Subtipo eliminado"}
