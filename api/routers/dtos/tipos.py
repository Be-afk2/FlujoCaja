from pydantic import BaseModel
from typing import List, Optional


class TipoCreateDto(BaseModel):
    nombre: str
    descripcion: str


class OneId(BaseModel):
    id: int


class SubtipoResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]


class SubTipoCreate(BaseModel):
    nombre: str
    tipo: int


class TipoListResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]


class TipoDetailResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    subtipos: Optional[List[SubtipoResponse]]
