from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from bd.models.cuentas import Cuenta


class Moneda(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str

    cuentas: List["Cuenta"] = Relationship(back_populates="moneda")