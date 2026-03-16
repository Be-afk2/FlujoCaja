from sqlmodel import SQLModel,Field, Relationship
from typing import List, Optional, TYPE_CHECKING

from bd.models.cuentas import Cuenta

class TipoCuenta(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tipo: str

    cuentas: List["Cuenta"] = Relationship(back_populates="tipo_cuenta")