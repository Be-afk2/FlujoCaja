from datetime import date
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

if TYPE_CHECKING:
    from bd.models.cuentas import Cuenta
    from bd.models.entidad import Entidad
    from bd.models.moneda import Moneda
    from bd.models.movimiento import Movimiento


class Deuda(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)

    entidad_id: int = Field(foreign_key="entidad.id", index=True)
    entidad: Optional["Entidad"] = Relationship(back_populates="deudas")

    direccion: str
    monto_original: float

    moneda_id: int = Field(foreign_key="moneda.id")
    moneda: Optional["Moneda"] = Relationship()

    descripcion: Optional[str] = Field(default=None)
    fecha: date = Field(default_factory=date.today)
    vencimiento: Optional[date] = Field(default=None)

    movimiento_inicial_id: Optional[int] = Field(
        default=None, foreign_key="movimiento.id"
    )
    movimiento_inicial: Optional["Movimiento"] = Relationship()

    pagos: List["PagoDeuda"] = Relationship(back_populates="deuda")


class PagoDeuda(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("movimiento_id", name="uq_pagodeuda_movimiento"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)

    deuda_id: int = Field(foreign_key="deuda.id", index=True)
    deuda: Optional["Deuda"] = Relationship(back_populates="pagos")

    monto: float
    fecha: date = Field(default_factory=date.today)

    cuenta_id: int = Field(foreign_key="cuenta.id")
    cuenta: Optional["Cuenta"] = Relationship()

    movimiento_id: int = Field(foreign_key="movimiento.id")
    movimiento: Optional["Movimiento"] = Relationship()

    descripcion: Optional[str] = Field(default=None)
