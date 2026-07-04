from typing import List, TYPE_CHECKING
import uuid
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from bd.models.cuentas import Cuenta
    from bd.models.movimiento import Movimiento


class User(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    name: str
    apellido: str
    passw: str

    movimientos: List["Movimiento"] = Relationship(back_populates="user")
    cuentas: List["Cuenta"] = Relationship(back_populates="user")


    ## user pues