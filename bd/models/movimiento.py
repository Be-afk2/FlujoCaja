from datetime import date
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Index
from sqlmodel import Field, Relationship, SQLModel

if TYPE_CHECKING:
    from bd.models.cuentas import Cuenta
    from bd.models.subTipo import Subtipo
    from bd.models.tipo import Tipo
    from bd.models.user import User


class Movimiento(SQLModel, table=True):
    # Indices compuestos para las consultas calientes (ver Fase 11 de
    # planes/porHacer4.md). Siempre se filtra por user_id, por eso va primero.
    __table_args__ = (
        Index("ix_movimiento_user_fecha", "user_id", "fecha"),
        Index("ix_movimiento_user_cuenta_fecha", "user_id", "cuenta_id", "fecha"),
        Index("ix_movimiento_user_tipo_fecha", "user_id", "tipo_id", "fecha"),
        Index("ix_movimiento_user_es_deuda_fecha", "user_id", "es_deuda", "fecha"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    monto: float
    es_ingreso: bool
    es_deuda: bool = Field(default=False)

    tipo_id: int = Field(foreign_key="tipo.id")
    tipo: Optional["Tipo"] = Relationship(back_populates="movimientos")

    subtipo_id: Optional[int] = Field(default=None, foreign_key="subtipo.id")
    subtipo: Optional["Subtipo"] = Relationship()

    user_id: str = Field(foreign_key="user.id")
    user: Optional["User"] = Relationship(back_populates="movimientos")

    cuenta_id: int = Field(foreign_key="cuenta.id")
    cuenta: Optional["Cuenta"] = Relationship(back_populates="movimientos")

    descripcion: Optional[str] = Field(default=None)

    fecha: date = Field(default_factory=date.today)
