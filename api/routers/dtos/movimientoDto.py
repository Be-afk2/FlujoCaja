from datetime import date, datetime
from typing import Annotated, Optional, List
from pydantic import BaseModel, BeforeValidator


def _parse_fecha(v: str | date | None) -> date | None:
    if v is None or isinstance(v, date):
        return v
    return datetime.strptime(v, "%d-%m-%Y").date()


DateFromString = Annotated[date, BeforeValidator(_parse_fecha)]


class MovimientoCreate(BaseModel):
    monto: float
    tipo_id: int
    cuenta_id: int
    subtipo_id: Optional[int] = None
    descripcion: Optional[str] = None
    fecha: Optional[DateFromString] = None


class MovimientoUpdate(BaseModel):
    monto: Optional[float] = None
    tipo_id: Optional[int] = None
    cuenta_id: Optional[int] = None
    subtipo_id: Optional[int] = None
    descripcion: Optional[str] = None
    fecha: Optional[DateFromString] = None


class MovimientoFilter(BaseModel):
    fecha_desde: Optional[DateFromString] = None
    fecha_hasta: Optional[DateFromString] = None
    cuenta_id: Optional[int] = None
    tipo_id: Optional[int] = None
    subtipo_id: Optional[int] = None
    es_ingreso: Optional[bool] = None
    pagina: int = 1
    cantidad: int = 10


class MovimientoResponse(BaseModel):
    id: int
    monto: float
    es_ingreso: bool
    tipo_id: int
    subtipo_id: Optional[int]
    cuenta_id: int
    descripcion: Optional[str]
    fecha: date


class MovimientoListResponse(BaseModel):
    data: List[MovimientoResponse]
    total: int
    pagina: int


class MovimientoImportItem(BaseModel):
    monto: float
    tipo_id: int
    cuenta_id: int
    subtipo_id: Optional[int] = None
    descripcion: Optional[str] = None
    fecha: Optional[DateFromString] = None


class MovimientoImportRequest(BaseModel):
    filas: List[MovimientoImportItem]


class MovimientoImportError(BaseModel):
    fila: int
    error: str


class MovimientoImportResponse(BaseModel):
    importados: int
    errores: List[MovimientoImportError]
