def test_catalogos_tipos_cuenta_y_monedas(client, auth_headers):
    headers = auth_headers("cuenta1")
    r = client.get("/cuentas/tipos-cuenta", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) >= 1

    r = client.get("/monedas/", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) >= 1


def test_crear_cuenta_con_saldo_cero(client, auth_headers, crear_cuenta):
    headers = auth_headers("cuenta2")
    cuenta = crear_cuenta(headers, nombre="Efectivo")
    assert cuenta["id"] > 0
    assert cuenta["saldo"] == 0.0
    assert cuenta["nombre"] == "Efectivo"


def test_listar_cuentas_del_usuario(client, auth_headers, crear_cuenta):
    headers = auth_headers("cuenta3")
    crear_cuenta(headers, nombre="Ahorro")
    crear_cuenta(headers, nombre="Corriente")

    r = client.get("/cuentas/", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 2
