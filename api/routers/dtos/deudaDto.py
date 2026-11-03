from datetime import date
from typing import List, Optional

from pydantic import BaseModel

from .common import DateFromString


class DeudaCreate(BaseModel):
    entidad_id: int
    direccion: str
    monto_original: float
    moneda_id: int
    descripcion: Optional[str] = None
    fecha: Optional[DateFromString] = None
    vencimiento: Optional[DateFromString] = None
    cuenta_inicial_id: Optional[int] = None


class DeudaUpdate(BaseModel):
    descripcion: Optional[str] = None
    vencimiento: Optional[DateFromString] = None
    fecha: Optional[DateFromString] = None
    monto_original: Optional[float] = None
    moneda_id: Optional[int] = None
    direccion: Optional[str] = None


class DeudaResponse(BaseModel):
    id: int
    entidad_id: int
    direccion: str
    monto_original: float
    moneda_id: int
    descripcion: Optional[str]
    fecha: date
    vencimiento: Optional[date]
    movimiento_inicial_id: Optional[int]


class DeudaListItem(DeudaResponse):
    total_abonos: float
    pendiente: float
    estado: str


class PagoDeudaCreate(BaseModel):
    monto: float
    cuenta_id: int
    fecha: Optional[DateFromString] = None
    descripcion: Optional[str] = None


class PagoDeudaUpdate(BaseModel):
    monto: Optional[float] = None
    cuenta_id: Optional[int] = None
    fecha: Optional[DateFromString] = None
    descripcion: Optional[str] = None


class PagoDeudaResponse(BaseModel):
    id: int
    deuda_id: int
    monto: float
    fecha: date
    cuenta_id: int
    movimiento_id: int
    descripcion: Optional[str]
    moneda_distinta: bool = False


class DeudaDetailResponse(DeudaListItem):
    pagos: List[PagoDeudaResponse]
