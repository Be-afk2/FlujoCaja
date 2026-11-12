from datetime import date

import pytest


def _hoy_api() -> str:
    return date.today().strftime("%d-%m-%Y")


def _saldo(client, headers, cuenta_id):
    cuentas = client.get("/cuentas/", headers=headers).json()
    return next(c["saldo"] for c in cuentas if c["id"] == cuenta_id)


def _deuda_listada(client, headers, deuda_id):
    deudas = client.get("/deudas/", headers=headers).json()
    return next(d for d in deudas if d["id"] == deuda_id)


def _tipo_y_subtipos_deudas(client, headers):
    tipos = client.get("/tipos/?cantidad=50", headers=headers).json()
    tipo = next(t for t in tipos if t["nombre"] == "Deudas")
    detalle = client.get(
        "/subtipos/", params={"tipo_id": tipo["id"]}, headers=headers
    ).json()
    return tipo["id"], {s["id"]: s["nombre"] for s in detalle["subtipos"]}


def test_deuda_sin_cuenta_no_mueve_saldo(client, auth_headers, crear_cuenta, crear_entidad, crear_deuda):
    headers = auth_headers("deuda1")
    cuenta = crear_cuenta(headers)
    entidad = crear_entidad(headers)
    deuda = crear_deuda(headers, entidad["id"], monto=1000.0)

    assert deuda["movimiento_inicial_id"] is None
    assert _saldo(client, headers, cuenta["id"]) == 0.0

    fila = _deuda_listada(client, headers, deuda["id"])
    assert fila["pendiente"] == 1000.0
    assert fila["total_abonos"] == 0.0
    assert fila["estado"] == "pendiente"

    assert client.get("/movimientos/", headers=headers).json()["total"] == 0


@pytest.mark.parametrize(
    "direccion,signo,subtipo_esperado,es_ingreso_deuda",
    [
        ("cobrar", -1, "Préstamo otorgado", False),
        ("pagar", 1, "Préstamo recibido", True),
    ],
)
def test_deuda_con_cuenta_mueve_saldo_y_crea_movimiento(
    client,
    auth_headers,
    crear_cuenta,
    crear_entidad,
    crear_deuda,
    obtener_moneda,
    direccion,
    signo,
    subtipo_esperado,
    es_ingreso_deuda,
):
    headers = auth_headers(f"deuda2_{direccion}")
    moneda_id = obtener_moneda(headers)
    cuenta = crear_cuenta(headers)
    entidad = crear_entidad(headers)
    deuda = crear_deuda(
        headers,
        entidad["id"],
        monto=1000.0,
        direccion=direccion,
        moneda_id=moneda_id,
        cuenta_inicial_id=cuenta["id"],
        fecha=_hoy_api(),
    )

    assert deuda["movimiento_inicial_id"] is not None
    assert _saldo(client, headers, cuenta["id"]) == signo * 1000.0

    tipo_id, subtipos = _tipo_y_subtipos_deudas(client, headers)
    mov = client.get(
        f"/movimientos/{deuda['movimiento_inicial_id']}", headers=headers
    ).json()
    assert mov["es_deuda"] is True
    assert mov["monto"] == signo * 1000.0
    assert mov["tipo_id"] == tipo_id
    assert subtipos[mov["subtipo_id"]] == subtipo_esperado

    hoy = date.today()
    resumen = client.get(
        "/resumen/mensual",
        params={"anio": hoy.year, "mes": hoy.month, "moneda_id": moneda_id},
        headers=headers,
    ).json()
    total_ingresos = sum(r["total_ingresos"] for r in resumen)
    total_gastos = sum(r["total_gastos"] for r in resumen)
    total_ingresos_deuda = sum(r["total_ingresos_deuda"] for r in resumen)
    total_gastos_deuda = sum(r["total_gastos_deuda"] for r in resumen)
    if es_ingreso_deuda:
        assert total_ingresos == 1000.0
        assert total_ingresos_deuda == 1000.0
        assert total_gastos == 0.0
        assert total_gastos_deuda == 0.0
    else:
        assert total_ingresos == 0.0
        assert total_ingresos_deuda == 0.0
        assert total_gastos == 1000.0
        assert total_gastos_deuda == 1000.0


def test_abono_parcial_reduce_pendiente_y_saldo(
    client, auth_headers, crear_cuenta, crear_entidad, crear_deuda, crear_pago
):
    headers = auth_headers("deuda3")
    cuenta = crear_cuenta(headers)
    entidad = crear_entidad(headers)
    deuda = crear_deuda(headers, entidad["id"], monto=1000.0, fecha=_hoy_api())

    pago = crear_pago(headers, deuda["id"], cuenta["id"], 300.0)
    assert pago["moneda_distinta"] is False
    assert _saldo(client, headers, cuenta["id"]) == 300.0

    fila = _deuda_listada(client, headers, deuda["id"])
    assert fila["pendiente"] == 700.0
    assert fila["total_abonos"] == 300.0
    assert fila["estado"] == "pendiente"

    _, subtipos = _tipo_y_subtipos_deudas(client, headers)
    mov = client.get(f"/movimientos/{pago['movimiento_id']}", headers=headers).json()
    assert mov["es_deuda"] is True
    assert mov["monto"] == 300.0
    assert subtipos[mov["subtipo_id"]] == "Abono deuda"


@pytest.mark.parametrize(
    "direccion,subtipo_final,signo",
    [("cobrar", "Cobro deuda", 1), ("pagar", "Pago deuda", -1)],
)
def test_pago_final_marca_pagada_y_subtipo(
    client,
    auth_headers,
    crear_cuenta,
    crear_entidad,
    crear_deuda,
    crear_pago,
    direccion,
    subtipo_final,
    signo,
):
    headers = auth_headers(f"deuda4_{direccion}")
    cuenta = crear_cuenta(headers)
    entidad = crear_entidad(headers)
    deuda = crear_deuda(
        headers, entidad["id"], monto=1000.0, direccion=direccion, fecha=_hoy_api()
    )

    crear_pago(headers, deuda["id"], cuenta["id"], 300.0)
    final = crear_pago(headers, deuda["id"], cuenta["id"], 700.0)

    fila = _deuda_listada(client, headers, deuda["id"])
    assert fila["estado"] == "pagada"
    assert fila["pendiente"] == 0.0
    assert fila["total_abonos"] == 1000.0
    assert _saldo(client, headers, cuenta["id"]) == signo * 1000.0

    _, subtipos = _tipo_y_subtipos_deudas(client, headers)
    mov = client.get(f"/movimientos/{final['movimiento_id']}", headers=headers).json()
    assert subtipos[mov["subtipo_id"]] == subtipo_final
    assert mov["monto"] == signo * 700.0


def test_sobrepago_retorna_400(
    client, auth_headers, crear_cuenta, crear_entidad, crear_deuda
):
    headers = auth_headers("deuda5")
    cuenta = crear_cuenta(headers)
    entidad = crear_entidad(headers)
    deuda = crear_deuda(headers, entidad["id"], monto=1000.0)

    r = client.post(
        f"/deudas/{deuda['id']}/pagos",
        json={"monto": 1100.0, "cuenta_id": cuenta["id"]},
        headers=headers,
    )
    assert r.status_code == 400
    assert "superar" in r.json()["error"].lower()

    assert _deuda_listada(client, headers, deuda["id"])["pendiente"] == 1000.0
    assert _saldo(client, headers, cuenta["id"]) == 0.0


def test_pago_con_cuenta_de_otro_usuario_retorna_400(
    client, auth_headers, crear_cuenta, crear_entidad, crear_deuda
):
    headers_otros = auth_headers("deuda6_otros")
    cuenta_ajena = crear_cuenta(headers_otros, nombre="Ajena")

    headers = auth_headers("deuda6")
    entidad = crear_entidad(headers)
    deuda = crear_deuda(headers, entidad["id"], monto=1000.0)

    r = client.post(
        f"/deudas/{deuda['id']}/pagos",
        json={"monto": 100.0, "cuenta_id": cuenta_ajena["id"]},
        headers=headers,
    )
    assert r.status_code == 400
    assert "pertenece" in r.json()["error"].lower()


def test_editar_pago_recalcula_saldo_y_pendiente(
    client, auth_headers, crear_cuenta, crear_entidad, crear_deuda, crear_pago
):
    headers = auth_headers("deuda7")
    cuenta = crear_cuenta(headers)
    entidad = crear_entidad(headers)
    deuda = crear_deuda(headers, entidad["id"], monto=1000.0, fecha=_hoy_api())
    pago = crear_pago(headers, deuda["id"], cuenta["id"], 200.0)
    assert _saldo(client, headers, cuenta["id"]) == 200.0

    r = client.put(
        f"/deudas/{deuda['id']}/pagos/{pago['id']}",
        json={"monto": 500.0},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["monto"] == 500.0

    assert _saldo(client, headers, cuenta["id"]) == 500.0
    assert _deuda_listada(client, headers, deuda["id"])["pendiente"] == 500.0


def test_eliminar_pago_revierte_saldo_y_pendiente(
    client, auth_headers, crear_cuenta, crear_entidad, crear_deuda, crear_pago
):
    headers = auth_headers("deuda8")
    cuenta = crear_cuenta(headers)
    entidad = crear_entidad(headers)
    deuda = crear_deuda(headers, entidad["id"], monto=1000.0, fecha=_hoy_api())
    pago = crear_pago(headers, deuda["id"], cuenta["id"], 300.0)

    r = client.delete(
        f"/deudas/{deuda['id']}/pagos/{pago['id']}", headers=headers
    )
    assert r.status_code == 200, r.text

    assert _saldo(client, headers, cuenta["id"]) == 0.0
    assert _deuda_listada(client, headers, deuda["id"])["pendiente"] == 1000.0
    assert (
        client.get(f"/movimientos/{pago['movimiento_id']}", headers=headers).status_code
        == 404
    )


def test_eliminar_deuda_revierte_todos_los_movimientos(
    client, auth_headers, crear_cuenta, crear_entidad, crear_deuda, crear_pago
):
    headers = auth_headers("deuda9")
    cuenta = crear_cuenta(headers)
    entidad = crear_entidad(headers)
    deuda = crear_deuda(
        headers,
        entidad["id"],
        monto=1000.0,
        direccion="pagar",
        cuenta_inicial_id=cuenta["id"],
        fecha=_hoy_api(),
    )
    pago = crear_pago(headers, deuda["id"], cuenta["id"], 400.0)
    assert _saldo(client, headers, cuenta["id"]) == 600.0

    r = client.delete(f"/deudas/{deuda['id']}", headers=headers)
    assert r.status_code == 200, r.text

    assert _saldo(client, headers, cuenta["id"]) == 0.0
    assert client.get("/deudas/", headers=headers).json() == []
    assert (
        client.get(
            f"/movimientos/{deuda['movimiento_inicial_id']}", headers=headers
        ).status_code
        == 404
    )
    assert (
        client.get(f"/movimientos/{pago['movimiento_id']}", headers=headers).status_code
        == 404
    )

    detalle = client.get(f"/entidades/{entidad['id']}", headers=headers).json()
    assert detalle["deudas"] == []


def test_deuda_vencida_por_fecha(
    client, auth_headers, crear_entidad, crear_deuda
):
    headers = auth_headers("deuda10")
    entidad = crear_entidad(headers)
    deuda = crear_deuda(
        headers, entidad["id"], monto=500.0, vencimiento="01-01-2020"
    )

    fila = _deuda_listada(client, headers, deuda["id"])
    assert fila["estado"] == "vencida"
    assert fila["pendiente"] == 500.0


def test_moneda_distinta_no_convierte_montos(
    client, auth_headers, crear_cuenta, crear_entidad, crear_deuda, crear_pago
):
    headers = auth_headers("deuda11")
    monedas = client.get("/monedas/", headers=headers).json()
    assert len(monedas) >= 2
    moneda_deuda = monedas[0]["id"]
    moneda_cuenta = monedas[1]["id"]

    cuenta = crear_cuenta(headers, nombre="Otra moneda", moneda=moneda_cuenta)
    entidad = crear_entidad(headers)
    deuda = crear_deuda(
        headers,
        entidad["id"],
        monto=1000.0,
        moneda_id=moneda_deuda,
        fecha=_hoy_api(),
    )

    pago = crear_pago(headers, deuda["id"], cuenta["id"], 400.0)
    assert pago["moneda_distinta"] is True

    assert _saldo(client, headers, cuenta["id"]) == 400.0
    assert _deuda_listada(client, headers, deuda["id"])["pendiente"] == 600.0

    hoy = date.today()
    resumen_cuenta = client.get(
        "/resumen/mensual",
        params={"anio": hoy.year, "mes": hoy.month, "moneda_id": moneda_cuenta},
        headers=headers,
    ).json()
    assert sum(r["total_ingresos"] for r in resumen_cuenta) == 400.0
    assert sum(r["total_ingresos_deuda"] for r in resumen_cuenta) == 400.0

    resumen_deuda = client.get(
        "/resumen/mensual",
        params={"anio": hoy.year, "mes": hoy.month, "moneda_id": moneda_deuda},
        headers=headers,
    ).json()
    assert resumen_deuda == []


def test_editar_deuda_con_abonos_bloquea_montos(
    client,
    auth_headers,
    crear_cuenta,
    crear_entidad,
    crear_deuda,
    crear_pago,
    obtener_moneda,
):
    headers = auth_headers("deuda12")
    cuenta = crear_cuenta(headers)
    entidad = crear_entidad(headers)
    deuda = crear_deuda(headers, entidad["id"], monto=1000.0, fecha=_hoy_api())
    crear_pago(headers, deuda["id"], cuenta["id"], 100.0)

    r = client.put(
        f"/deudas/{deuda['id']}", json={"monto_original": 2000.0}, headers=headers
    )
    assert r.status_code == 400

    r = client.put(
        f"/deudas/{deuda['id']}", json={"direccion": "pagar"}, headers=headers
    )
    assert r.status_code == 400

    r = client.put(
        f"/deudas/{deuda['id']}",
        json={"moneda_id": obtener_moneda(headers, 2)},
        headers=headers,
    )
    assert r.status_code == 400

    r = client.put(
        f"/deudas/{deuda['id']}", json={"descripcion": "Actualizada"}, headers=headers
    )
    assert r.status_code == 200, r.text
    assert r.json()["descripcion"] == "Actualizada"


def test_aislamiento_de_entidades_deudas_y_pagos(
    client,
    auth_headers,
    crear_cuenta,
    crear_entidad,
    crear_deuda,
    crear_pago,
    obtener_moneda,
):
    headers_a = auth_headers("deuda13_a")
    cuenta_a = crear_cuenta(headers_a)
    entidad_a = crear_entidad(headers_a, nombre="Entidad A")
    deuda_a = crear_deuda(headers_a, entidad_a["id"], monto=500.0)
    crear_pago(headers_a, deuda_a["id"], cuenta_a["id"], 100.0)

    headers_b = auth_headers("deuda13_b")
    cuenta_b = crear_cuenta(headers_b)

    assert client.get("/entidades/", headers=headers_b).json() == []
    assert client.get("/deudas/", headers=headers_b).json() == []
    assert client.get(f"/entidades/{entidad_a['id']}", headers=headers_b).status_code == 404
    assert (
        client.put(
            f"/entidades/{entidad_a['id']}",
            json={"nombre": "Hack"},
            headers=headers_b,
        ).status_code
        == 404
    )
    assert (
        client.delete(f"/entidades/{entidad_a['id']}", headers=headers_b).status_code
        == 404
    )
    assert (
        client.put(
            f"/deudas/{deuda_a['id']}",
            json={"descripcion": "Hack"},
            headers=headers_b,
        ).status_code
        == 404
    )
    assert (
        client.delete(f"/deudas/{deuda_a['id']}", headers=headers_b).status_code == 404
    )

    r = client.post(
        "/deudas/",
        json={
            "entidad_id": entidad_a["id"],
            "direccion": "cobrar",
            "monto_original": 100.0,
            "moneda_id": obtener_moneda(headers_b),
        },
        headers=headers_b,
    )
    assert r.status_code == 404

    r = client.post(
        f"/deudas/{deuda_a['id']}/pagos",
        json={"monto": 10.0, "cuenta_id": cuenta_b["id"]},
        headers=headers_b,
    )
    assert r.status_code == 404
