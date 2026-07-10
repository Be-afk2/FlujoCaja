from pydantic import BaseModel


class MonedaDTO(BaseModel):
    nombre: str
    simbolo: str


class MonedaResponse(BaseModel):
    id: int
    nombre: str
    simbolo: str
