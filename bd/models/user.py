import uuid
from typing import TYPE_CHECKING, List

from sqlalchemy import Column, String
from sqlalchemy.types import TypeDecorator
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from bd.models.cuentas import Cuenta
    from bd.models.movimiento import Movimiento


class GUID(TypeDecorator):
    """UUID guardado como texto con guiones.

    SQLAlchemy almacena `Uuid` en SQLite como 32 caracteres hex sin guiones,
    mientras que todas las columnas `user_id` guardan `str(uuid)` con guiones.
    Eso rompia las claves foraneas al activar `PRAGMA foreign_keys=ON`.
    """

    impl = String(36)
    cache_ok = True

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None or isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


class User(SQLModel, table=True):
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4,
        sa_column=Column(GUID(), primary_key=True, nullable=False),
    )
    name: str
    apellido: str
    passw: str

    movimientos: List["Movimiento"] = Relationship(back_populates="user")
    cuentas: List["Cuenta"] = Relationship(back_populates="user")


    ## user pues
