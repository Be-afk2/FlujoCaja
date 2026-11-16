from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel

from .common import DateFromString


class DeudaMensualCreate(BaseModel):
    modalidad: str
    tipo_id: int
    moneda_id: int
    dia_aparicion: int
    dia_limite: int
    descripcion: Optional[str] = None
    monto_cuota: Optional[float] = None
    monto_total: Optional[float] = None
    cuotas_totales: Optional[int] = None
    fecha_inicio: Optional[DateFromString] = None
    entidad_id: Optional[int] = None
    subtipo_id: Optional[int] = None
    cuenta_pago_default_id: Optional[int] = None


class DeudaMensualUpdate(BaseModel):
    descripcion: Optional[str] = None
    entidad_id: Optional[int] = None
    tipo_id: Optional[int] = None
    subtipo_id: Optional[int] = None
    cuenta_pago_default_id: Optional[int] = None
    dia_aparicion: Optional[int] = None
    dia_limite: Optional[int] = None
    monto_cuota: Optional[float] = None
    monto_total: Optional[float] = None
    cuotas_totales: Optional[int] = None
    fecha_inicio: Optional[DateFromString] = None
    modalidad: Optional[str] = None


class PagoCuotaMensualCreate(BaseModel):
    cuenta_id: Optional[int] = None
    monto: Optional[float] = None
    fecha: Optional[DateFromString] = None
    descripcion: Optional[str] = None


class PagarCuotasMensualesCreate(BaseModel):
    cuota_ids: List[int]
    cuenta_id: Optional[int] = None
    fecha: Optional[DateFromString] = None
    descripcion: Optional[str] = None


class PagoCuotaMensualResponse(BaseModel):
    id: int
    cuota_id: int
    monto: float
    fecha: date
    cuenta_id: int
    movimiento_id: int
    descripcion: Optional[str]
    moneda_distinta: bool = False


class CuotaMensualResponse(BaseModel):
    id: int
    deuda_mensual_id: int
    numero: int
    anio: int
    mes: int
    fecha_aparicion: date
    fecha_limite: date
    monto: float
    estado: str
    estado_pago: Optional[str]
    pagos: List[PagoCuotaMensualResponse] = []


class DeudaMensualResponse(BaseModel):
    id: int
    entidad_id: Optional[int]
    tipo_id: int
    subtipo_id: Optional[int]
    moneda_id: int
    descripcion: Optional[str]
    modalidad: str
    monto_modo: str
    monto_cuota: float
    monto_total: Optional[float]
    cuotas_totales: Optional[int]
    dia_aparicion: int
    dia_limite: int
    fecha_inicio: date
    estado: str
    fecha_cancelacion: Optional[date]
    cuenta_pago_default_id: Optional[int]
    created_at: datetime


class DeudaMensualListItem(DeudaMensualResponse):
    pendiente: float
    pagado: float
    vencidas: int
    vencidas_monto: float
    proxima: Optional[CuotaMensualResponse]


class DeudaMensualDetailResponse(DeudaMensualListItem):
    cuotas: List[CuotaMensualResponse]


class ProximaCuotaItem(BaseModel):
    cuota_id: int
    deuda_mensual_id: int
    descripcion: Optional[str]
    moneda_id: int
    entidad_id: Optional[int]
    tipo_id: int
    numero: int
    anio: int
    mes: int
    fecha_aparicion: date
    fecha_limite: date
    monto: float
    estado: str
    dias_restantes: int
    vencida: bool


class ResumenCuotasMensuales(BaseModel):
    cantidad: int
    monto: float


class ResumenDeudasMensuales(BaseModel):
    compromiso_mensual: float
    pendiente_total: float
    vencidas: ResumenCuotasMensuales
    proximas: ResumenCuotasMensuales
    pagado_mes: float
    cuotas_mes: int
