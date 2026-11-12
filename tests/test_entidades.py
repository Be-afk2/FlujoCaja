def test_crear_listar_editar_eliminar_entidad(client, auth_headers, crear_entidad):
    headers = auth_headers("entidad1")
    entidad = crear_entidad(headers, nombre="Juan", tipo="persona", descripcion="Amigo")

    assert entidad["id"] > 0
    assert entidad["nombre"] == "Juan"
    assert entidad["tipo"] == "persona"
    assert entidad["descripcion"] == "Amigo"

    listado = client.get("/entidades/", headers=headers).json()
    assert len(listado) == 1
    assert listado[0]["id"] == entidad["id"]
    assert listado[0]["saldos"] == []
    assert listado[0]["deudas_pendientes"] == 0
    assert listado[0]["proximo_vencimiento"] is None

    r = client.put(
        f"/entidades/{entidad['id']}",
        json={"nombre": "Juan Perez", "tipo": "empresa"},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    assert r.json()["nombre"] == "Juan Perez"
    assert r.json()["tipo"] == "empresa"

    r = client.delete(f"/entidades/{entidad['id']}", headers=headers)
    assert r.status_code == 200, r.text
    assert client.get("/entidades/", headers=headers).json() == []


def test_crear_entidad_nombre_vacio_retorna_400(client, auth_headers):
    headers = auth_headers("entidad2")
    r = client.post("/entidades/", json={"nombre": "   ", "tipo": "persona"}, headers=headers)
    assert r.status_code == 400
    assert "nombre" in r.json()["error"].lower()


def test_tipo_entidad_invalido_retorna_400(client, auth_headers):
    headers = auth_headers("entidad3")
    r = client.post("/entidades/", json={"nombre": "Robot", "tipo": "robot"}, headers=headers)
    assert r.status_code == 400
    assert "tipo de entidad" in r.json()["error"].lower()


def test_eliminar_entidad_con_deudas_retorna_400(
    client, auth_headers, crear_entidad, crear_deuda
):
    headers = auth_headers("entidad4")
    entidad = crear_entidad(headers, nombre="Con deuda")
    crear_deuda(headers, entidad["id"], monto=500.0)

    r = client.delete(f"/entidades/{entidad['id']}", headers=headers)
    assert r.status_code == 400
    assert "deudas" in r.json()["error"].lower()

    assert len(client.get("/entidades/", headers=headers).json()) == 1


def test_entidad_inexistente_retorna_404(client, auth_headers):
    headers = auth_headers("entidad5")
    assert client.get("/entidades/999", headers=headers).status_code == 404
    assert client.put("/entidades/999", json={"nombre": "X"}, headers=headers).status_code == 404
    assert client.delete("/entidades/999", headers=headers).status_code == 404


def test_listar_entidades_calcula_saldos_y_pendientes(
    client, auth_headers, crear_entidad, crear_deuda, obtener_moneda
):
    headers = auth_headers("entidad6")
    moneda_id = obtener_moneda(headers)
    entidad = crear_entidad(headers, nombre="Mixta")

    crear_deuda(
        headers,
        entidad["id"],
        monto=600.0,
        direccion="cobrar",
        moneda_id=moneda_id,
        vencimiento="31-12-2030",
    )
    crear_deuda(
        headers,
        entidad["id"],
        monto=400.0,
        direccion="pagar",
        moneda_id=moneda_id,
        vencimiento="15-06-2031",
    )

    item = client.get("/entidades/", headers=headers).json()[0]
    assert item["deudas_pendientes"] == 2
    assert item["proximo_vencimiento"] == "2030-12-31"
    assert len(item["saldos"]) == 1

    saldo = item["saldos"][0]
    assert saldo["moneda_id"] == moneda_id
    assert saldo["a_favor"] == 600.0
    assert saldo["en_contra"] == 400.0
    assert saldo["neto"] == 200.0


def test_detalle_entidad_incluye_deudas(client, auth_headers, crear_entidad, crear_deuda):
    headers = auth_headers("entidad7")
    entidad = crear_entidad(headers, nombre="Detalle")
    deuda = crear_deuda(headers, entidad["id"], monto=750.0, descripcion="Prestamo")

    detalle = client.get(f"/entidades/{entidad['id']}", headers=headers).json()
    assert detalle["id"] == entidad["id"]
    assert len(detalle["deudas"]) == 1

    item = detalle["deudas"][0]
    assert item["id"] == deuda["id"]
    assert item["monto_original"] == 750.0
    assert item["pendiente"] == 750.0
    assert item["estado"] == "pendiente"
    assert item["pagos"] == []
