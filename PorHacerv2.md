# FlujoCaja - Roadmap tecnico V2

Tareas derivadas de `idea.md`. Incorpora la **Fase 9 - Entidades y deudas** y
mantiene pendiente la **Fase 7.5 - Inteligencia financiera basada en datos**.

---

## Fase 9 - Entidades y deudas

Objetivo: registrar personas/empresas con deudas en ambas direcciones (me deben /
yo debo), con abonos parciales, saldos por moneda y movimientos vinculados.

### 9.1 Modelo de datos

- [x] Crear `bd/models/entidad.py` con `Entidad` (`id`, `user_id`, `nombre`, `tipo`, `descripcion`).
- [x] Crear `bd/models/deuda.py` con `Deuda` (`id`, `user_id`, `entidad_id`, `direccion`, `monto_original`, `moneda_id`, `descripcion`, `fecha`, `vencimiento`, `movimiento_inicial_id`).
- [x] Crear `PagoDeuda` (`id`, `user_id`, `deuda_id`, `monto`, `fecha`, `cuenta_id`, `movimiento_id`, `descripcion`).
- [x] Agregar `es_deuda: bool = False` a `bd/models/movimiento.py`.
- [x] Agregar `total_ingresos_deuda` y `total_gastos_deuda` a `bd/models/resumen.py`.
- [x] Exportar los modelos nuevos en `bd/models/__init__.py`.
- [x] Definir relaciones: `Entidad` 1→N `Deuda`, `Deuda` 1→N `PagoDeuda`, `Deuda.movimiento_inicial_id`→`Movimiento` (opcional), `PagoDeuda.movimiento_id`→`Movimiento` (obligatorio, único).
- [x] Crear índices: `entidad.user_id`, `deuda.user_id`, `deuda.entidad_id`, `pagodeuda.deuda_id`, `movimiento.es_deuda`.

### 9.2 Reglas de negocio

- [x] Implementar tabla de signos: desembolso me deben (−cuenta / +deuda), cobro me deben (+cuenta / −deuda), desembolso yo debo (+cuenta / +deuda), pago yo debo (−cuenta / −deuda).
- [x] Guardar montos de `Deuda`/`PagoDeuda` siempre positivos; calcular signo según dirección y evento.
- [x] Implementar subtipos automáticos bajo tipo **"Deudas"**: Préstamo otorgado, Préstamo recibido, Abono deuda, Pago deuda, Cobro deuda.
- [x] Calcular estado: `pendiente = monto_original − suma(abonos)`; `pagada` si `<= 0`; `vencida` si `> 0` y `vencimiento < hoy`; `pendiente` en el resto.
- [x] Validar `monto_original > 0` y que el abono no supere el pendiente.
- [ ] Advertir en UI si la cuenta del pago difiere de la moneda de la deuda (helper `monedas_distintas` listo en `bd/domain/deuda.py`; falta UI en 9.8).
- [x] Mostrar saldos de entidad por moneda (cálculo `calcular_saldos_por_moneda` + `listar_entidades` por moneda; la UI llega en 9.8).
- [x] Bloquear edición/eliminación de movimientos con `es_deuda=True` desde la tabla general de movimientos (implementado en 9.3).

### 9.3 Refactor de movimientos

- [x] Extraer `_crear_movimiento_sesion(session, ..., es_deuda=False)` en `bd/crud/movimiento.py`.
- [x] Extraer `_actualizar_movimiento_sesion(session, mov, ...)`.
- [x] Extraer `_eliminar_movimiento_sesion(session, mov)`.
- [x] Hacer que las funciones públicas usen las internas y hagan commit.
- [x] Bloquear `crear_movimiento` y `update_movimiento` si `es_deuda=True`.
- [x] Devolver error claro en `delete_movimiento` si el movimiento pertenece a una deuda.
- [x] Agregar `es_deuda: Optional[bool]` a `MovimientoFilter` y `movimientos_filtrados`.

### 9.4 CRUD

- [x] Crear `bd/crud/entidad.py` (crear, listar con saldos por moneda, detalle, editar, eliminar con bloqueo si tiene deudas).
- [x] Crear `bd/crud/deuda.py` con transacciones atómicas (deuda + movimiento + saldo + resumen).
- [x] Implementar alta de deuda sin cuenta (solo obligación, sin mover saldos).
- [x] Implementar alta de deuda con cuenta (desembolso inicial + actualización de saldo).
- [x] Implementar registro de pago/cobro/abono con cuenta obligatoria.
- [x] Implementar edición de deuda (descripción/vencimiento siempre; monto/moneda/dirección solo sin abonos).
- [x] Implementar edición de abono (revertir movimiento anterior y aplicar el nuevo).
- [x] Implementar eliminación de abono (borrar movimiento vinculado, revertir saldo y resumen).
- [x] Implementar eliminación de deuda (borrar todos sus movimientos y revertir saldos).

### 9.5 Resumen y reportes

- [x] Actualizar `actualizar_por_movimiento` para aceptar `es_deuda` y `old_es_deuda`.
- [x] Actualizar `recalcular_mes` para calcular `total_ingresos_deuda` y `total_gastos_deuda`.
- [x] Mantener en `ResumenMensual` el total general (incluye deudas) más el desglose.
- [ ] Agregar `incluir_deudas: bool = True` a `/resumen/mensual`, `/resumen/anual` y `/resumen/rango`; restar el desglose cuando sea `false`.

### 9.6 API y DTOs

- [x] Extraer `DateFromString` a `api/routers/dtos/common.py` y reutilizarlo.
- [x] Crear `api/routers/dtos/entidadDto.py`: `EntidadCreate`, `EntidadUpdate`, `EntidadResponse`, `SaldoEntidad`, `EntidadDetailResponse`.
- [x] Crear `api/routers/dtos/deudaDto.py`: `DeudaCreate`, `DeudaUpdate`, `DeudaResponse`, `PagoDeudaCreate`, `PagoDeudaResponse`.
- [x] Crear `api/routers/entidades.py`:
  - [x] `GET /entidades/` (saldos por moneda, pendientes, próximo vencimiento).
  - [x] `POST /entidades/` → 201.
  - [x] `GET /entidades/{id}` (entidad + deudas + pagos).
  - [x] `PUT /entidades/{id}`.
  - [x] `DELETE /entidades/{id}` → 400 si tiene deudas.
- [x] Crear `api/routers/deudas.py`:
  - [x] `GET /deudas/` con filtros `entidad_id`, `direccion`, `estado`.
  - [x] `POST /deudas/` → 201, acepta `cuenta_inicial_id` opcional.
  - [x] `PUT /deudas/{id}`.
  - [x] `DELETE /deudas/{id}` (deuda + pagos + movimientos vinculados).
  - [x] `POST /deudas/{id}/pagos` → 201.
  - [x] `PUT /deudas/{id}/pagos/{pago_id}`.
  - [x] `DELETE /deudas/{id}/pagos/{pago_id}`.
- [x] Registrar ambos routers en `api/mainApi.py` (con `Depends(validate_token)` y `tags`).

### 9.7 Migración, seeds y compatibilidad

- [x] Crear `alembic/versions/20261103_0003_entidades_deudas.py` con `down_revision = "20260704_0002_add_descripcion"`.
- [x] Crear tablas `entidad`, `deuda`, `pagodeuda`.
- [x] Agregar `movimiento.es_deuda` con `server_default="0"`.
- [x] Agregar `resumenmensual.total_ingresos_deuda` y `total_gastos_deuda` con `server_default="0"`.
- [x] Agregar índices de la fase.
- [x] Agregar tipo `Deudas` ("Préstamos, deudas y cobros") a `DEFAULT_TIPOS` en `bd/seeds.py`.
- [x] Agregar subtipos idempotentes en `seed_db()` (Préstamo otorgado, Préstamo recibido, Abono deuda, Pago deuda, Cobro deuda).
- [x] Ajustar `apply_database_migrations()`: si la base no tiene `movimiento.descripcion` → `stamp` en `20260629_0001_initial_schema`; si la tiene → `stamp` en `20260704_0002_add_descripcion`; luego `upgrade head`.
- [x] Agregar las nuevas tablas a `APP_TABLES` en `bd/migrations.py`.

### 9.8 Frontend

- [ ] Crear `web/pages/deudas.html` + `web/js/deudas.js` con layout de dos paneles.
- [ ] Panel izquierdo: buscador de entidades, tarjetas (nombre, tipo, saldo neto por moneda, pendientes, próximo vencimiento), botón "Nueva entidad", filtro de moneda.
- [ ] Panel derecho: cabecera de entidad, resumen (a favor, en contra, neto), filtros (Todas / Me deben / Yo debo / Vencidas / Pagadas), botón "Nueva deuda".
- [ ] Lista de deudas con badge de dirección, descripción, monto original, pendiente, vencimiento, estado, barra de progreso, historial de pagos expandible y acciones (Abonar/Pagar/Cobrar, Editar, Eliminar).
- [ ] Modal nueva/editar entidad.
- [ ] Modal nueva deuda (dirección, monto, moneda, fecha, vencimiento, descripción, checkbox "Registrar movimiento inicial en una cuenta", selector de cuenta condicional, texto dinámico "Sale de mi cuenta"/"Entra a mi cuenta").
- [ ] Modal registrar pago/cobro (pendiente actual y resultante, monto, fecha, cuenta, nota, advertencia de moneda distinta).
- [ ] Modal editar deuda y editar abono.
- [ ] Confirmación de eliminación con aviso de reversión de movimientos.
- [ ] Agregar ítem **"Deudas"** al sidebar en `web/components/sidemenu.html`.
- [ ] Agregar `cargarSelectorMonedas(selectId, seleccionado)` en `web/js/funciones.js` y reutilizar `cargarSelectorCuentas`, `fechaParaAPI`, `formatearDinero`.

### 9.9 Dashboard y transacciones

- [ ] Agregar toggle "Incluir deudas en totales" persistido en `localStorage`.
- [ ] Aplicar el toggle a tarjetas y gráficos (`web/js/panelControl.js`).
- [ ] Pasar `es_deuda=false` al gráfico de categorías cuando el toggle esté desactivado.
- [ ] Mostrar badge "Deuda" en la tabla de movimientos y en recientes.
- [ ] Mantener la visualización de movimientos de deuda en el listado general sin permitir editarlos desde ahí.

### 9.10 Tests y calidad

- [ ] Crear `tests/test_entidades.py`: crear, listar, editar, eliminar sin deudas, eliminar con deudas → 400.
- [ ] Crear `tests/test_deudas.py`:
  - [ ] Deuda sin cuenta: no mueve saldo, pendiente = monto.
  - [ ] Deuda con cuenta: saldo según tabla de signos, movimiento `es_deuda=True` con tipo/subtipo correctos, resumen con desglose.
  - [ ] Abono parcial: saldo correcto, pendiente reducido, subtipo "Abono deuda".
  - [ ] Pago final: estado `pagada`, subtipo "Pago deuda"/"Cobro deuda".
  - [ ] Sobrepago → 400.
  - [ ] Pago con cuenta de otro usuario → 400.
  - [ ] Editar abono: saldo y pendiente recalculados.
  - [ ] Eliminar abono: movimiento eliminado, saldo revertido, pendiente restaurado.
  - [ ] Eliminar deuda: todos los movimientos revertidos.
  - [ ] Deuda vencida: estado `vencida`.
  - [ ] Moneda distinta: sin conversión y sin romper cálculos.
  - [ ] Aislamiento de entidades, deudas y pagos entre usuarios.
- [ ] Tests de reportes: `resumen/*?incluir_deudas=false` resta el desglose; `movimientos/?es_deuda=false` filtra; movimiento de deuda no editable/eliminable desde `/movimientos`.
- [ ] Ejecutar `python -m pytest tests -v`.
- [ ] Ejecutar `python -m ruff check tests api/mainApi.py` (o `.\run_lint.ps1`).
- [ ] Documentación: actualizar `AGENTS.md` y `porHacer.md` con la Fase 9.
- [ ] Prueba manual end-to-end de la página de deudas.

---

## Fase 7.5 - Inteligencia financiera basada en datos

Objetivo: aprovechar el historial ya almacenado para entregar hallazgos claros,
proyecciones explicables y alertas accionables. Se trabajará por usuario y se
respetará el aislamiento actual de sus datos.

### Datos disponibles y alcance inicial

Fuente principal: `Movimiento` (`monto`, `es_ingreso`, `fecha`, `cuenta`,
`tipo`, `subtipo`, `descripcion`, `user_id`), complementada por `Cuenta`
(`saldo`, tipo y moneda) y el agregado `ResumenMensual` (ingresos, gastos y
neto por cuenta/mes). Esto permite analizar comportamiento temporal, categorías
y cuentas sin incorporar datos externos ni decisiones automatizadas.

### Etapa 1 - Fundaciones y calidad de datos

- [ ] Definir un contrato de métricas y periodos: moneda, cuenta, zona horaria,
  mes calendario y reglas para ingresos/gastos/reembolsos.
- [ ] Crear consultas/servicio de analítica separado del CRUD para agregar
  movimientos por día, semana, mes, tipo, subtipo y cuenta.
- [ ] Detectar y comunicar cobertura insuficiente (por ejemplo, menos de tres
  meses o pocos movimientos); nunca presentar una proyección como certeza.
- [ ] Incorporar pruebas con datos sintéticos para agregados, filtros, meses sin
  movimientos, montos negativos y aislamiento por usuario.
- [ ] Mantener los cálculos reproducibles desde los movimientos; usar
  `ResumenMensual` solo como optimización/caché verificable.

### Etapa 2 - Analítica descriptiva y comparativa

- [ ] Evolución de ingresos, gastos y flujo neto: mensual, acumulado y
  comparación con el periodo anterior.
- [ ] Distribución y tendencia de gasto por tipo, subtipo y cuenta; mostrar
  importe, porcentaje del total y variación absoluta/porcentual.
- [ ] Calendario de gasto e identificación de días/semanas de mayor salida de
  dinero.
- [ ] Concentración de gastos: categorías y descripciones que explican la mayor
  parte del gasto, para detectar focos de ahorro.
- [ ] Salud de liquidez: saldo actual por cuenta, flujo neto reciente y ritmo
  promedio de gasto; no sumar cuentas de distintas monedas sin conversión.
- [ ] Filtros consistentes por periodo, cuenta, moneda y categoría, con opción
  de exportar los mismos datos que alimentan cada gráfico.

### Etapa 3 - Alertas y patrones explicables

- [ ] Detectar gastos inusuales comparando cada movimiento con la mediana y
  variabilidad histórica de su categoría/cuenta; mostrar siempre el motivo y
  permitir descartarlo.
- [ ] Detectar categorías con aumento sostenido (por ejemplo, frente al promedio
  móvil de los últimos tres meses) y descensos de ingreso relevantes.
- [ ] Identificar gastos recurrentes candidatos por similitud de descripción,
  importe, categoría e intervalo entre fechas; solicitar confirmación del
  usuario antes de etiquetarlos como recurrentes.
- [ ] Crear centro de alertas con severidad, fecha, explicación, estado visto y
  enlace a los movimientos que la originan.

### Etapa 4 - Proyecciones conservadoras

- [ ] Proyectar cierre de mes: gasto e ingreso acumulados + ritmo diario del
  periodo actual, comparado con meses equivalentes anteriores.
- [ ] Proyectar saldo a 30/60/90 días por cuenta usando flujo neto histórico y
  recurrentes confirmados; indicar rango probable y supuestos usados.
- [ ] Mostrar fecha estimada de saldo bajo para una cuenta, solo cuando haya
  suficiente historial y sin confundirla con una alerta bancaria real.
- [ ] Medir error de predicción de forma retrospectiva (backtesting) antes de
  activar una proyección para usuarios; publicar cobertura, error medio y nivel
  de confianza.
- [ ] Empezar con medias móviles, mediana y tendencia lineal robusta. Evaluar
  modelos más complejos únicamente si el historial y el backtesting demuestran
  una mejora clara.

### Etapa 5 - Datos que conviene capturar a futuro (opcionales)

- [ ] Añadir presupuestos por categoría y periodo para comparar gasto real vs.
  plan y anticipar sobrepasos.
- [ ] Permitir marcar movimientos como recurrentes, transferencia interna,
  reembolso o extraordinario para evitar sesgos en análisis y proyecciones.
- [ ] Guardar una contraparte/comercio normalizado, conservando la descripción
  original, para agrupar compras similares con mayor precisión.
- [ ] Registrar objetivos de ahorro y fechas objetivo para transformar las
  proyecciones en escenarios de avance.
- [ ] Diseñar conversión de monedas con fecha/tipo de cambio antes de producir
  totales globales multi-moneda.

### Entregables técnicos y de experiencia

- [ ] Endpoints de solo lectura bajo `/analiticas` con DTOs versionados,
  filtros explícitos y autorización mediante el usuario autenticado.
- [ ] Nueva vista "Analíticas" con resumen, detalle bajo demanda, estados sin
  historial y texto claro sobre metodología y limitaciones.
- [ ] Persistir únicamente preferencias y alertas confirmadas; recalcular las
  métricas/proyecciones desde los movimientos o con cachés invalidables.
- [ ] Añadir pruebas unitarias de fórmulas, integración de endpoints y casos de
  regresión con una serie temporal conocida.

---

## Orden de implementación

- [ ] Modelos + migración + seeds + exports.
- [ ] Refactor de movimientos con `es_deuda` y desglose de resumen.
- [ ] CRUD de entidades y deudas con transacciones atómicas.
- [ ] API: DTOs, routers, registro en `mainApi.py`.
- [ ] Frontend: página de deudas, sidebar, modales.
- [ ] Dashboard: toggle de deudas + badges.
- [ ] Tests + lint + prueba manual.
- [ ] Documentación: actualizar `AGENTS.md` y `porHacer.md` con la Fase 9.

---

## Fuera de alcance (por ahora)

- Intereses, mora o recargos automáticos.
- Conversión real entre monedas con tipo de cambio.
- Recordatorios automáticos de vencimiento.
- Adjuntos o comprobantes.
- Historial de auditoría de cambios.
- Deudas compartidas entre usuarios.

