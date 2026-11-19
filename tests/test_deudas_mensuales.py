from datetime import date, timedelta

import pytest
from sqlmodel import Session, select

from bd.database import engine
from bd.models import CuotaMensual


def _fecha_api(fecha: date) -> str:
    return fecha.strftime("%d-%m-%Y")


def _fecha(valor: str) -> date:
    return date.fromisoformat(valor)


def _saldo(client, headers, cuenta_id: int) -> float:
    cuentas = client.get("/cuentas/", headers=headers).json()
    return next(c["saldo"] for c in cuentas if c["id"] == cuenta_id)


def _detalle(client, headers, deuda_id: int) -> dict:
    r = client.get(f"/deudas-mensuales/{deuda_id}", headers=headers)
    assert r.status_code == 200, r.text
    return r.json()


def _cuota(detalle: dict, numero: int = 1) -> dict:
    return next(c for c in detalle["cuotas"] if c["numero"] == numero)


def _pagar_cuota(
    client,
    headers,
    cuota_id: int,
    cuenta_id: int,
    *,
    fecha: date | None = None,
    descripcion: str | None = None,
) -> dict:
    body: dict = {"cuenta_id": cuenta_id}
    if fecha is not None:
        body["fecha"] = _fecha_api(fecha)
    if descripcion is not None:
        body["descripcion"] = descripcion
    r = client.post(
        f"/deudas-mensuales/cuotas/{cuota_id}/pagar",
        json=body,
        headers=headers,
    )
    assert r.status_code == 201, r.text
    return r.json()


def _totales_resumen(client, headers, moneda_id: int) -> dict:
    hoy = date.today()
    filas = client.get(
        "/resumen/mensual",
        params={"anio": hoy.year, "mes": hoy.month, "moneda_id": moneda_id},
        headers=headers,
    ).json()
    return {
        campo: round(sum(fila[campo] for fila in filas), 2)
        for campo in (
            "total_ingresos",
            "total_gastos",
            "total_ingresos_deuda",
            "total_gastos_deuda",
        )
    }


def test_recurrente_sin_entidad_genera_cuotas(
    client, auth_headers, crear_tipo, crear_deuda_mensual
):
    headers = auth_headers("mensual_recurrente")
    tipo = crear_tipo(headers, nombre="Suscripciones")

    deuda = crear_deuda_mensual(
        headers,
        tipo_id=tipo["id"],
        descripcion="Internet",
        monto_cuota=1500.0,
        dia_aparicion=1,
        dia_limite=5,
    )

    assert deuda["entidad_id"] is None
    assert deuda["modalidad"] == "recurrente"
    assert deuda["monto_modo"] == "fijo"
    assert deuda["monto_cuota"] == 1500.0
    assert deuda["estado"] == "activa"

    detalle = _detalle(client, headers, deuda["id"])
    assert len(detalle["cuotas"]) >= 2
    assert [c["numero"] for c in detalle["cuotas"]] == list(
        range(1, len(detalle["cuotas"]) + 1)
    )
    assert all(c["monto"] == 1500.0 for c in detalle["cuotas"])
    assert all(c["estado"] == "pendiente" for c in detalle["cuotas"])
    assert client.get("/movimientos/", headers=headers).json()["total"] == 0


def test_lecturas_no_sincronizan_cuotas_y_post_es_idempotente(
    client, auth_headers, crear_entidad, crear_deuda_mensual
):
    headers = auth_headers("mensual_sync_explicito")
    entidad = crear_entidad(headers, nombre="Entidad sync")
    deuda = crear_deuda_mensual(
        headers, entidad_id=entidad["id"], monto_cuota=120.0
    )

    with Session(engine) as session:
        cuotas = session.exec(
            select(CuotaMensual)
            .where(CuotaMensual.deuda_mensual_id == deuda["id"])
            .order_by(CuotaMensual.numero)
        ).all()
        assert cuotas
        cuota_eliminada = cuotas[-1]
        cuota_id, numero = cuota_eliminada.id, cuota_eliminada.numero
        cuotas_esperadas = [
            (cuota.id, cuota.fecha_limite)
            for cuota in cuotas[:-1]
        ]
        session.delete(cuota_eliminada)
        session.commit()

    # Las lecturas no generan ni cambian cuotas, aunque falte una ocurrencia.
    assert client.get("/deudas-mensuales/", headers=headers).status_code == 200
    assert client.get(
        f"/deudas-mensuales/{deuda['id']}", headers=headers
    ).status_code == 200
    assert client.get("/deudas-mensuales/proximas", headers=headers).status_code == 200
    assert client.get("/deudas-mensuales/resumen", headers=headers).status_code == 200
    assert client.get("/entidades/", headers=headers).status_code == 200
    assert client.get(
        f"/entidades/{entidad['id']}", headers=headers
    ).status_code == 200
    with Session(engine) as session:
        assert session.get(CuotaMensual, cuota_id) is None
        cuotas_leidas = session.exec(
            select(CuotaMensual.id, CuotaMensual.fecha_limite).where(
                CuotaMensual.deuda_mensual_id == deuda["id"]
            )
        ).all()
        assert {
            (int(id_leida), fecha_limite)
            for id_leida, fecha_limite in cuotas_leidas
        } == set(cuotas_esperadas)

    sincronizada = client.post(
        "/deudas-mensuales/sincronizar", headers=headers
    )
    assert sincronizada.status_code == 200, sincronizada.text
    assert sincronizada.json()["cuotas_creadas"] == 1
    with Session(engine) as session:
        restaurada = session.exec(
            select(CuotaMensual).where(
                CuotaMensual.deuda_mensual_id == deuda["id"],
                CuotaMensual.numero == numero,
            )
        ).first()
        assert restaurada is not None
        fecha_limite = restaurada.fecha_limite

    segunda = client.post("/deudas-mensuales/sincronizar", headers=headers)
    assert segunda.status_code == 200, segunda.text
    assert segunda.json()["cuotas_creadas"] == 0
    with Session(engine) as session:
        restaurada = session.exec(
            select(CuotaMensual).where(
                CuotaMensual.deuda_mensual_id == deuda["id"],
                CuotaMensual.numero == numero,
            )
        ).first()
        assert restaurada.fecha_limite == fecha_limite


@pytest.mark.parametrize(
    "modo,esperado",
    [
        ("antes", "antes_de_tiempo"),
        ("dia", "al_dia"),
        ("atrasada", "atrasada"),
    ],
)
def test_estado_pago_segun_fecha(
    client,
    auth_headers,
    crear_cuenta,
    crear_deuda_mensual,
    modo,
    esperado,
):
    headers = auth_headers(f"mensual_estado_{modo}")
    cuenta = crear_cuenta(headers)
    deuda = crear_deuda_mensual(
        headers,
        monto_cuota=500.0,
        dia_aparicion=10,
        dia_limite=20,
    )
    cuota = _cuota(_detalle(client, headers, deuda["id"]))
    aparicion = _fecha(cuota["fecha_aparicion"])
    limite = _fecha(cuota["fecha_limite"])

    if modo == "antes":
        fecha_pago = aparicion - timedelta(days=1)
    elif modo == "dia":
        fecha_pago = aparicion
    else:
        fecha_pago = limite + timedelta(days=1)

    _pagar_cuota(client, headers, cuota["id"], cuenta["id"], fecha=fecha_pago)

    actualizada = _cuota(_detalle(client, headers, deuda["id"]))
    assert actualizada["estado"] == "pagada"
    assert actualizada["estado_pago"] == esperado
    assert len(actualizada["pagos"]) == 1


def test_pago_crea_movimiento_categoria_saldo_y_resumen(
    client, auth_headers, crear_cuenta, crear_tipo, crear_deuda_mensual, obtener_moneda
):
    headers = auth_headers("mensual_movimiento")
    moneda_id = obtener_moneda(headers)
    tipo = crear_tipo(headers, nombre="Alquiler")
    cuenta = crear_cuenta(headers)
    deuda = crear_deuda_mensual(
        headers,
        tipo_id=tipo["id"],
        moneda_id=moneda_id,
        descripcion="Alquiler oficina",
        monto_cuota=1200.0,
    )
    cuota = _cuota(_detalle(client, headers, deuda["id"]))

    pago = _pagar_cuota(
        client,
        headers,
        cuota["id"],
        cuenta["id"],
        fecha=date.today(),
    )

    movimiento = client.get(
        f"/movimientos/{pago['movimiento_id']}", headers=headers
    ).json()
    assert movimiento["es_deuda"] is True
    assert movimiento["monto"] == -1200.0
    assert movimiento["tipo_id"] == tipo["id"]
    assert movimiento["descripcion"] == "Alquiler oficina"
    assert _saldo(client, headers, cuenta["id"]) == -1200.0

    totales = _totales_resumen(client, headers, moneda_id)
    assert totales["total_ingresos"] == 0.0
    assert totales["total_gastos"] == 1200.0
    assert totales["total_ingresos_deuda"] == 0.0
    assert totales["total_gastos_deuda"] == 1200.0


def test_detalle_marca_moneda_distinta_en_pagos_de_cuotas(
    client,
    auth_headers,
    crear_cuenta,
    crear_entidad,
    crear_deuda_mensual,
    obtener_moneda,
):
    headers = auth_headers("mensual_moneda")
    moneda_deuda = obtener_moneda(headers)
    moneda_otra = obtener_moneda(headers, indice=1)
    entidad = crear_entidad(headers, nombre="Inmobiliaria")
    cuenta_otra = crear_cuenta(headers, nombre="Cuenta en otra moneda", moneda=moneda_otra)

    deuda = crear_deuda_mensual(
        headers,
        moneda_id=moneda_deuda,
        entidad_id=entidad["id"],
        monto_cuota=500.0,
    )
    cuota = _cuota(_detalle(client, headers, deuda["id"]))
    pago = _pagar_cuota(client, headers, cuota["id"], cuenta_otra["id"])
    assert pago["moneda_distinta"] is True

    # El detalle resuelve la moneda de todas las cuentas en una sola consulta
    # (sin abrir una sesion por pago).
    cuota_pagada = _cuota(_detalle(client, headers, deuda["id"]))
    assert [p["id"] for p in cuota_pagada["pagos"]] == [pago["id"]]
    assert cuota_pagada["pagos"][0]["moneda_distinta"] is True

    detalle_entidad = client.get(
        f"/entidades/{entidad['id']}", headers=headers
    ).json()
    mensual = detalle_entidad["deudas_mensuales"][0]
    assert mensual["cuotas"][0]["pagos"][0]["moneda_distinta"] is True


def test_plan_divide_total_ajusta_centavos_y_finaliza(
    client, auth_headers, crear_cuenta, crear_deuda_mensual
):
    headers = auth_headers("mensual_plan")
    cuenta = crear_cuenta(headers)
    deuda = crear_deuda_mensual(
        headers,
        modalidad="cuotas",
        monto_cuota=None,
        monto_total=1000.0,
        cuotas_totales=3,
    )
    detalle = _detalle(client, headers, deuda["id"])

    assert [c["monto"] for c in detalle["cuotas"]] == [333.33, 333.33, 333.34]
    assert round(sum(c["monto"] for c in detalle["cuotas"]), 2) == 1000.0

    r = client.post(
        "/deudas-mensuales/pagar-lote",
        json={
            "cuota_ids": [c["id"] for c in detalle["cuotas"]],
            "cuenta_id": cuenta["id"],
            "fecha": _fecha_api(date.today()),
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    assert len(r.json()) == 3

    final = _detalle(client, headers, deuda["id"])
    assert all(c["estado"] == "pagada" for c in final["cuotas"])
    assert final["pendiente"] == 0.0
    assert final["pagado"] == 1000.0
    assert _saldo(client, headers, cuenta["id"]) == -1000.0


def test_pago_de_varias_atrasadas_crea_registros_independientes(
    client, auth_headers, crear_cuenta, crear_deuda_mensual
):
    headers = auth_headers("mensual_lote")
    cuenta = crear_cuenta(headers)
    deuda = crear_deuda_mensual(
        headers,
        modalidad="cuotas",
        monto_cuota=None,
        monto_total=300.0,
        cuotas_totales=3,
        fecha_inicio=_fecha_api(date.today() - timedelta(days=90)),
        dia_aparicion=1,
        dia_limite=5,
    )
    detalle = _detalle(client, headers, deuda["id"])
    assert all(_fecha(c["fecha_limite"]) < date.today() for c in detalle["cuotas"])

    r = client.post(
        "/deudas-mensuales/pagar-lote",
        json={
            "cuota_ids": [c["id"] for c in detalle["cuotas"]],
            "cuenta_id": cuenta["id"],
            "fecha": _fecha_api(date.today()),
            "descripcion": "Pago atrasado",
        },
        headers=headers,
    )
    assert r.status_code == 201, r.text
    pagos = r.json()

    assert len(pagos) == 3
    assert len({p["id"] for p in pagos}) == 3
    assert len({p["movimiento_id"] for p in pagos}) == 3
    assert all(p["monto"] == 100.0 for p in pagos)
    assert all(p["descripcion"] == "Pago atrasado" for p in pagos)
    assert _saldo(client, headers, cuenta["id"]) == -300.0

    actualizada = _detalle(client, headers, deuda["id"])
    assert all(c["estado"] == "pagada" for c in actualizada["cuotas"])
    assert all(c["estado_pago"] == "atrasada" for c in actualizada["cuotas"])


def test_cancelar_conserva_pagadas_y_cancela_futuras(
    client, auth_headers, crear_cuenta, crear_deuda_mensual
):
    headers = auth_headers("mensual_cancelar")
    cuenta = crear_cuenta(headers)
    hoy = date.today()
    deuda = crear_deuda_mensual(
        headers,
        modalidad="cuotas",
        monto_cuota=None,
        monto_total=400.0,
        cuotas_totales=4,
        dia_aparicion=min(hoy.day, 28),
        dia_limite=min(hoy.day, 28),
    )
    cuota_pagada = _cuota(_detalle(client, headers, deuda["id"]))
    pago = _pagar_cuota(client, headers, cuota_pagada["id"], cuenta["id"])

    r = client.post(
        f"/deudas-mensuales/{deuda['id']}/cancelar", headers=headers
    )
    assert r.status_code == 200, r.text
    assert r.json()["estado"] == "cancelada"
    assert r.json()["fecha_cancelacion"] == date.today().isoformat()

    detalle = _detalle(client, headers, deuda["id"])
    primera = _cuota(detalle, 1)
    assert primera["estado"] == "pagada"
    assert len(primera["pagos"]) == 1
    assert all(c["estado"] == "cancelada" for c in detalle["cuotas"][1:])
    assert (
        client.get(
            f"/movimientos/{pago['movimiento_id']}", headers=headers
        ).status_code
        == 200
    )


def test_editar_solo_afecta_cuotas_futuras(
    client, auth_headers, crear_cuenta, crear_deuda_mensual
):
    headers = auth_headers("mensual_editar")
    cuenta = crear_cuenta(headers)
    hoy = date.today()
    deuda = crear_deuda_mensual(
        headers,
        monto_cuota=1000.0,
        dia_aparicion=min(hoy.day, 28),
        dia_limite=min(hoy.day, 28),
    )
    cuota_pagada = _cuota(_detalle(client, headers, deuda["id"]))
    _pagar_cuota(client, headers, cuota_pagada["id"], cuenta["id"])

    r = client.put(
        f"/deudas-mensuales/{deuda['id']}",
        json={"monto_cuota": 2000.0},
        headers=headers,
    )
    assert r.status_code == 200, r.text

    detalle = _detalle(client, headers, deuda["id"])
    assert _cuota(detalle, 1)["monto"] == 1000.0
    assert _cuota(detalle, 1)["estado"] == "pagada"
    assert _cuota(detalle, 2)["monto"] == 2000.0
    assert _cuota(detalle, 2)["estado"] == "pendiente"


def test_eliminar_revierte_movimientos(
    client, auth_headers, crear_cuenta, crear_deuda_mensual
):
    headers = auth_headers("mensual_eliminar")
    cuenta = crear_cuenta(headers)
    deuda = crear_deuda_mensual(
        headers,
        modalidad="cuotas",
        monto_cuota=None,
        monto_total=600.0,
        cuotas_totales=2,
    )
    cuota = _cuota(_detalle(client, headers, deuda["id"]))
    pago = _pagar_cuota(client, headers, cuota["id"], cuenta["id"])
    assert _saldo(client, headers, cuenta["id"]) == -300.0

    r = client.delete(f"/deudas-mensuales/{deuda['id']}", headers=headers)
    assert r.status_code == 200, r.text

    assert client.get("/deudas-mensuales/", headers=headers).json() == []
    assert (
        client.get(
            f"/deudas-mensuales/{deuda['id']}", headers=headers
        ).status_code
        == 404
    )
    assert _saldo(client, headers, cuenta["id"]) == 0.0
    assert client.get("/movimientos/", headers=headers).json()["total"] == 0
    assert (
        client.get(
            f"/movimientos/{pago['movimiento_id']}", headers=headers
        ).status_code
        == 404
    )


def test_integracion_con_entidad_y_resumen(
    client, auth_headers, crear_cuenta, crear_entidad, crear_deuda_mensual
):
    headers = auth_headers("mensual_entidad")
    cuenta = crear_cuenta(headers)
    entidad = crear_entidad(headers, nombre="Inmobiliaria")
    deuda = crear_deuda_mensual(
        headers,
        modalidad="cuotas",
        monto_cuota=None,
        monto_total=600.0,
        cuotas_totales=2,
        entidad_id=entidad["id"],
        descripcion="Alquiler",
    )
    cuota = _cuota(_detalle(client, headers, deuda["id"]))
    _pagar_cuota(client, headers, cuota["id"], cuenta["id"])

    detalle_entidad = client.get(
        f"/entidades/{entidad['id']}", headers=headers
    ).json()
    assert len(detalle_entidad["deudas_mensuales"]) == 1
    mensual = detalle_entidad["deudas_mensuales"][0]
    assert mensual["id"] == deuda["id"]
    assert mensual["pendiente"] == 300.0
    assert mensual["pagado"] == 300.0
    assert detalle_entidad["deudas_pendientes"] == 1
    assert detalle_entidad["saldos"][0]["en_contra"] == 300.0

    listado = client.get("/entidades/", headers=headers).json()
    assert listado[0]["deudas_pendientes"] == 1
    assert listado[0]["saldos"][0]["en_contra"] == 300.0

    resumen = client.get("/deudas-mensuales/resumen", headers=headers).json()
    assert resumen["compromiso_mensual"] == 300.0
    assert resumen["pendiente_total"] == 300.0
    assert resumen["pagado_mes"] == 300.0
    assert resumen["cuotas_mes"] == 1


def test_aislamiento_entre_usuarios(
    client,
    auth_headers,
    crear_cuenta,
    crear_entidad,
    crear_deuda_mensual,
    obtener_moneda,
    obtener_tipo_deudas,
):
    headers_a = auth_headers("mensual_aislamiento_a")
    entidad_a = crear_entidad(headers_a, nombre="Entidad A")
    deuda_a = crear_deuda_mensual(
        headers_a,
        entidad_id=entidad_a["id"],
        monto_cuota=500.0,
    )
    cuota_a = _cuota(_detalle(client, headers_a, deuda_a["id"]))

    headers_b = auth_headers("mensual_aislamiento_b")
    cuenta_b = crear_cuenta(headers_b)

    assert client.get("/deudas-mensuales/", headers=headers_b).json() == []
    assert (
        client.get(
            f"/deudas-mensuales/{deuda_a['id']}", headers=headers_b
        ).status_code
        == 404
    )
    assert (
        client.put(
            f"/deudas-mensuales/{deuda_a['id']}",
            json={"descripcion": "Hack"},
            headers=headers_b,
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/deudas-mensuales/{deuda_a['id']}/cancelar",
            headers=headers_b,
        ).status_code
        == 404
    )
    assert (
        client.delete(
            f"/deudas-mensuales/{deuda_a['id']}", headers=headers_b
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/deudas-mensuales/cuotas/{cuota_a['id']}/pagar",
            json={"cuenta_id": cuenta_b["id"]},
            headers=headers_b,
        ).status_code
        == 404
    )

    r = client.post(
        "/deudas-mensuales/",
        json={
            "modalidad": "recurrente",
            "tipo_id": obtener_tipo_deudas(headers_b),
            "moneda_id": obtener_moneda(headers_b),
            "dia_aparicion": 1,
            "dia_limite": 5,
            "monto_cuota": 100.0,
            "entidad_id": entidad_a["id"],
        },
        headers=headers_b,
    )
    assert r.status_code == 404

    assert client.get("/deudas-mensuales/proximas", headers=headers_b).json() == []
    resumen = client.get("/deudas-mensuales/resumen", headers=headers_b).json()
    assert resumen["pendiente_total"] == 0.0
    assert resumen["cuotas_mes"] == 0


def test_proximas_ordena_vencidas_primero(
    client, auth_headers, crear_deuda_mensual
):
    headers = auth_headers("mensual_proximas")
    hoy = date.today()
    futura = hoy + timedelta(days=3)
    vencida = crear_deuda_mensual(
        headers,
        modalidad="cuotas",
        monto_total=100.0,
        cuotas_totales=1,
        fecha_inicio=_fecha_api(hoy - timedelta(days=60)),
        dia_aparicion=1,
        dia_limite=5,
    )
    proxima = crear_deuda_mensual(
        headers,
        modalidad="cuotas",
        monto_total=200.0,
        cuotas_totales=1,
        fecha_inicio=_fecha_api(futura),
        dia_aparicion=futura.day,
        dia_limite=futura.day,
    )

    items = client.get(
        "/deudas-mensuales/proximas",
        params={"dias": 7},
        headers=headers,
    ).json()

    assert [item["deuda_mensual_id"] for item in items] == [
        vencida["id"],
        proxima["id"],
    ]
    assert items[0]["vencida"] is True
    assert items[1]["vencida"] is False
    assert items[1]["dias_restantes"] == 3
