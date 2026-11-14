"""Reglas de negocio puras para deudas mensuales.

Este modulo no conoce SQLModel ni la base de datos: solo calcula fechas,
montos, estados y prioridades. El CRUD de deudas mensuales lo reutiliza
dentro de sus transacciones (Fase 10.3).

Reglas clave (Fase 10.2):

- Los dias de aparicion y limite son 1-31; si el mes no tiene ese dia se usa
  el ultimo disponible.
- Si ``dia_limite < dia_aparicion`` el limite cae el mes siguiente.
- La primera cuota pertenece siempre al mes de ``fecha_inicio``, aunque el
  dia de aparicion ya haya pasado.
- Recurrente: se generan cuotas desde ``fecha_inicio`` hasta
  ``max(mes actual + 1, mes de inicio + 1)``.
- Plan: se generan las N cuotas; la ultima absorbe el ajuste de centavos.
- ``futura`` significa ``fecha_aparicion > hoy`` (editar y cancelar).
"""

from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import date
from typing import Iterable

from bd.domain.deuda import monedas_distintas

MODALIDAD_RECURRENTE = "recurrente"
MODALIDAD_CUOTAS = "cuotas"
MODALIDADES = (MODALIDAD_RECURRENTE, MODALIDAD_CUOTAS)

MONTO_MODO_FIJO = "fijo"
MONTO_MODO_CALCULADO = "calculado"
MONTOS_MODO = (MONTO_MODO_FIJO, MONTO_MODO_CALCULADO)

ESTADO_DEUDA_ACTIVA = "activa"
ESTADO_DEUDA_CANCELADA = "cancelada"
ESTADOS_DEUDA_MENSUAL = (ESTADO_DEUDA_ACTIVA, ESTADO_DEUDA_CANCELADA)

ESTADO_CUOTA_PENDIENTE = "pendiente"
ESTADO_CUOTA_PAGADA = "pagada"
ESTADO_CUOTA_CANCELADA = "cancelada"
ESTADOS_CUOTA = (
    ESTADO_CUOTA_PENDIENTE,
    ESTADO_CUOTA_PAGADA,
    ESTADO_CUOTA_CANCELADA,
)

ESTADO_PAGO_ANTES_DE_TIEMPO = "antes_de_tiempo"
ESTADO_PAGO_AL_DIA = "al_dia"
ESTADO_PAGO_ATRASADA = "atrasada"
ESTADOS_PAGO = (
    ESTADO_PAGO_ANTES_DE_TIEMPO,
    ESTADO_PAGO_AL_DIA,
    ESTADO_PAGO_ATRASADA,
)

SIGNO_PAGO_CUOTA = -1

_EPSILON = 1e-9


@dataclass(frozen=True)
class CuotaCalculada:
    """Cuota generada por las reglas, aun sin persistir."""

    numero: int
    anio: int
    mes: int
    fecha_aparicion: date
    fecha_limite: date
    monto: float


def ultimo_dia_mes(anio: int, mes: int) -> int:
    return calendar.monthrange(anio, mes)[1]


def dia_efectivo(anio: int, mes: int, dia: int) -> int:
    """Dia real dentro del mes (1-31 ajustado al ultimo dia disponible)."""
    validar_dia(dia)
    return min(dia, ultimo_dia_mes(anio, mes))


def fecha_en_mes(anio: int, mes: int, dia: int) -> date:
    return date(anio, mes, dia_efectivo(anio, mes, dia))


def sumar_meses(anio: int, mes: int, cantidad: int) -> tuple[int, int]:
    """Suma ``cantidad`` meses a (anio, mes) y normaliza el resultado."""
    total = anio * 12 + (mes - 1) + cantidad
    return total // 12, total % 12 + 1


def fechas_cuota(
    anio: int,
    mes: int,
    dia_aparicion: int,
    dia_limite: int,
) -> tuple[date, date]:
    """Fechas de aparicion y limite para la cuota del mes indicado.

    Si ``dia_limite < dia_aparicion`` el limite cae el mes siguiente.
    """
    validar_dia(dia_aparicion)
    validar_dia(dia_limite)

    aparicion = fecha_en_mes(anio, mes, dia_aparicion)
    if dia_limite < dia_aparicion:
        anio_limite, mes_limite = sumar_meses(anio, mes, 1)
    else:
        anio_limite, mes_limite = anio, mes
    limite = fecha_en_mes(anio_limite, mes_limite, dia_limite)
    return aparicion, limite


def _iterar_meses(
    desde: tuple[int, int],
    hasta: tuple[int, int],
) -> Iterable[tuple[int, int]]:
    anio, mes = desde
    while (anio, mes) <= hasta:
        yield anio, mes
        anio, mes = sumar_meses(anio, mes, 1)


def generar_cuotas_plan(
    fecha_inicio: date,
    dia_aparicion: int,
    dia_limite: int,
    monto_total: float,
    cuotas_totales: int,
) -> list[CuotaCalculada]:
    """Genera las N cuotas de un plan, con la primera en el mes de inicio."""
    validar_monto_total_plan(monto_total)
    validar_cuotas_totales(cuotas_totales)

    montos = montos_cuotas(monto_total, cuotas_totales)
    desde = (fecha_inicio.year, fecha_inicio.month)
    hasta = sumar_meses(desde[0], desde[1], cuotas_totales - 1)

    cuotas: list[CuotaCalculada] = []
    for numero, (anio, mes) in enumerate(_iterar_meses(desde, hasta), start=1):
        aparicion, limite = fechas_cuota(anio, mes, dia_aparicion, dia_limite)
        cuotas.append(
            CuotaCalculada(
                numero=numero,
                anio=anio,
                mes=mes,
                fecha_aparicion=aparicion,
                fecha_limite=limite,
                monto=montos[numero - 1],
            )
        )
    return cuotas


def generar_cuotas_recurrente(
    fecha_inicio: date,
    dia_aparicion: int,
    dia_limite: int,
    monto_cuota: float,
    hoy: date | None = None,
) -> list[CuotaCalculada]:
    """Genera cuotas recurrentes hasta ``max(hoy + 1, inicio + 1)``.

    Si ``fecha_inicio`` es futura se genera al menos hasta el mes siguiente al
    inicio, permitiendo pagos anticipados.
    """
    validar_monto_cuota(monto_cuota)

    hoy = hoy or date.today()
    desde = (fecha_inicio.year, fecha_inicio.month)
    fin_por_hoy = sumar_meses(hoy.year, hoy.month, 1)
    fin_por_inicio = sumar_meses(desde[0], desde[1], 1)
    hasta = max(fin_por_hoy, fin_por_inicio)

    cuotas: list[CuotaCalculada] = []
    for numero, (anio, mes) in enumerate(_iterar_meses(desde, hasta), start=1):
        aparicion, limite = fechas_cuota(anio, mes, dia_aparicion, dia_limite)
        cuotas.append(
            CuotaCalculada(
                numero=numero,
                anio=anio,
                mes=mes,
                fecha_aparicion=aparicion,
                fecha_limite=limite,
                monto=monto_cuota,
            )
        )
    return cuotas


def montos_cuotas(monto_total: float, cuotas: int) -> list[float]:
    """Divide el total en cuotas; la ultima absorbe el ajuste de centavos."""
    validar_monto_total_plan(monto_total)
    validar_cuotas_totales(cuotas)

    base = round(monto_total / cuotas, 2)
    montos = [base] * (cuotas - 1)
    montos.append(round(monto_total - base * (cuotas - 1), 2))
    return montos


def monto_cuota_plan(monto_total: float, cuotas: int) -> float:
    """Monto de referenia de una cuota de plan (la primera)."""
    return montos_cuotas(monto_total, cuotas)[0]


def estado_pago_cuota(
    fecha_pago: date,
    fecha_aparicion: date,
    fecha_limite: date,
) -> str:
    """Estado del pago comparado con la aparicion y el limite de la cuota."""
    if fecha_pago < fecha_aparicion:
        return ESTADO_PAGO_ANTES_DE_TIEMPO
    if fecha_pago <= fecha_limite:
        return ESTADO_PAGO_AL_DIA
    return ESTADO_PAGO_ATRASADA


def es_cuota_futura(fecha_aparicion: date, hoy: date | None = None) -> bool:
    return fecha_aparicion > (hoy or date.today())


def debe_cancelarse(
    estado: str,
    fecha_aparicion: date,
    hoy: date | None = None,
) -> bool:
    """Una cuota se cancela con la plantilla solo si es futura e impaga."""
    return estado == ESTADO_CUOTA_PENDIENTE and es_cuota_futura(
        fecha_aparicion, hoy
    )


def puede_editarse(
    estado: str,
    fecha_aparicion: date,
    hoy: date | None = None,
) -> bool:
    """Editar la plantilla solo afecta cuotas futuras impagas."""
    return debe_cancelarse(estado, fecha_aparicion, hoy)


def es_vencida(
    estado: str,
    fecha_limite: date,
    hoy: date | None = None,
) -> bool:
    return estado == ESTADO_CUOTA_PENDIENTE and fecha_limite < (
        hoy or date.today()
    )


def clave_prioridad(
    estado: str,
    fecha_limite: date,
    hoy: date | None = None,
) -> tuple[int, date]:
    """Clave de orden: vencidas, luego proximas, despues el resto.

    Dentro de cada grupo se ordena por fecha limite.
    """
    if es_vencida(estado, fecha_limite, hoy):
        return 0, fecha_limite
    if estado == ESTADO_CUOTA_PENDIENTE:
        return 1, fecha_limite
    return 2, fecha_limite


def monto_movimiento_pago(monto: float) -> float:
    """El pago de una cuota siempre genera un movimiento negativo (gasto)."""
    validar_monto_cuota(monto)
    return monto * SIGNO_PAGO_CUOTA


def validar_dia(dia: int) -> None:
    if not isinstance(dia, int) or not 1 <= dia <= 31:
        raise ValueError(f"Dia invalido: {dia!r}. Debe estar entre 1 y 31")


def validar_modalidad(modalidad: str) -> None:
    if modalidad not in MODALIDADES:
        raise ValueError(
            f"Modalidad invalida: {modalidad!r}. Use {MODALIDADES}"
        )


def validar_monto_modo(monto_modo: str) -> None:
    if monto_modo not in MONTOS_MODO:
        raise ValueError(
            f"Modo de monto invalido: {monto_modo!r}. Use {MONTOS_MODO}"
        )


def validar_monto_cuota(monto: float) -> None:
    if monto <= 0:
        raise ValueError("El monto de la cuota debe ser mayor que cero")


def validar_monto_total_plan(monto: float) -> None:
    if monto <= 0:
        raise ValueError("El monto total del plan debe ser mayor que cero")


def validar_cuotas_totales(cuotas: int) -> None:
    if not isinstance(cuotas, int) or cuotas < 1:
        raise ValueError("El numero de cuotas debe ser mayor que cero")


def validar_monto_pago(monto: float, monto_cuota: float) -> None:
    """El pago es completo: el monto debe coincidir con el de la cuota."""
    validar_monto_cuota(monto)
    if abs(monto - monto_cuota) > _EPSILON:
        raise ValueError(
            "El pago debe ser completo e igual al monto de la cuota "
            f"({monto_cuota})"
        )


def validar_plantilla(
    *,
    modalidad: str,
    monto_modo: str,
    monto_cuota: float,
    monto_total: float | None = None,
    cuotas_totales: int | None = None,
    dia_aparicion: int,
    dia_limite: int,
) -> None:
    """Valida la coherencia de una plantilla antes de persistirla."""
    validar_modalidad(modalidad)
    validar_monto_modo(monto_modo)
    validar_dia(dia_aparicion)
    validar_dia(dia_limite)
    validar_monto_cuota(monto_cuota)

    if modalidad == MODALIDAD_RECURRENTE:
        if monto_modo != MONTO_MODO_FIJO:
            raise ValueError("Una deuda recurrente debe usar monto_modo='fijo'")
        return

    if monto_modo != MONTO_MODO_CALCULADO:
        raise ValueError("Un plan de cuotas debe usar monto_modo='calculado'")
    if monto_total is None:
        raise ValueError("Un plan de cuotas requiere monto_total")
    validar_monto_total_plan(monto_total)
    if cuotas_totales is None:
        raise ValueError("Un plan de cuotas requiere cuotas_totales")
    validar_cuotas_totales(cuotas_totales)


__all__ = [
    "MODALIDAD_RECURRENTE",
    "MODALIDAD_CUOTAS",
    "MODALIDADES",
    "MONTO_MODO_FIJO",
    "MONTO_MODO_CALCULADO",
    "MONTOS_MODO",
    "ESTADO_DEUDA_ACTIVA",
    "ESTADO_DEUDA_CANCELADA",
    "ESTADOS_DEUDA_MENSUAL",
    "ESTADO_CUOTA_PENDIENTE",
    "ESTADO_CUOTA_PAGADA",
    "ESTADO_CUOTA_CANCELADA",
    "ESTADOS_CUOTA",
    "ESTADO_PAGO_ANTES_DE_TIEMPO",
    "ESTADO_PAGO_AL_DIA",
    "ESTADO_PAGO_ATRASADA",
    "ESTADOS_PAGO",
    "SIGNO_PAGO_CUOTA",
    "CuotaCalculada",
    "ultimo_dia_mes",
    "dia_efectivo",
    "fecha_en_mes",
    "sumar_meses",
    "fechas_cuota",
    "generar_cuotas_plan",
    "generar_cuotas_recurrente",
    "montos_cuotas",
    "monto_cuota_plan",
    "estado_pago_cuota",
    "es_cuota_futura",
    "debe_cancelarse",
    "puede_editarse",
    "es_vencida",
    "clave_prioridad",
    "monto_movimiento_pago",
    "validar_dia",
    "validar_modalidad",
    "validar_monto_modo",
    "validar_monto_cuota",
    "validar_monto_total_plan",
    "validar_cuotas_totales",
    "validar_monto_pago",
    "validar_plantilla",
    "monedas_distintas",
]
