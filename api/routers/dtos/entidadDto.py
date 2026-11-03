from datetime import date
from typing import List, Optional

from pydantic import BaseModel

from .deudaDto import DeudaDetailResponse


class EntidadCreate(BaseModel):
    nombre: str
    tipo: str = "persona"
    descripcion: Optional[str] = None


class EntidadUpdate(BaseModel):
    nombre: Optional[str] = None
    tipo: Optional[str] = None
    descripcion: Optional[str] = None


class EntidadResponse(BaseModel):
    id: int
    nombre: str
    tipo: str
    descripcion: Optional[str]


class SaldoEntidad(BaseModel):
    moneda_id: int
    a_favor: float
    en_contra: float
    neto: float


class EntidadListItem(EntidadResponse):
    saldos: List[SaldoEntidad]
    deudas_pendientes: int
    proximo_vencimiento: Optional[date]


class EntidadDetailResponse(EntidadListItem):
    deudas: List[DeudaDetailResponse]
