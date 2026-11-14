from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from bd.models.deuda import Deuda
    from bd.models.deudaMensual import DeudaMensual


class Entidad(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)
    nombre: str
    tipo: str = "persona"
    descripcion: Optional[str] = Field(default=None)

    deudas: List["Deuda"] = Relationship(back_populates="entidad")
    deudas_mensuales: List["DeudaMensual"] = Relationship(back_populates="entidad")
