from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional, TYPE_CHECKING


if TYPE_CHECKING:
    from bd.models.user import User
    from bd.models.moneda import Moneda
    from bd.models.tipoCuenta import TipoCuenta


class Cuenta(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    saldo: float
    descripcion: Optional[str] = None

    tipo_id: int = Field(foreign_key="tipocuenta.id")
    tipo_cuenta: Optional["TipoCuenta"] = Relationship(back_populates="cuentas")

    moneda_id: int = Field(foreign_key="moneda.id")
    moneda: Optional["Moneda"] = Relationship(back_populates="cuentas")

    user_id: str = Field(foreign_key="user.id")
    user: Optional["User"] = Relationship(back_populates="cuentas")

