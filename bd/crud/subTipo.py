import logging
from sqlmodel import Session
from bd.crud.tipo import get_sub_tipos
from bd.database import engine
from bd.models.subTipo import Subtipo

logger = logging.getLogger(__name__)


def crear_subTipo_bd(nombre: str, descripcion: str = None , tipoid =int) -> Subtipo:
    logger.debug("Creando subtipo nombre=%s descripcion=%s tipoid=%s", nombre, descripcion, tipoid)

    tipo = get_sub_tipos(tipoid)
    nuevo_tipo = Subtipo(nombre=nombre, descripcion=descripcion,tipo=tipo)
    with Session(engine) as session:
        session.add(nuevo_tipo)
        session.commit()
        session.refresh(nuevo_tipo)
    return nuevo_tipo
