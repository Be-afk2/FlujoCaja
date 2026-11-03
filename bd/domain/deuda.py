"""Reglas de negocio puras para entidades y deudas.

Este modulo no conoce SQLModel ni la base de datos: solo define la tabla de
signos, los subtipos automaticos, el estado de una deuda y las validaciones.
El CRUD de deudas lo reutiliza dentro de sus transacciones.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable, Literal

Direccion = Literal["cobrar", "pagar"]
Evento = Literal["desembolso", "pago"]
EstadoDeuda = Literal["pendiente", "pagada", "vencida"]

DIRECCION_COBRAR: Direccion = "cobrar"
DIRECCION_PAGAR: Direccion = "pagar"
DIRECCIONES = (DIRECCION_COBRAR, DIRECCION_PAGAR)

EVENTO_DESEMBOLSO: Evento = "desembolso"
EVENTO_PAGO: Evento = "pago"
EVENTOS = (EVENTO_DESEMBOLSO, EVENTO_PAGO)

TIPO_DEUDAS = "Deudas"

TIPOS_ENTIDAD = ("persona", "empresa", "otro")

SUBTIPO_PRESTAMO_OTORGADO = "Préstamo otorgado"
SUBTIPO_PRESTAMO_RECIBIDO = "Préstamo recibido"
SUBTIPO_ABONO_DEUDA = "Abono deuda"
SUBTIPO_PAGO_DEUDA = "Pago deuda"
SUBTIPO_COBRO_DEUDA = "Cobro deuda"

SUBTIPOS_DEUDAS = (
    SUBTIPO_PRESTAMO_OTORGADO,
    SUBTIPO_PRESTAMO_RECIBIDO,
    SUBTIPO_ABONO_DEUDA,
    SUBTIPO_PAGO_DEUDA,
    SUBTIPO_COBRO_DEUDA,
)

_EPSILON = 1e-9

_SIGNO_CUENTA = {
    (DIRECCION_COBRAR, EVENTO_DESEMBOLSO): -1,
    (DIRECCION_COBRAR, EVENTO_PAGO): 1,
    (DIRECCION_PAGAR, EVENTO_DESEMBOLSO): 1,
    (DIRECCION_PAGAR, EVENTO_PAGO): -1,
}


def validar_direccion(direccion: str) -> None:
    if direccion not in DIRECCIONES:
        raise ValueError(
            f"Direccion invalida: {direccion!r}. Use 'cobrar' o 'pagar'"
        )


def validar_tipo_entidad(tipo: str) -> None:
    if tipo not in TIPOS_ENTIDAD:
        raise ValueError(
            f"Tipo de entidad invalido: {tipo!r}. Use uno de {TIPOS_ENTIDAD}"
        )


def validar_evento(evento: str) -> None:
    if evento not in EVENTOS:
        raise ValueError(
            f"Evento invalido: {evento!r}. Use 'desembolso' o 'pago'"
        )


def signo_cuenta(direccion: str, evento: str) -> int:
    """Signo que se aplica al saldo de la cuenta.

    - Me deben · desembolso: -1
    - Me deben · cobro/abono: +1
    - Yo debo · desembolso: +1
    - Yo debo · pago/abono: -1
    """
    validar_direccion(direccion)
    validar_evento(evento)
    return _SIGNO_CUENTA[(direccion, evento)]


def signo_pendiente(evento: str) -> int:
    """Signo que se aplica al pendiente de la deuda (desembolso suma, pago resta)."""
    validar_evento(evento)
    return 1 if evento == EVENTO_DESEMBOLSO else -1


def monto_con_signo(monto: float, direccion: str, evento: str) -> float:
    """Convierte un monto positivo en el monto firmado del movimiento de cuenta."""
    if monto <= 0:
        raise ValueError("El monto debe ser mayor que cero")
    return monto * signo_cuenta(direccion, evento)


def subtipo_deuda(direccion: str, evento: str, es_final: bool = False) -> str:
    """Devuelve el subtipo automatico bajo el tipo 'Deudas'."""
    validar_direccion(direccion)
    validar_evento(evento)

    if evento == EVENTO_DESEMBOLSO:
        return (
            SUBTIPO_PRESTAMO_OTORGADO
            if direccion == DIRECCION_COBRAR
            else SUBTIPO_PRESTAMO_RECIBIDO
        )

    if es_final:
        return (
            SUBTIPO_PAGO_DEUDA
            if direccion == DIRECCION_PAGAR
            else SUBTIPO_COBRO_DEUDA
        )

    return SUBTIPO_ABONO_DEUDA


def calcular_pendiente(monto_original: float, total_abonos: float = 0.0) -> float:
    return monto_original - total_abonos


def es_pago_final(pendiente_restante: float) -> bool:
    return pendiente_restante <= _EPSILON


def validar_monto_original(monto: float) -> None:
    if monto <= 0:
        raise ValueError("El monto original debe ser mayor que cero")


def validar_abono(monto: float, pendiente: float) -> None:
    if monto <= 0:
        raise ValueError("El monto del abono debe ser mayor que cero")
    if monto > pendiente + _EPSILON:
        raise ValueError("El abono no puede superar el pendiente de la deuda")


def estado_deuda(
    monto_original: float,
    total_abonos: float = 0.0,
    vencimiento: date | None = None,
    hoy: date | None = None,
) -> EstadoDeuda:
    pendiente = calcular_pendiente(monto_original, total_abonos)

    if pendiente <= _EPSILON:
        return "pagada"
    if vencimiento is not None and vencimiento < (hoy or date.today()):
        return "vencida"
    return "pendiente"


def monedas_distintas(moneda_deuda: int, moneda_cuenta: int) -> bool:
    """True si la cuenta del pago usa otra moneda (no se convierte, solo se avisa)."""
    return moneda_deuda != moneda_cuenta


@dataclass
class SaldoMoneda:
    moneda_id: int
    a_favor: float = 0.0
    en_contra: float = 0.0

    @property
    def neto(self) -> float:
        return self.a_favor - self.en_contra


def calcular_saldos_por_moneda(
    deudas: Iterable[tuple[int, str, float]],
) -> list[SaldoMoneda]:
    """Agrupa pendientes por moneda sin sumar monedas distintas.

    Recibe una iterable de `(moneda_id, direccion, pendiente)`.
    """
    saldos: dict[int, SaldoMoneda] = {}

    for moneda_id, direccion, pendiente in deudas:
        validar_direccion(direccion)
        saldo = saldos.setdefault(moneda_id, SaldoMoneda(moneda_id))
        if direccion == DIRECCION_COBRAR:
            saldo.a_favor += pendiente
        else:
            saldo.en_contra += pendiente

    return sorted(saldos.values(), key=lambda saldo: saldo.moneda_id)
