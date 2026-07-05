from datetime import date, datetime
from typing import Optional
from pydantic import BaseModel, field_validator


def _parse_fecha(v: str | None) -> date | None:
    if v is None:
        return None
    return datetime.strptime(v, "%d-%m-%Y").date()


def _format_fecha(d: date | None) -> str | None:
    if d is None:
        return None
    return d.strftime("%d-%m-%Y")


class MovimientoCreate(BaseModel):
    monto: float
    tipo_id: int
    cuenta_id: int
    subtipo_id: Optional[int] = None
    descripcion: Optional[str] = None
    fecha: Optional[str] = None

    @field_validator("fecha", mode="before")
    @classmethod
    def parse_fecha(cls, v):
        return _parse_fecha(v)


class MovimientoUpdate(BaseModel):
    monto: Optional[float] = None
    tipo_id: Optional[int] = None
    cuenta_id: Optional[int] = None
    subtipo_id: Optional[int] = None
    descripcion: Optional[str] = None
    fecha: Optional[str] = None

    @field_validator("fecha", mode="before")
    @classmethod
    def parse_fecha(cls, v):
        return _parse_fecha(v)


class MovimientoFilter(BaseModel):
    fecha_desde: Optional[str] = None
    fecha_hasta: Optional[str] = None
    cuenta_id: Optional[int] = None
    tipo_id: Optional[int] = None
    subtipo_id: Optional[int] = None
    es_ingreso: Optional[bool] = None
    pagina: int = 1
    cantidad: int = 10

    @field_validator("fecha_desde", "fecha_hasta", mode="before")
    @classmethod
    def parse_fecha_filtro(cls, v):
        return _parse_fecha(v)


class MovimientoResponse(BaseModel):
    id: int
    monto: float
    es_ingreso: bool
    tipo_id: int
    subtipo_id: Optional[int]
    cuenta_id: int
    user_id: str
    descripcion: Optional[str]
    fecha: date
