from typing import Optional

from sqlmodel import Session, select

from bd.crud.deuda import abonos_por_deuda, pendiente_y_estado
from bd.crud.exceptions import RecursoNoEncontradoError
from bd.database import engine
from bd.domain.deuda import calcular_saldos_por_moneda, validar_tipo_entidad
from bd.models import Deuda, Entidad, PagoDeuda, User


def _validar_entidad(session: Session, entidad_id: int, user: User) -> Entidad:
    entidad = session.get(Entidad, entidad_id)
    if not entidad or entidad.user_id != str(user.id):
        raise RecursoNoEncontradoError(f"Entidad {entidad_id} no encontrada")
    return entidad


def _normalizar_nombre(nombre: str) -> str:
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("El nombre de la entidad no puede estar vacio")
    return nombre


def crear_entidad(
    user: User,
    nombre: str,
    tipo: str = "persona",
    descripcion: Optional[str] = None,
) -> Entidad:
    nombre = _normalizar_nombre(nombre)
    validar_tipo_entidad(tipo)

    with Session(engine) as session:
        entidad = Entidad(
            user_id=str(user.id),
            nombre=nombre,
            tipo=tipo,
            descripcion=descripcion,
        )
        session.add(entidad)
        session.commit()
        session.refresh(entidad)

    return entidad


def editar_entidad(
    user: User,
    entidad_id: int,
    *,
    nombre: Optional[str] = None,
    tipo: Optional[str] = None,
    descripcion: Optional[str] = None,
) -> Entidad:
    if tipo is not None:
        validar_tipo_entidad(tipo)
    if nombre is not None:
        nombre = _normalizar_nombre(nombre)

    with Session(engine) as session:
        entidad = _validar_entidad(session, entidad_id, user)
        if nombre is not None:
            entidad.nombre = nombre
        if tipo is not None:
            entidad.tipo = tipo
        if descripcion is not None:
            entidad.descripcion = descripcion

        session.add(entidad)
        session.commit()
        session.refresh(entidad)

    return entidad


def eliminar_entidad(user: User, entidad_id: int) -> bool:
    with Session(engine) as session:
        entidad = _validar_entidad(session, entidad_id, user)
        deuda = session.exec(
            select(Deuda).where(Deuda.entidad_id == entidad.id)
        ).first()
        if deuda is not None:
            raise ValueError("No se puede eliminar una entidad con deudas")

        session.delete(entidad)
        session.commit()

    return True


def _resumen_entidad(
    entidad: Entidad,
    deudas: list[Deuda],
    abonos: dict[int, float],
) -> dict:
    deudas_detalle = []
    pendientes = 0
    proximo_vencimiento = None

    for deuda in deudas:
        total_deuda = abonos.get(deuda.id, 0.0)
        pendiente, estado = pendiente_y_estado(deuda, total_deuda)
        if estado != "pagada":
            pendientes += 1
            if deuda.vencimiento is not None and (
                proximo_vencimiento is None or deuda.vencimiento < proximo_vencimiento
            ):
                proximo_vencimiento = deuda.vencimiento
        deudas_detalle.append(
            {
                "deuda": deuda,
                "total_abonos": total_deuda,
                "pendiente": pendiente,
                "estado": estado,
            }
        )

    saldos = calcular_saldos_por_moneda(
        [
            (item["deuda"].moneda_id, item["deuda"].direccion, item["pendiente"])
            for item in deudas_detalle
            if item["estado"] != "pagada"
        ]
    )

    return {
        "entidad": entidad,
        "deudas": deudas_detalle,
        "saldos": saldos,
        "deudas_pendientes": pendientes,
        "proximo_vencimiento": proximo_vencimiento,
    }


def listar_entidades(user: User) -> list[dict]:
    with Session(engine) as session:
        entidades = session.exec(
            select(Entidad)
            .where(Entidad.user_id == str(user.id))
            .order_by(Entidad.nombre)
        ).all()
        deudas = session.exec(
            select(Deuda).where(Deuda.user_id == str(user.id))
        ).all()
        abonos = abonos_por_deuda(session, str(user.id))

        deudas_por_entidad: dict[int, list[Deuda]] = {}
        for deuda in deudas:
            deudas_por_entidad.setdefault(deuda.entidad_id, []).append(deuda)

        return [
            _resumen_entidad(
                entidad,
                deudas_por_entidad.get(entidad.id, []),
                abonos,
            )
            for entidad in entidades
        ]


def obtener_entidad(user: User, entidad_id: int) -> dict:
    with Session(engine) as session:
        entidad = _validar_entidad(session, entidad_id, user)
        deudas = session.exec(
            select(Deuda)
            .where(Deuda.entidad_id == entidad.id)
            .order_by(Deuda.fecha.desc(), Deuda.id.desc())
        ).all()
        abonos = abonos_por_deuda(session, str(user.id))

        resumen = _resumen_entidad(entidad, deudas, abonos)
        pagos_por_deuda: dict[int, list[PagoDeuda]] = {}
        for pago in session.exec(
            select(PagoDeuda)
            .where(PagoDeuda.user_id == str(user.id))
            .order_by(PagoDeuda.fecha)
        ).all():
            pagos_por_deuda.setdefault(pago.deuda_id, []).append(pago)

        for item in resumen["deudas"]:
            item["pagos"] = pagos_por_deuda.get(item["deuda"].id, [])

        return resumen
