from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from bd.models.tipo import Tipo


class Subtipo(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str

    tipo_id: int = Field(foreign_key="tipo.id")

    tipo: Optional["Tipo"] = Relationship(back_populates="subtipos")