from datetime import datetime, timezone
from sqlmodel import SQLModel, Field
from typing import Optional

class Sesion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    idUser: str
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False
    )
