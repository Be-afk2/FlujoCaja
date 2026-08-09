def test_crear_movimiento_ingreso_infiere_es_ingreso(client, auth_headers, crear_cuenta, crear_movimiento):
    headers = auth_headers("mov1")
    cuenta = crear_cuenta(headers)
    mov = crear_movimiento(headers, cuenta["id"], monto=1000.0)

    assert mov["es_ingreso"] is True
    assert mov["monto"] == 1000.0


def test_crear_movimiento_gasto_infiere_es_ingreso(client, auth_headers, crear_cuenta, crear_movimiento):
    headers = auth_headers("mov2")
    cuenta = crear_cuenta(headers)
    mov = crear_movimiento(headers, cuenta["id"], monto=-200.0)

    assert mov["es_ingreso"] is False
    assert mov["monto"] == -200.0


def test_saldo_actualizado_al_crear_movimientos(client, auth_headers, crear_cuenta, crear_movimiento):
    headers = auth_headers("mov3")
    cuenta = crear_cuenta(headers)

    crear_movimiento(headers, cuenta["id"], monto=1000.0)
    crear_movimiento(headers, cuenta["id"], monto=-200.0)

    r = client.get("/cuentas/", headers=headers)
    saldo = next(c["saldo"] for c in r.json() if c["id"] == cuenta["id"])
    assert saldo == 800.0


def test_saldo_actualizado_al_editar_movimiento(client, auth_headers, crear_cuenta, crear_movimiento):
    headers = auth_headers("mov4")
    cuenta = crear_cuenta(headers)
    mov = crear_movimiento(headers, cuenta["id"], monto=1000.0)

    r = client.put(f"/movimientos/{mov['id']}", json={"monto": 1500.0}, headers=headers)
    assert r.status_code == 200

    cuentas = client.get("/cuentas/", headers=headers).json()
    saldo = next(c["saldo"] for c in cuentas if c["id"] == cuenta["id"])
    assert saldo == 1500.0


def test_saldo_actualizado_al_editar_cambiando_cuenta(client, auth_headers, crear_cuenta, crear_movimiento):
    headers = auth_headers("mov5")
    cuenta_a = crear_cuenta(headers, nombre="A")
    cuenta_b = crear_cuenta(headers, nombre="B")
    mov = crear_movimiento(headers, cuenta_a["id"], monto=1000.0)

    r = client.put(f"/movimientos/{mov['id']}", json={"cuenta_id": cuenta_b["id"]}, headers=headers)
    assert r.status_code == 200

    cuentas = client.get("/cuentas/", headers=headers).json()
    saldo_a = next(c["saldo"] for c in cuentas if c["id"] == cuenta_a["id"])
    saldo_b = next(c["saldo"] for c in cuentas if c["id"] == cuenta_b["id"])
    assert saldo_a == 0.0
    assert saldo_b == 1000.0


def test_saldo_revertido_al_eliminar_movimiento(client, auth_headers, crear_cuenta, crear_movimiento):
    headers = auth_headers("mov6")
    cuenta = crear_cuenta(headers)
    mov = crear_movimiento(headers, cuenta["id"], monto=500.0)

    r = client.delete(f"/movimientos/{mov['id']}", headers=headers)
    assert r.status_code == 200

    cuentas = client.get("/cuentas/", headers=headers).json()
    saldo = next(c["saldo"] for c in cuentas if c["id"] == cuenta["id"])
    assert saldo == 0.0


def test_filtro_por_rango_de_fechas(client, auth_headers, crear_cuenta, crear_movimiento):
    headers = auth_headers("mov7")
    cuenta = crear_cuenta(headers)
    crear_movimiento(headers, cuenta["id"], monto=100.0, fecha="01-01-2026")
    crear_movimiento(headers, cuenta["id"], monto=-50.0, fecha="15-01-2026")
    crear_movimiento(headers, cuenta["id"], monto=200.0, fecha="01-02-2026")

    r = client.get("/movimientos/", params={"fecha_desde": "16-01-2026"}, headers=headers)
    assert r.status_code == 200
    assert r.json()["total"] == 1
    assert r.json()["data"][0]["monto"] == 200.0

    r = client.get(
        "/movimientos/",
        params={"fecha_desde": "10-01-2026", "fecha_hasta": "20-01-2026"},
        headers=headers,
    )
    assert r.json()["total"] == 1
    assert r.json()["data"][0]["monto"] == -50.0


def test_filtro_por_es_ingreso(client, auth_headers, crear_cuenta, crear_movimiento):
    headers = auth_headers("mov8")
    cuenta = crear_cuenta(headers)
    crear_movimiento(headers, cuenta["id"], monto=100.0)
    crear_movimiento(headers, cuenta["id"], monto=-50.0)

    r = client.get("/movimientos/", params={"es_ingreso": "true"}, headers=headers)
    assert r.json()["total"] == 1
    assert r.json()["data"][0]["monto"] == 100.0

    r = client.get("/movimientos/", params={"es_ingreso": "false"}, headers=headers)
    assert r.json()["total"] == 1
    assert r.json()["data"][0]["monto"] == -50.0


def test_filtro_por_cuenta(client, auth_headers, crear_cuenta, crear_movimiento):
    headers = auth_headers("mov9")
    cuenta_a = crear_cuenta(headers, nombre="A")
    cuenta_b = crear_cuenta(headers, nombre="B")
    crear_movimiento(headers, cuenta_a["id"], monto=100.0)
    crear_movimiento(headers, cuenta_b["id"], monto=200.0)

    r = client.get("/movimientos/", params={"cuenta_id": cuenta_a["id"]}, headers=headers)
    assert r.json()["total"] == 1
    assert r.json()["data"][0]["monto"] == 100.0


def test_filtro_por_tipo(client, auth_headers, crear_cuenta, crear_tipo):
    headers = auth_headers("mov10")
    cuenta = crear_cuenta(headers)
    tipo_a = crear_tipo(headers, nombre="Tipo A")
    tipo_b = crear_tipo(headers, nombre="Tipo B")

    client.post(
        "/movimientos/",
        json={"monto": 100.0, "tipo_id": tipo_a["id"], "cuenta_id": cuenta["id"]},
        headers=headers,
    )
    client.post(
        "/movimientos/",
        json={"monto": 200.0, "tipo_id": tipo_b["id"], "cuenta_id": cuenta["id"]},
        headers=headers,
    )

    r = client.get("/movimientos/", params={"tipo_id": tipo_a["id"]}, headers=headers)
    assert r.json()["total"] == 1
    assert r.json()["data"][0]["monto"] == 100.0


def test_paginacion(client, auth_headers, crear_cuenta, crear_movimiento):
    headers = auth_headers("mov11")
    cuenta = crear_cuenta(headers)
    for i in range(5):
        crear_movimiento(headers, cuenta["id"], monto=float(i + 1), fecha=f"0{i + 1}-02-2026")

    r = client.get("/movimientos/", params={"pagina": 1, "cantidad": 2}, headers=headers)
    assert r.status_code == 200
    assert len(r.json()["data"]) == 2
    assert r.json()["total"] == 5
    assert r.json()["pagina"] == 1
