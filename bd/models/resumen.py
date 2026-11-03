from typing import Optional

from sqlmodel import Field, SQLModel, UniqueConstraint


class ResumenMensual(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("user_id", "cuenta_id", "anio", "mes", name="uq_resumen_mensual"),
        {"sqlite_autoincrement": True},
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: str = Field(foreign_key="user.id")
    cuenta_id: int = Field(foreign_key="cuenta.id")
    anio: int
    mes: int
    total_ingresos: float = 0.0
    total_gastos: float = 0.0
    neto: float = 0.0
    total_ingresos_deuda: float = 0.0
    total_gastos_deuda: float = 0.0
