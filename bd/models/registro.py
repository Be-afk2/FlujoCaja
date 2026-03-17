from datetime import datetime
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, TYPE_CHECKING


if TYPE_CHECKING:
    from bd.models.user import User
    from bd.models.tipo import Tipo
    from bd.models.cuentas import Cuenta


class Registro(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    monto: float
    es_ingreso: bool

    tipo_id: int = Field(foreign_key="tipo.id")
    tipo: Optional["Tipo"] = Relationship(back_populates="registros")

    user_id: str = Field(foreign_key="user.id")
    user: Optional["User"] = Relationship(back_populates="registros")


    cuenta_id: str = Field(foreign_key="cuenta.id")
    cuenta: Optional["Cuenta"] = Relationship(back_populates="registros")

    #fecha de solo dd/mm/aaaa
    fecha: datetime = Field(default_factory=datetime.now)
    
    tipo: "Tipo" = Relationship()

# historial de gastos 