from datetime import date


def _hoy_api() -> str:
    return date.today().strftime("%d-%m-%Y")


def _sumar(resumenes, campo):
    return sum(r[campo] for r in resumenes)


def _crear_datos_reporte(
    client, headers, crear_cuenta, crear_tipo, crear_movimiento, crear_entidad, crear_deuda, obtener_moneda
):
    moneda_id = obtener_moneda(headers)
    cuenta = crear_cuenta(headers)
    tipo = crear_tipo(headers, nombre="Reporte")
    fecha = _hoy_api()

    crear_movimiento(headers, cuenta["id"], 1000.0, tipo_id=tipo["id"], fecha=fecha)
    crear_movimiento(headers, cuenta["id"], -200.0, tipo_id=tipo["id"], fecha=fecha)

    entidad = crear_entidad(headers)
    deuda_ingreso = crear_deuda(
        headers,
        entidad["id"],
        monto=500.0,
        direccion="pagar",
        moneda_id=moneda_id,
        cuenta_inicial_id=cuenta["id"],
        fecha=fecha,
    )
    deuda_gasto = crear_deuda(
        headers,
        entidad["id"],
        monto=300.0,
        direccion="cobrar",
        moneda_id=moneda_id,
        cuenta_inicial_id=cuenta["id"],
        fecha=fecha,
    )
    return moneda_id, deuda_ingreso, deuda_gasto


def test_resumen_mensual_incluir_deudas_false_resta_desglose(
    client,
    auth_headers,
    crear_cuenta,
    crear_tipo,
    crear_movimiento,
    crear_entidad,
    crear_deuda,
    obtener_moneda,
):
    headers = auth_headers("reporte1")
    moneda_id, _, _ = _crear_datos_reporte(
        client,
        headers,
        crear_cuenta,
        crear_tipo,
        crear_movimiento,
        crear_entidad,
        crear_deuda,
        obtener_moneda,
    )
    hoy = date.today()
    params = {"anio": hoy.year, "mes": hoy.month, "moneda_id": moneda_id}

    con_deudas = client.get("/resumen/mensual", params=params, headers=headers).json()
    assert _sumar(con_deudas, "total_ingresos") == 1500.0
    assert _sumar(con_deudas, "total_gastos") == 500.0
    assert _sumar(con_deudas, "neto") == 1000.0
    assert _sumar(con_deudas, "total_ingresos_deuda") == 500.0
    assert _sumar(con_deudas, "total_gastos_deuda") == 300.0

    sin_deudas = client.get(
        "/resumen/mensual",
        params={**params, "incluir_deudas": "false"},
        headers=headers,
    ).json()
    assert _sumar(sin_deudas, "total_ingresos") == 1000.0
    assert _sumar(sin_deudas, "total_gastos") == 200.0
    assert _sumar(sin_deudas, "neto") == 800.0
    assert _sumar(sin_deudas, "total_ingresos_deuda") == 500.0
    assert _sumar(sin_deudas, "total_gastos_deuda") == 300.0


def test_resumen_anual_y_rango_incluir_deudas_false(
    client,
    auth_headers,
    crear_cuenta,
    crear_tipo,
    crear_movimiento,
    crear_entidad,
    crear_deuda,
    obtener_moneda,
):
    headers = auth_headers("reporte2")
    moneda_id, _, _ = _crear_datos_reporte(
        client,
        headers,
        crear_cuenta,
        crear_tipo,
        crear_movimiento,
        crear_entidad,
        crear_deuda,
        obtener_moneda,
    )
    hoy = date.today()

    anual = client.get(
        "/resumen/anual",
        params={
            "anio": hoy.year,
            "moneda_id": moneda_id,
            "incluir_deudas": "false",
        },
        headers=headers,
    ).json()
    assert _sumar(anual, "total_ingresos") == 1000.0
    assert _sumar(anual, "total_gastos") == 200.0

    periodo = f"{hoy.year}-{hoy.month:02d}"
    rango = client.get(
        "/resumen/rango",
        params={
            "desde": periodo,
            "hasta": periodo,
            "moneda_id": moneda_id,
            "incluir_deudas": "false",
        },
        headers=headers,
    ).json()
    assert _sumar(rango, "total_ingresos") == 1000.0
    assert _sumar(rango, "total_gastos") == 200.0


def test_filtro_movimientos_por_es_deuda(
    client,
    auth_headers,
    crear_cuenta,
    crear_tipo,
    crear_movimiento,
    crear_entidad,
    crear_deuda,
    obtener_moneda,
):
    headers = auth_headers("reporte3")
    _crear_datos_reporte(
        client,
        headers,
        crear_cuenta,
        crear_tipo,
        crear_movimiento,
        crear_entidad,
        crear_deuda,
        obtener_moneda,
    )

    solo_deuda = client.get(
        "/movimientos/", params={"es_deuda": "true"}, headers=headers
    ).json()
    assert solo_deuda["total"] == 2
    assert all(m["es_deuda"] is True for m in solo_deuda["data"])

    sin_deuda = client.get(
        "/movimientos/", params={"es_deuda": "false"}, headers=headers
    ).json()
    assert sin_deuda["total"] == 2
    assert all(m["es_deuda"] is False for m in sin_deuda["data"])


def test_movimiento_de_deuda_no_se_edita_ni_elimina_desde_movimientos(
    client,
    auth_headers,
    crear_cuenta,
    crear_tipo,
    crear_movimiento,
    crear_entidad,
    crear_deuda,
    obtener_moneda,
):
    headers = auth_headers("reporte4")
    moneda_id, deuda_ingreso, _ = _crear_datos_reporte(
        client,
        headers,
        crear_cuenta,
        crear_tipo,
        crear_movimiento,
        crear_entidad,
        crear_deuda,
        obtener_moneda,
    )
    assert moneda_id > 0
    mov_id = deuda_ingreso["movimiento_inicial_id"]
    assert mov_id is not None

    r = client.put(f"/movimientos/{mov_id}", json={"monto": 1.0}, headers=headers)
    assert r.status_code == 400
    assert "deuda" in r.json()["error"].lower()

    r = client.delete(f"/movimientos/{mov_id}", headers=headers)
    assert r.status_code == 400
    assert "deuda" in r.json()["error"].lower()

    mov = client.get(f"/movimientos/{mov_id}", headers=headers)
    assert mov.status_code == 200
    assert mov.json()["es_deuda"] is True
