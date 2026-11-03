import logging

from sqlmodel import Session, select

from bd.database import engine
from bd.domain.deuda import SUBTIPOS_DEUDAS, TIPO_DEUDAS
from bd.models import Moneda, Subtipo, Tipo, TipoCuenta

logger = logging.getLogger(__name__)


DEFAULT_MONEDAS = [
    {"nombre": "Peso argentino", "simbolo": "$"},
    {"nombre": "Dolar estadounidense", "simbolo": "US$"},
    {"nombre": "Euro", "simbolo": "€"},
    {"nombre": "peso Chileno", "simbolo": "$"},
]

DEFAULT_TIPOS = [
    {"nombre": "Alimentacion", "descripcion": "Gastos de comida y supermercado"},
    {"nombre": "Transporte", "descripcion": "Combustible, pasajes y movilidad"},
    {"nombre": "Servicios", "descripcion": "Agua, luz, internet y telefonia"},
    {"nombre": "Salud", "descripcion": "Medicamentos y atencion medica"},
    {"nombre": "Ocio", "descripcion": "Entretenimiento y recreacion"},
    {"nombre": "Sueldo", "descripcion": "Salario o sueldo mensual"},
    {"nombre": "Freelance", "descripcion": "Trabajos independientes"},
    {"nombre": "Inversiones", "descripcion": "Rendimientos de inversiones"},
    {"nombre": "Varios", "descripcion": "Otros ingresos"},
    {"nombre": TIPO_DEUDAS, "descripcion": "Préstamos, deudas y cobros"},
]

DEFAULT_SUBTIPOS = {
    TIPO_DEUDAS: list(SUBTIPOS_DEUDAS),
}

DEFAULT_TIPOS_CUENTA = [
    {"tipo": "Efectivo"},
    {"tipo": "Caja de ahorro"},
    {"tipo": "Cuenta corriente"},
    {"tipo": "Tarjeta"},
    {"tipo": "Cuenta Rut"},
]


def _seed_moneda(session: Session, nombre: str, simbolo: str) -> bool:
    existente = session.exec(select(Moneda).where(Moneda.nombre == nombre)).first()
    if existente:
        return False

    session.add(Moneda(nombre=nombre, simbolo=simbolo))
    return True


def _seed_tipo(session: Session, nombre: str, descripcion: str | None = None) -> bool:
    existente = session.exec(select(Tipo).where(Tipo.nombre == nombre)).first()
    if existente:
        return False

    session.add(Tipo(nombre=nombre, descripcion=descripcion))
    return True


def _seed_subtipo(session: Session, tipo_id: int, nombre: str) -> bool:
    existente = session.exec(
        select(Subtipo).where(Subtipo.tipo_id == tipo_id, Subtipo.nombre == nombre)
    ).first()
    if existente:
        return False

    session.add(Subtipo(nombre=nombre, tipo_id=tipo_id))
    return True


def _seed_tipo_cuenta(session: Session, tipo: str) -> bool:
    existente = session.exec(select(TipoCuenta).where(TipoCuenta.tipo == tipo)).first()
    if existente:
        return False

    session.add(TipoCuenta(tipo=tipo))
    return True


def seed_db() -> None:
    monedas_creadas = 0
    tipos_creados = 0
    subtipos_creados = 0
    tipos_cuenta_creados = 0

    with Session(engine) as session:
        for moneda in DEFAULT_MONEDAS:
            if _seed_moneda(session, moneda["nombre"], moneda["simbolo"]):
                monedas_creadas += 1

        for tipo in DEFAULT_TIPOS:
            if _seed_tipo(session, tipo["nombre"], tipo.get("descripcion")):
                tipos_creados += 1
        session.flush()

        for tipo_nombre, subtipos in DEFAULT_SUBTIPOS.items():
            tipo = session.exec(select(Tipo).where(Tipo.nombre == tipo_nombre)).first()
            if tipo is None:
                continue
            for subtipo_nombre in subtipos:
                if _seed_subtipo(session, tipo.id, subtipo_nombre):
                    subtipos_creados += 1

        for tipo_cuenta in DEFAULT_TIPOS_CUENTA:
            if _seed_tipo_cuenta(session, tipo_cuenta["tipo"]):
                tipos_cuenta_creados += 1

        session.commit()

    logger.info(
        "Seeds aplicados: %s monedas, %s tipos, %s subtipos y %s tipos de cuenta",
        monedas_creadas,
        tipos_creados,
        subtipos_creados,
        tipos_cuenta_creados,
    )
