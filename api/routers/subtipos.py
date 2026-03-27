from fastapi import APIRouter
router = APIRouter()
router = APIRouter(prefix="/subTipos")


@router.post("/create")
def crear_tipo(tipoNew:TipoCreateDto):
    return crear_tipo_bd(tipoNew.nombre,tipoNew.descripcion)