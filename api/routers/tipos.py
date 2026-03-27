from fastapi import APIRouter

from bd.crud.tipo import get_one_tipo, get_sub_tipos, get_tipo_lista, get_tipos_bd,crear_tipo_bd

from .dtos.paguinador import PaguinadorDto
from .dtos.tipos import OneId, TipoCreateDto


router = APIRouter()
router = APIRouter(prefix="/tipos")

@router.get("/")
def get_test(paguinador:PaguinadorDto):
    return  get_tipos_bd(paguinador.pagina,paguinador.cantidad)

@router.get("/lista")
def get_lista(paguinador:PaguinadorDto):
    return get_tipo_lista(paguinador.pagina,paguinador.cantidad)


@router.post("/create")
def crear_tipo(tipoNew:TipoCreateDto):
    return crear_tipo_bd(tipoNew.nombre,tipoNew.descripcion)
 
 
@router.get("/one/name")
def get_one():
    return get_one_tipo()


@router.get("/subtipo/{tipo_id}")
def get_sub(tipo_id: int):
    return get_sub_tipos(tipo_id)