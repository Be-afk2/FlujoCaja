def test_usuario_b_no_ve_datos_de_usuario_a(client, auth_headers, crear_cuenta, crear_movimiento):
    headers_a = auth_headers("userA")
    cuenta_a = crear_cuenta(headers_a, nombre="Cuenta A")
    mov_a = crear_movimiento(headers_a, cuenta_a["id"], monto=100.0)

    headers_b = auth_headers("userB")

    r = client.get("/movimientos/", headers=headers_b)
    assert r.json()["total"] == 0

    r = client.get(f"/movimientos/{mov_a['id']}", headers=headers_b)
    assert r.status_code == 404

    r = client.get("/cuentas/", headers=headers_b)
    assert all(c["id"] != cuenta_a["id"] for c in r.json())


def test_usuario_b_no_modifica_datos_de_usuario_a(client, auth_headers, crear_cuenta, crear_movimiento):
    headers_a = auth_headers("userA")
    cuenta_a = crear_cuenta(headers_a, nombre="Cuenta A")
    mov_a = crear_movimiento(headers_a, cuenta_a["id"], monto=100.0)

    headers_b = auth_headers("userB")

    r = client.put(f"/movimientos/{mov_a['id']}", json={"monto": 999.0}, headers=headers_b)
    assert r.status_code == 404

    r = client.delete(f"/movimientos/{mov_a['id']}", headers=headers_b)
    assert r.status_code == 404


def test_usuario_b_no_crea_movimiento_con_cuenta_ajena(client, auth_headers, crear_cuenta, crear_tipo):
    headers_a = auth_headers("userA")
    cuenta_a = crear_cuenta(headers_a, nombre="Cuenta A")

    headers_b = auth_headers("userB")
    tipo_b = crear_tipo(headers_b, nombre="Tipo B")

    r = client.post(
        "/movimientos/",
        json={"monto": 500.0, "tipo_id": tipo_b["id"], "cuenta_id": cuenta_a["id"]},
        headers=headers_b,
    )
    assert r.status_code == 400


def test_token_de_a_queda_invalido_al_loguearse_b(client, auth_headers):
    headers_a = auth_headers("userA")
    assert client.get("/auth", headers=headers_a).status_code == 200

    auth_headers("userB")

    r = client.get("/auth", headers=headers_a)
    assert r.status_code == 401
