from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field

from .common import DateFromString

# Tope duro del listado: las exportaciones usan /movimientos/exportar, que no
# pagina. Evita que un `cantidad=100000` materialice toda la tabla en memoria.
MAX_MOVIMIENTOS_POR_PAGINA = 1000


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


class MovimientoFiltrosBase(BaseModel):
    fecha_desde: Optional[DateFromString] = None
    fecha_hasta: Optional[DateFromString] = None
    cuenta_id: Optional[int] = None
    moneda_id: Optional[int] = None
    tipo_id: Optional[int] = None
    subtipo_id: Optional[int] = None
    es_ingreso: Optional[bool] = None
    es_deuda: Optional[bool] = None


class MovimientoFilter(MovimientoFiltrosBase):
    pagina: int = Field(default=1, ge=1)
    cantidad: int = Field(default=10, ge=1, le=MAX_MOVIMIENTOS_POR_PAGINA)


class MovimientoExportFilter(MovimientoFiltrosBase):
    """Filtros de la exportacion CSV: no pagina, exporta todo lo que matchea."""


class MovimientoResponse(BaseModel):
    id: int
    monto: float
    es_ingreso: bool
    es_deuda: bool
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
