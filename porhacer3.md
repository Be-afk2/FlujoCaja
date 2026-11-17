# FlujoCaja - Roadmap tecnico V3

Tareas derivadas de `planes/idea2.md` (**Deudas mensuales**). Incorpora la
**Fase 10 - Deudas mensuales** y mantiene pendiente la **Fase 7.5 - Inteligencia
financiera basada en datos** de `PorHacerv2.md`.

---

## Fase 10 - Deudas mensuales

Objetivo: registrar compromisos que se repiten cada mes o planes de cuotas,
generar sus cuotas automáticamente, pagarlas desde una cuenta (creando el
movimiento correspondiente) y conservar el historial al cancelar o eliminar.

Alcance funcional:

- Nueva página **"Deudas mensuales"** en el sidebar, enlazada desde Deudas.
- Dos modalidades: **recurrente** y **plan de cuotas**.
- Plantilla con: entidad opcional, categoría/subtipo, moneda, descripción,
  modalidad, monto, N cuotas, día de aparición, día límite, fecha de inicio.
- Generación automática de cuotas mensuales.
- Pago rápido desde el inicio y pago detallado desde la página de deudas mensuales.
- Historial de cuotas y pagos.
- Cancelación con conservación de historial.
- Edición de cuotas futuras.
- Eliminación con advertencia y reversión de movimientos.
- Integración con entidades y resumen de Deudas.

### 10.1 Modelo de datos

- [x] Crear `bd/models/deudaMensual.py` con `DeudaMensual` (plantilla): `id`, `user_id`, `entidad_id` opcional, `tipo_id` obligatorio, `subtipo_id` opcional, `moneda_id`, `descripcion`, `modalidad` (`recurrente | cuotas`), `monto_modo` (`fijo | calculado`), `monto_cuota`, `monto_total` (solo plan), `cuotas_totales` (solo plan), `dia_aparicion` (1-31), `dia_limite` (1-31), `fecha_inicio`, `estado` (`activa | cancelada`), `fecha_cancelacion`, `cuenta_pago_default_id` opcional, `created_at`.
- [x] Crear `CuotaMensual` (ocurrencia): `id`, `user_id`, `deuda_mensual_id`, `numero`, `anio`, `mes`, `fecha_aparicion`, `fecha_limite`, `monto`, `estado` (`pendiente | pagada | cancelada`), `estado_pago` (`antes_de_tiempo | al_dia | atrasada`, solo pagadas).
- [x] Crear `PagoCuotaMensual`: `id`, `user_id`, `cuota_id` único, `monto`, `fecha`, `cuenta_id`, `movimiento_id` único, `descripcion` (`estado_pago` se deriva de la cuota, no se duplica).
- [x] Agregar restricción única por `(deuda_mensual_id, numero)`.
- [x] Agregar relación `deudas_mensuales` en `bd/models/entidad.py`.
- [x] Exportar los nuevos modelos en `bd/models/__init__.py`.

### 10.2 Reglas de negocio

Archivo `bd/domain/deuda_mensual.py`:

- [x] **Fechas:** aparición y límite son días 1-31. Si el mes no tiene el día, se usa el último disponible. Si `dia_limite < dia_aparicion`, el límite cae el mes siguiente.
- [x] **Primera cuota:** mes de `fecha_inicio`, aunque el día de aparición ya haya pasado.
- [x] **Generación:** plan → se generan las N cuotas al crear; recurrente → se generan desde `fecha_inicio` hasta `max(mes actual + 1, mes de inicio + 1)` (permite pagos anticipados y atrasados).
- [x] **Estado de pago:** comparar la fecha de pago con `fecha_aparicion` y `fecha_limite`: antes de aparición → `antes_de_tiempo`; entre aparición y límite → `al_dia`; después del límite → `atrasada`.
- [x] **Prioridad:** vencidas primero, luego próximas, ordenadas por fecha límite.
- [x] **Pago:** completo por cuota, desde una cuenta. Genera movimiento negativo con la categoría elegida, `es_deuda=True`, descuenta saldo y actualiza `ResumenMensual`.
- [x] **Varias atrasadas:** se pueden pagar en lote; cada cuota crea su pago y movimiento independiente.
- [x] **Cancelar:** la plantilla pasa a `cancelada`; las pagadas quedan y muestran "Deuda cancelada"; las futuras impagas pasan a `cancelada` y dejan de sumar.
- [x] **Editar:** solo afecta cuotas futuras impagas; las pagadas no cambian.
- [x] **Eliminar:** permitido con advertencia; borra cuotas, pagos y movimientos, revirtiendo saldos.
- [x] **Eliminar pago individual:** revierte el movimiento y devuelve la cuota a `pendiente`.
- [x] **Categoría:** definida en la plantilla y heredada por todas las cuotas.
- [x] **Moneda distinta:** si la cuenta del pago usa otra moneda, se avisa y no se convierte (misma regla que Deudas).

Decisiones acordadas:

- Ajuste de centavos: la última cuota absorbe la diferencia (`montos_cuotas`).
- `monto_modo`: `fijo` = recurrente, `calculado` = plan; `validar_plantilla` exige la coherencia.
- "Futura" = `fecha_aparicion > hoy` (aplica a editar y cancelar).
- Recurrente con `fecha_inicio` futura: se genera hasta `mes de inicio + 1`.

### 10.3 CRUD

Archivo `bd/crud/deudaMensual.py`:

- [x] Crear/listar/editar/cancelar/eliminar plantillas.
- [x] Generar y sincronizar cuotas.
- [x] Pagar cuota, editar pago, eliminar pago.
- [x] Resumen y próximas.
- [x] Reutilizar `_crear_movimiento_sesion`, `_actualizar_movimiento_sesion`, `_eliminar_movimiento_sesion` y `actualizar_saldo`.

Decisiones acordadas:

- Auto-sync de cuotas en `listar`, `obtener`, `proximas` y `resumen` (idempotente).
- Edición estructural (modalidad, fecha_inicio, cuotas_totales, monto_total) solo sin pagos; el resto actualiza únicamente cuotas futuras impagas.
- Pago en lote todo o nada en una sola transacción.
- `pendiente_total`: recurrentes solo cuotas ya aparecidas; planes todas las impagas.

### 10.4 Integración con entidades

En `bd/crud/entidad.py`:

- [x] Sumar pendientes de mensuales a `saldos` como `en_contra`.
- [x] Incluir la próxima cuota en `proximo_vencimiento`.
- [x] Agregar `deudas_mensuales` al detalle de entidad.
- [x] Para recurrentes, sumar solo cuotas ya aparecidas e impagas.
- [x] Para planes, sumar todas las cuotas impagas (incluidas futuras).

Decisiones acordadas:

- Se incluyen todas las plantillas asociadas (también canceladas); solo se excluyen cuotas canceladas.
- `deudas_pendientes` suma una plantilla con al menos una cuota pendiente computable.
- `proximo_vencimiento` usa la menor `fecha_limite` de cualquier cuota pendiente (incluidas futuras generadas y vencidas).
- El detalle devuelve todas las plantillas con resumen y su lista de cuotas.
- Eliminar entidad se bloquea si tiene deudas mensuales asociadas.

### 10.5 API y DTOs

- [x] Crear router `api/routers/deudasMensuales.py` y registrarlo en `api/mainApi.py` (con `Depends(validate_token)` y `tags`):
  - [x] `GET /deudas-mensuales/`
  - [x] `POST /deudas-mensuales/` → 201
  - [x] `GET /deudas-mensuales/proximas?dias=7&moneda_id=`
  - [x] `GET /deudas-mensuales/resumen?moneda_id=`
  - [x] `GET /deudas-mensuales/{id}`
  - [x] `PUT /deudas-mensuales/{id}`
  - [x] `POST /deudas-mensuales/{id}/cancelar`
  - [x] `DELETE /deudas-mensuales/{id}`
  - [x] `POST /deudas-mensuales/cuotas/{cuota_id}/pagar`
  - [x] `PUT /deudas-mensuales/cuotas/{cuota_id}/pagos/{pago_id}`
  - [x] `DELETE /deudas-mensuales/cuotas/{cuota_id}/pagos/{pago_id}`
- [x] Crear `api/routers/dtos/deudaMensualDto.py`:
  - [x] `DeudaMensualCreate`
  - [x] `DeudaMensualUpdate`
  - [x] `DeudaMensualResponse`
  - [x] `DeudaMensualListItem`
  - [x] `CuotaMensualResponse`
  - [x] `PagoCuotaMensualCreate`
  - [x] `PagoCuotaMensualResponse`
  - [x] `DeudaMensualDetailResponse`
  - [x] `ProximaCuotaItem`
  - [x] `ResumenDeudasMensuales`
- [x] Usar `DateFromString` (`dd-mm-YYYY`) en las fechas.

Decisiones acordadas:

- `PagoCuotaMensualCreate.monto` es opcional; si falta se usa el monto de la cuota (pago completo). El mismo DTO se reutiliza en `PUT`.
- Endpoint extra `POST /deudas-mensuales/pagar-lote` con DTO `PagarCuotasMensualesCreate` para pagar varias cuotas en una transacción todo-o-nada.
- `DeudaMensualDetailResponse.cuotas` anida `pagos` dentro de cada cuota.
- `GET /entidades/{id}` ahora expone `deudas_mensuales` con el mismo formato de detalle (incluye pagos).
- DTOs extra: `PagarCuotasMensualesCreate` y `ResumenCuotasMensuales` (para `vencidas`/`proximas`).

### 10.6 Migración

- [x] Crear `alembic/versions/20261114_0004_deudas_mensuales.py` con `down_revision = "20261103_0003_entidades_deudas"`.
- [x] Crear tablas `deudamensual`, `cuotamensual`, `pagocuotamensual`.
- [x] Agregar índices y claves foráneas.
- [x] Agregar las tablas a `APP_TABLES` en `bd/migrations.py`.
- [x] No modificar tablas existentes.

Decisiones acordadas:

- La migración 0004 solo se creó y verificó; **no se aplicó** a `database.db` real (sigue en 0003).
- Se probó `upgrade head`/`downgrade base` en una base vacía temporal y `0003 → 0004 → 0003` sobre una copia de la base real, conservando usuarios, movimientos, entidades, deudas y pagos.
- `alembic check` no detecta diferencias entre la migración y `SQLModel.metadata`.
- Sin `ondelete` en FKs, siguiendo el estilo de las migraciones existentes; el CRUD elimina en orden.

### 10.7 Frontend

Página nueva:

- [ ] Crear `web/pages/deudasMensuales.html`.
- [ ] Crear `web/js/deudasMensuales.js`.
- [ ] Crear `web/css/deudasMensuales.css`.
- [ ] Header con filtros por moneda, categoría, estado y modalidad.
- [ ] Cards: compromiso mensual, pendiente total, vencidas, próximas.
- [ ] Panel izquierdo: lista de deudas mensuales con búsqueda.
- [ ] Panel derecho: detalle con cuotas actuales, vencidas, próximas e historial de pagos.
- [ ] Modales: crear/editar plantilla, pagar cuota, pagar varias atrasadas, cancelar, eliminar, editar/eliminar pago.
- [ ] Sin `backdrop-filter` (quirk de Qt WebEngine).

Sidebar:

- [ ] Nuevo ítem "Deudas mensuales" en `web/components/sidemenu.html`.
- [ ] Badge de vencidas.

Deudas existente:

- [ ] Botón "Deudas mensuales" en `web/pages/deudas.html`.
- [ ] Card/resumen de mensuales en `web/js/deudas.js`.
- [ ] Sección de mensuales en el detalle de entidad si tiene entidad asociada.

Inicio:

- [ ] Bloque "Pagos mensuales" con vencidas y próximas (7 días por defecto) en `web/pages/panelControl.html` + `web/js/panelControl.js`.
- [ ] Botón **Pagar**.
- [ ] Modal rápido con cuenta, fecha y nota.
- [ ] Refrescar al pagar.

Helpers reutilizados:

- [ ] `cargarSelectorCuentas`
- [ ] `cargarSelectorMonedas`
- [ ] `cargarSelectorTipos`
- [ ] `cargarSubtipos`
- [ ] `escaparHtml`
- [ ] `fechaParaAPI`
- [ ] `formatearFechaLegible`
- [ ] `mostrarNotificacion`

### 10.8 Tests

- [ ] Crear `tests/test_deudas_mensuales.py` y fixtures en `tests/conftest.py`:
  - [ ] Crear recurrente sin entidad, con categoría, y verificar cuota generada.
  - [ ] Pagar antes / al día / atrasada y verificar `estado_pago`.
  - [ ] Verificar movimiento con categoría elegida, `es_deuda=True`, saldo y resumen.
  - [ ] Plan total ÷ N, ajuste de centavos y finalización.
  - [ ] Pago de varias atrasadas con registros independientes.
  - [ ] Cancelar conserva pagadas y cancela futuras.
  - [ ] Editar solo afecta futuras.
  - [ ] Eliminar revierte movimientos.
  - [ ] Integración con entidad y resumen de Deudas.
  - [ ] Aislamiento entre usuarios.
  - [ ] Orden de `/proximas` (vencidas primero).
- [ ] Ejecutar `python -m pytest tests -v`.
- [ ] Ejecutar `python -m ruff check tests api/mainApi.py api/routers/deudasMensuales.py api/routers/dtos/deudaMensualDto.py bd/crud/deudaMensual.py bd/domain/deuda_mensual.py bd/models/deudaMensual.py`.

### 10.9 Documentación

- [ ] Actualizar `AGENTS.md` con la Fase 10: nuevos modelos, endpoints, migración, reglas de fechas y quirks.
- [ ] Actualizar `porHacer.md`.

### 10.10 Archivos principales

- [ ] `bd/models/deudaMensual.py`
- [ ] `bd/models/__init__.py`
- [ ] `bd/models/entidad.py`
- [ ] `bd/domain/deuda_mensual.py`
- [ ] `bd/crud/deudaMensual.py`
- [ ] `bd/crud/entidad.py`
- [ ] `api/routers/deudasMensuales.py`
- [ ] `api/routers/dtos/deudaMensualDto.py`
- [ ] `api/mainApi.py`
- [ ] `alembic/versions/20261114_0004_deudas_mensuales.py`
- [ ] `bd/migrations.py`
- [ ] `web/pages/deudasMensuales.html`
- [ ] `web/js/deudasMensuales.js`
- [ ] `web/css/deudasMensuales.css`
- [ ] `web/components/sidemenu.html`
- [ ] `web/pages/deudas.html`
- [ ] `web/js/deudas.js`
- [ ] `web/pages/panelControl.html`
- [ ] `web/js/panelControl.js`
- [ ] `tests/conftest.py`
- [ ] `tests/test_deudas_mensuales.py`
- [ ] `AGENTS.md`
- [ ] `porHacer.md`

---

## Pendientes de confirmar

1. **"Una sola fecha para todas las nuevas cuotas"**
   - ¿Es un campo opcional al editar: "fecha límite única para las cuotas futuras que se generen desde este punto"?
   - ¿O cada cuota futura mantiene su fecha límite mensual?

2. **Entidad**
   - ¿La página Deudas debe listar también las mensuales o solo sumarlas en saldos/resumen y dejar el listado en su página?

3. **Plan de cuotas**
   - ¿El saldo pendiente de la entidad debe incluir todas las cuotas impagas (incluidas futuras) y la recurrente solo las ya aparecidas? Es lo propuesto.

4. **Inicio**
   - ¿"Próximas" = 7 días, 30 días o la próxima cuota de cada deuda?
   - Propuesta: vencidas + próximos 7 días, con badge de vencidas en el sidebar.

---

## Orden de implementación

- [ ] Modelos + relación en entidad + exports.
- [ ] Migración Alembic + `APP_TABLES`.
- [ ] Reglas de negocio (`bd/domain/deuda_mensual.py`).
- [ ] CRUD de plantillas, cuotas y pagos.
- [ ] Integración con entidades y resumen.
- [ ] API: DTOs, router y registro en `mainApi.py`.
- [ ] Frontend: página, sidebar, modales y helpers.
- [ ] Inicio: bloque de pagos mensuales y pago rápido.
- [ ] Tests + lint + prueba manual.
- [ ] Documentación: `AGENTS.md` y `porHacer.md`.

---

## Fuera de alcance (por ahora)

- Abonos parciales por cuota (el pago es completo).
- Intereses, mora o recargos automáticos.
- Conversión real entre monedas con tipo de cambio.
- Recordatorios automáticos de vencimiento.
- Adjuntos o comprobantes.
- Deudas mensuales compartidas entre usuarios.

---

## Regla de avance

Antes de agregar funciones nuevas, cada cambio importante debe cumplir:

- Tener datos persistidos correctamente.
- Tener validaciones en backend.
- Tener manejo de error en frontend.
- No depender de datos de ejemplo.
- Mantener separada la lógica de negocio de los routers.
- Poder probarse manualmente desde la app.
