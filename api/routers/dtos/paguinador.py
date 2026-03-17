from pydantic import BaseModel
from sqlmodel import SQLModel
from typing import Optional

class PaguinadorDto(BaseModel):
    cantidad: Optional[int] = None
    pagina: Optional[int] = None