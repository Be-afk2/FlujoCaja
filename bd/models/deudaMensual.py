from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlmodel import Field, Relationship, SQLModel, UniqueConstraint

if TYPE_CHECKING:
    from bd.models.cuentas import Cuenta
    from bd.models.entidad import Entidad
    from bd.models.moneda import Moneda
    from bd.models.movimiento import Movimiento
    from bd.models.subTipo import Subtipo
    from bd.models.tipo import Tipo


class DeudaMensual(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)

    entidad_id: Optional[int] = Field(
        default=None, foreign_key="entidad.id", index=True
    )
    entidad: Optional["Entidad"] = Relationship(back_populates="deudas_mensuales")

    tipo_id: int = Field(foreign_key="tipo.id")
    tipo: Optional["Tipo"] = Relationship()

    subtipo_id: Optional[int] = Field(default=None, foreign_key="subtipo.id")
    subtipo: Optional["Subtipo"] = Relationship()

    moneda_id: int = Field(foreign_key="moneda.id")
    moneda: Optional["Moneda"] = Relationship()

    descripcion: Optional[str] = Field(default=None)

    modalidad: str
    monto_modo: str = Field(default="fijo")
    monto_cuota: float
    monto_total: Optional[float] = Field(default=None)
    cuotas_totales: Optional[int] = Field(default=None)

    dia_aparicion: int
    dia_limite: int
    fecha_inicio: date = Field(default_factory=date.today)

    estado: str = Field(default="activa", index=True)
    fecha_cancelacion: Optional[date] = Field(default=None)

    cuenta_pago_default_id: Optional[int] = Field(
        default=None, foreign_key="cuenta.id"
    )
    cuenta_pago_default: Optional["Cuenta"] = Relationship()

    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    cuotas: List["CuotaMensual"] = Relationship(back_populates="deuda_mensual")


class CuotaMensual(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "deuda_mensual_id", "numero", name="uq_cuotamensual_deuda_numero"
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)

    deuda_mensual_id: int = Field(foreign_key="deudamensual.id", index=True)
    deuda_mensual: Optional["DeudaMensual"] = Relationship(back_populates="cuotas")

    numero: int
    anio: int
    mes: int

    fecha_aparicion: date
    fecha_limite: date

    monto: float
    estado: str = Field(default="pendiente", index=True)
    estado_pago: Optional[str] = Field(default=None)

    pagos: List["PagoCuotaMensual"] = Relationship(back_populates="cuota")


class PagoCuotaMensual(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("cuota_id", name="uq_pagocuotamensual_cuota"),
        UniqueConstraint("movimiento_id", name="uq_pagocuotamensual_movimiento"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id", index=True)

    cuota_id: int = Field(foreign_key="cuotamensual.id", index=True)
    cuota: Optional["CuotaMensual"] = Relationship(back_populates="pagos")

    monto: float
    fecha: date = Field(default_factory=date.today)

    cuenta_id: int = Field(foreign_key="cuenta.id")
    cuenta: Optional["Cuenta"] = Relationship()

    movimiento_id: int = Field(foreign_key="movimiento.id")
    movimiento: Optional["Movimiento"] = Relationship()

    descripcion: Optional[str] = Field(default=None)
