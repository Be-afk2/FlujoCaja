from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from bd.models.movimiento import Movimiento
    from bd.models.subTipo import Subtipo


class Tipo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    descripcion: Optional[str] = None

    movimientos: List["Movimiento"] = Relationship(back_populates="tipo")
    subtipos: List["Subtipo"] = Relationship(back_populates="tipo")