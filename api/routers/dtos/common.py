from datetime import date, datetime
from typing import Annotated

from pydantic import BeforeValidator


def _parse_fecha(v: str | date | None) -> date | None:
    if v is None or isinstance(v, date):
        return v
    return datetime.strptime(v, "%d-%m-%Y").date()


DateFromString = Annotated[date, BeforeValidator(_parse_fecha)]
