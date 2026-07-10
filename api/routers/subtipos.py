from fastapi import APIRouter, Query
from api.routers.dtos.tipos import SubTipoCreate, SubtipoResponse, TipoDetailResponse
from bd.crud.subTipo import crear_subTipo_bd
from bd.crud.tipo import get_sub_tipos

router = APIRouter(prefix="/subtipos", tags=["Subtipos"])

@router.get("/", response_model=TipoDetailResponse)
def listar_subtipos(tipo_id: int = Query(description="ID del tipo para filtrar subtipos")):
    return get_sub_tipos(tipo_id)

@router.post("/", status_code=201, response_model=SubtipoResponse)
def crear_subtipo(tipoNew: SubTipoCreate):
    return crear_subTipo_bd(tipoNew.nombre, tipoNew.tipo)
