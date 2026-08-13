from datetime import date

from sqlmodel import Session, select

from bd.crud.cuenta import crear_cuenta
from bd.crud.movimiento import crear_movimiento, delete_movimiento, get_movimiento, update_movimiento
from bd.crud.resumen import get_resumen_mensual
from bd.crud.user import crear_usuario
from bd.database import engine
from bd.models import Cuenta, Moneda, ResumenMensual, TipoCuenta, User


def _crear_usuario_cuenta() -> tuple[User, Cuenta]:
    user = crear_usuario("unit", "Test", "clave123")
    with Session(engine) as s:
        moneda = s.exec(select(Moneda)).first()
        tipo_cuenta = s.exec(select(TipoCuenta)).first()
    cuenta = crear_cuenta("Efectivo", "", tipo_cuenta.id, moneda.id, user)
    return user, cuenta


def _saldo(cuenta_id: int) -> float:
    with Session(engine) as s:
        return s.get(Cuenta, cuenta_id).saldo


def _resumenes(user: User) -> list[ResumenMensual]:
    with Session(engine) as s:
        return s.exec(
            select(ResumenMensual).where(ResumenMensual.user_id == str(user.id))
        ).all()


def test_crear_movimiento_actualiza_saldo():
    user, cuenta = _crear_usuario_cuenta()
    crear_movimiento(1000.0, 1, cuenta.id, user, fecha=date(2026, 3, 15))
    assert _saldo(cuenta.id) == 1000.0

    crear_movimiento(-300.0, 1, cuenta.id, user, fecha=date(2026, 3, 20))
    assert _saldo(cuenta.id) == 700.0


def test_update_movimiento_recalcula_saldo():
    user, cuenta = _crear_usuario_cuenta()
    mov = crear_movimiento(1000.0, 1, cuenta.id, user, fecha=date(2026, 3, 15))

    update_movimiento(mov.id, user, monto=1500.0)
    assert _saldo(cuenta.id) == 1500.0

    update_movimiento(mov.id, user, monto=-200.0)
    assert _saldo(cuenta.id) == -200.0


def test_delete_movimiento_revierte_saldo():
    user, cuenta = _crear_usuario_cuenta()
    mov = crear_movimiento(500.0, 1, cuenta.id, user, fecha=date(2026, 3, 15))
    assert _saldo(cuenta.id) == 500.0

    assert delete_movimiento(mov.id, user) is True
    assert _saldo(cuenta.id) == 0.0


def test_resumen_mensual_ingresos_gastos_neto():
    user, cuenta = _crear_usuario_cuenta()
    crear_movimiento(1000.0, 1, cuenta.id, user, fecha=date(2026, 3, 5))
    crear_movimiento(-300.0, 1, cuenta.id, user, fecha=date(2026, 3, 10))
    crear_movimiento(200.0, 1, cuenta.id, user, fecha=date(2026, 4, 2))

    resumenes = _resumenes(user)
    assert len(resumenes) == 2

    marzo = next(r for r in resumenes if r.mes == 3)
    assert marzo.total_ingresos == 1000.0
    assert marzo.total_gastos == 300.0
    assert marzo.neto == 700.0


def test_resumen_mensual_se_actualiza_y_elimina():
    user, cuenta = _crear_usuario_cuenta()
    mov = crear_movimiento(1000.0, 1, cuenta.id, user, fecha=date(2026, 3, 5))

    update_movimiento(mov.id, user, monto=1500.0)
    marzo = _resumenes(user)[0]
    assert marzo.total_ingresos == 1500.0

    delete_movimiento(mov.id, user)
    assert _resumenes(user) == []


def test_usuario_no_accede_a_movimiento_de_otro():
    user_a, cuenta_a = _crear_usuario_cuenta()
    user_b = crear_usuario("unit_b", "Test", "clave123")
    mov_a = crear_movimiento(1000.0, 1, cuenta_a.id, user_a, fecha=date(2026, 3, 15))

    assert get_movimiento(mov_a.id, user_b) is None
    assert update_movimiento(mov_a.id, user_b, monto=1) is None
    assert delete_movimiento(mov_a.id, user_b) is False

    try:
        crear_movimiento(500.0, 1, cuenta_a.id, user_b)
        raise AssertionError("no debió crear un movimiento con cuenta ajena")
    except ValueError:
        pass


def test_resumen_mensual_filtra_por_moneda():
    user = crear_usuario("unit_mon", "Test", "clave123")
    with Session(engine) as s:
        monedas = s.exec(select(Moneda).limit(2)).all()
        tipo_cuenta = s.exec(select(TipoCuenta)).first()
    assert len(monedas) == 2

    cuenta_a = crear_cuenta("A", "", tipo_cuenta.id, monedas[0].id, user)
    cuenta_b = crear_cuenta("B", "", tipo_cuenta.id, monedas[1].id, user)
    crear_movimiento(1000.0, 1, cuenta_a.id, user, fecha=date(2026, 3, 5))
    crear_movimiento(200.0, 1, cuenta_b.id, user, fecha=date(2026, 3, 6))

    total = get_resumen_mensual(user, 2026, 3)
    assert len(total) == 2

    filtrado_a = get_resumen_mensual(user, 2026, 3, moneda_id=monedas[0].id)
    assert len(filtrado_a) == 1
    assert filtrado_a[0].cuenta_id == cuenta_a.id

    filtrado_b = get_resumen_mensual(user, 2026, 3, moneda_id=monedas[1].id)
    assert len(filtrado_b) == 1
    assert filtrado_b[0].cuenta_id == cuenta_b.id
