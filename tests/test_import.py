def test_importar_movimientos_validos(client, auth_headers, crear_cuenta, crear_tipo):
    headers = auth_headers("import1")
    cuenta = crear_cuenta(headers)
    tipo = crear_tipo(headers)

    filas = [
        {"monto": 1000.0, "tipo_id": tipo["id"], "cuenta_id": cuenta["id"], "fecha": "01-03-2026"},
        {"monto": -300.0, "tipo_id": tipo["id"], "cuenta_id": cuenta["id"], "fecha": "02-03-2026"},
        {"monto": 200.0, "tipo_id": tipo["id"], "cuenta_id": cuenta["id"], "fecha": "05-03-2026"},
    ]

    r = client.post("/movimientos/importar", json={"filas": filas}, headers=headers)
    assert r.status_code == 200
    assert r.json()["importados"] == 3
    assert r.json()["errores"] == []

    movimientos = client.get("/movimientos/", headers=headers).json()
    assert movimientos["total"] == 3

    cuentas = client.get("/cuentas/", headers=headers).json()
    saldo = next(c["saldo"] for c in cuentas if c["id"] == cuenta["id"])
    assert saldo == 900.0


def test_importar_reporta_errores_por_fila_sin_abortar(client, auth_headers, crear_cuenta, crear_tipo):
    headers = auth_headers("import2")
    cuenta = crear_cuenta(headers)
    tipo = crear_tipo(headers)

    filas = [
        {"monto": 100.0, "tipo_id": tipo["id"], "cuenta_id": cuenta["id"]},
        {"monto": 500.0, "tipo_id": tipo["id"], "cuenta_id": 99999},
        {"monto": 200.0, "tipo_id": tipo["id"], "cuenta_id": cuenta["id"]},
    ]

    r = client.post("/movimientos/importar", json={"filas": filas}, headers=headers)
    assert r.status_code == 200
    assert r.json()["importados"] == 2
    assert len(r.json()["errores"]) == 1
    assert r.json()["errores"][0]["fila"] == 2

    movimientos = client.get("/movimientos/", headers=headers).json()
    assert movimientos["total"] == 2


def test_importar_con_cuenta_ajena(client, auth_headers, crear_cuenta, crear_tipo):
    headers_a = auth_headers("userA")
    cuenta_a = crear_cuenta(headers_a, nombre="Cuenta A")

    headers_b = auth_headers("userB")
    tipo_b = crear_tipo(headers_b, nombre="Tipo B")

    filas = [
        {"monto": 100.0, "tipo_id": tipo_b["id"], "cuenta_id": cuenta_a["id"]},
        {"monto": 50.0, "tipo_id": tipo_b["id"], "cuenta_id": 99999},
    ]

    r = client.post("/movimientos/importar", json={"filas": filas}, headers=headers_b)
    assert r.status_code == 200
    assert r.json()["importados"] == 0
    assert len(r.json()["errores"]) == 2


def test_importar_sin_auth(client):
    r = client.post("/movimientos/importar", json={"filas": []})
    assert r.status_code == 401


def test_importar_filas_vacias(client, auth_headers):
    headers = auth_headers("import3")
    r = client.post("/movimientos/importar", json={"filas": []}, headers=headers)
    assert r.status_code == 200
    assert r.json()["importados"] == 0
    assert r.json()["errores"] == []
