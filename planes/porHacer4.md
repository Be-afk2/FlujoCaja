# FlujoCaja - Roadmap técnico V4

Tareas derivadas de la auditoría de rendimiento de noviembre de 2026. Incorpora
las **Fases 11 a 13** (datos/API, frontend/assets y deuda técnica) y mantiene
pendientes la **prueba manual visual de la Fase 10** y la **Fase 7.5 -
Inteligencia financiera basada en datos** de `porHacer2.md`.

---

## Estado de partida (línea base medida)

Datos relevados antes de empezar, para comparar después de cada fase:

- `web/vendor/tailwind.js`: **398 KB** de JavaScript parseado y ejecutado en
  cada navegación (Tailwind Play CDN compilando en runtime).
- `web/fonts`: **100 archivos / 3.95 MB** con 6 familias (Hanken Grotesk, Inter,
  JetBrains Mono, Public Sans, Noto Sans, Material Symbols).
  - `material-symbols-1.woff2` solo pesa **1.1 MB** para ~25 iconos usados.
  - Los `.ttf` de Font Awesome (568 KB) son redundantes en Qt WebEngine.
- Dashboard: ~15 peticiones HTTP por carga; `cuentas/` se pide **4 veces** y
  `tipos/` **2-3 veces**.
- `movimiento` no tiene índices salvo `es_deuda`; las consultas calientes
  filtran por `user_id` + `fecha` / `cuenta_id` / `tipo_id`.
- Los endpoints de lectura de deudas mensuales hacen `commit()` (auto-sync).
- `requirements-dev.txt` no estaba instalado en el venv: `pytest` no corría.
- Grafo MCP reindexado: 1483 nodos / 6143 aristas (referencia, no métrica de la app).

---

## Fase 11 - Rendimiento de datos y API

Objetivo: que las consultas y escrituras escalen con muchos movimientos, sin
escribir en la base durante lecturas y sin autenticar dos veces por petición.

Alcance funcional:

- Índices para las consultas calientes y migración con `downgrade` verificado.
- Agregados y conteos eficientes (sin traer filas de más).
- Sincronización de cuotas fuera del camino de lectura.
- Configuración de SQLite adecuada para un proceso con hilos.
- Menos trabajo por petición en `validate_token`.

### 11.1 Índices y migración

Estado: **hecho** (migración `20261118_0005_indices_rendimiento`, head actual).

- [x] Crear `alembic/versions/20261118_0005_indices_rendimiento.py` con
      `down_revision = "20261114_0004_deudas_mensuales"`.
- [x] Índices finales (validados con `EXPLAIN QUERY PLAN` sobre una base
      sintética de 35k movimientos y 7.2k cuotas):
  - [x] `movimiento`: `ix_movimiento_user_fecha (user_id, fecha)`.
  - [x] `movimiento`: `ix_movimiento_user_cuenta_fecha (user_id, cuenta_id, fecha)`.
  - [x] `movimiento`: `ix_movimiento_user_tipo_fecha (user_id, tipo_id, fecha)`.
  - [x] `movimiento`: `ix_movimiento_user_es_deuda_fecha (user_id, es_deuda, fecha)`.
  - [x] `cuotamensual`: `ix_cuotamensual_user_estado_fecha_limite (user_id, estado, fecha_limite)`.
  - [x] `pagocuotamensual`: `ix_pagocuotamensual_user_fecha (user_id, fecha)`.
- [x] Eliminar el índice simple `ix_movimiento_es_deuda` (reemplazado por el
      compuesto; ninguna consulta filtra por `es_deuda` sin `user_id`).
- [x] Declarar los índices compuestos en `bd/models/movimiento.py` y
      `bd/models/deudaMensual.py` con `__table_args__` + `Index`, para que
      `alembic check` no detecte diferencias ("No new upgrade operations detected").
- [x] Verificar `upgrade head` → `downgrade -1` → `upgrade head` sobre una copia
      de la base real y sobre una base vacía (instalación nueva).
- [x] Medir `EXPLAIN QUERY PLAN` y tiempos de las consultas de `/movimientos`,
      `/resumen/*` y `/deudas-mensuales/*` antes y después (ver tabla abajo).

Medición (ms, mejor de 7 ejecuciones):

| Consulta | Antes | Después | Mejora |
|---|---:|---:|---:|
| Lista `/movimientos` (user+fecha, orden fecha) | 5.64 | 0.06 | 94x |
| Count de la paginación | 5.45 | 0.35 | 15x |
| `recalcular_mes` (user+cuenta+fecha) | 4.07 | 0.12 | 35x |
| Filtro por tipo (user+tipo, orden fecha) | 3.72 | 0.07 | 56x |
| Filtro `es_deuda` (user+es_deuda, orden fecha) | 5.42 | 0.06 | 89x |
| Dashboard categorías (`es_deuda=false`, limit 200) | 6.05 | 0.43 | 14x |
| Próximas cuotas (user+estado+fecha_limite) | 6.14 | 4.97 | 1.2x |

Decisiones resueltas:

- [x] **`es_deuda`**: se descarta el índice parcial (`WHERE es_deuda = 1`) y se
      usa el compuesto `(user_id, es_deuda, fecha)`, que sirve tanto para
      `es_deuda=1` como para `es_deuda=0` (el dashboard usa `=false`).
- [x] **`(deuda_mensual_id, estado)`**: descartado, no aporta nada (6.26 ms vs
      6.14 ms sin índice) porque ya existe `ix_cuotamensual_deuda_mensual_id`.
- [x] **`(user_id, fecha_limite)` en `cuotamensual`**: descartado (1.1x; el
      costo es el volumen de filas, no la búsqueda).
- [x] **`sesion.token`**: descartado; `obtener_sesion_db()` hace
      `select(Sesion).first()` sin filtrar por token y hay una sola fila.
- [x] **Próximas cuotas (1.2x)**: el índice se usa y elimina el
      `TEMP B-TREE`, pero el costo real es el `IN` con todas las plantillas
      del usuario. La mejora grande corresponde a la Fase 11.2 (quitar el `IN`
      redundante, porque las deudas ya están filtradas por `user_id`).

### 11.2 Consultas y agregados

- [ ] `bd/crud/movimiento.py` (`movimientos_filtrados`): reemplazar
      `select(Movimiento.id).all()` + `len()` por `select(func.count())`.
- [ ] `bd/crud/resumen.py` (`recalcular_mes`): reemplazar
      `func.extract("year"/"month", fecha)` por rango
      `fecha >= inicio AND fecha < inicio_mes_siguiente` (usa índice).
- [ ] `bd/crud/resumen.py` (`recalcular_todos`): eliminar el bucle cuadrático
      (N scans) y agrupar por `(cuenta_id, anio, mes)` en una sola consulta.
- [ ] `bd/crud/deudaMensual.py` (`_numeros_existentes`): batchear todos los
      `deuda_mensual_id` en un solo `IN (...)` y pasar el set a
      `_sincronizar_cuotas_sesion`.
- [ ] `bd/crud/deudaMensual.py` (`proximas_cuotas` / `resumen_deudas_mensuales`):
      quitar el `deuda_mensual_id IN (...)` redundante (las deudas ya vienen
      filtradas por `user_id`); es el costo real que el índice no resuelve.
- [ ] Revisar `listar_entidades` / `obtener_entidad` para evitar lazy loads y
      usar `selectinload` donde se accede a relaciones fuera de la sesión.
- [ ] Gráfico del dashboard (`web/js/panelControl.js`, `renderGrafico`): usar
      `GET /resumen/rango` (ya existe) en lugar de N llamadas a
      `/resumen/anual` (una por año).

Decisiones pendientes:

- [ ] Definir si `/movimientos` mantiene el límite actual por página o si se
      agrega un tope duro para exportaciones.

### 11.3 Auto-sync de cuotas fuera del camino de lectura

Hoy `listar_deudas_mensuales`, `obtener_deuda_mensual`, `proximas_cuotas`,
`resumen_deudas_mensuales`, `listar_entidades` y `obtener_entidad` hacen
`commit()` durante un GET.

- [ ] Elegir estrategia (decisión pendiente):
  - [ ] (a) sincronizar una vez al iniciar la app,
  - [ ] (b) endpoint explícito `POST /deudas-mensuales/sincronizar` invocado por
        el frontend al entrar a Deudas mensuales / Inicio,
  - [ ] (c) tarea periódica en el proceso de la API.
- [ ] Dejar los GET sin escrituras (`session.flush()` como máximo, nunca
      `commit`), manteniendo respuesta idéntica para el usuario.
- [ ] Asegurar que la sincronización siga siendo idempotente y batcheada.
- [ ] Badge del sidebar (`web/js/loadmenu.js`): no consultar
      `/deudas-mensuales/resumen` en cada página; usar cache corto (ver Fase 12)
      o un parámetro liviano (`?campos=vencidas`).
- [ ] Tests: dos GET consecutivos no deben cambiar la cantidad de cuotas ni
      `fecha_limite`.

### 11.4 Configuración de SQLite

- [ ] En `bd/database.py`, agregar listener `connect` con:
      `journal_mode=WAL`, `synchronous=NORMAL`, `foreign_keys=ON`,
      `busy_timeout=5000`.
- [ ] Revisar `connect_args` / pool para uso desde el threadpool de uvicorn.
- [ ] Ajustar `api/routers/datos.py` (backup/restaurar): forzar
      `PRAGMA wal_checkpoint(TRUNCATE)` antes de copiar el archivo y contemplar
      los archivos `-wal` / `-shm` al restaurar.
- [ ] Confirmar que `PRAGMA integrity_check` sigue pasando tras restaurar.

### 11.5 Autenticación por petición

- [ ] `api/dependencies.py`: cachear `token → User` en memoria con TTL corto
      (5-10 s) para evitar 2 SELECT por request.
- [ ] Invalidar el cache en login, logout y `actualizar_token_bd`.
- [ ] Alternativa a evaluar: token firmado (HMAC) con expiración para no tocar
      la base en cada request.
- [ ] El fixture `reset_db` de los tests debe limpiar el cache entre casos.

### 11.6 Tests de la fase

- [ ] Test de migración `0004 ↔ 0005` sobre base temporal.
- [ ] Tests de regresión de resumen y saldos tras agregar índices.
- [ ] Test de sync idempotente y de GET sin escrituras.
- [ ] Test de cache de autenticación (login, request, logout → 401).
- [ ] Ejecutar `python -m pytest tests -v` y `python -m ruff check ...`.

### 11.7 Documentación

- [ ] Actualizar `AGENTS.md`: índices, PRAGMAs, estrategia de sync y cache de
      autenticación.
- [ ] Registrar en `porHacer4.md` la versión de migración en `head`.

### 11.8 Archivos principales

- [ ] `alembic/versions/<fecha>_0005_indices_rendimiento.py`
- [ ] `bd/models/movimiento.py`
- [ ] `bd/models/deudaMensual.py`
- [ ] `bd/database.py`
- [ ] `bd/crud/movimiento.py`
- [ ] `bd/crud/resumen.py`
- [ ] `bd/crud/deudaMensual.py`
- [ ] `bd/crud/sesion.py`
- [ ] `api/dependencies.py`
- [ ] `api/routers/datos.py`
- [ ] `web/js/panelControl.js`
- [ ] `web/js/loadmenu.js`

---

## Fase 12 - Frontend y assets

Objetivo: reducir el trabajo por navegación (menos peticiones, menos JS
compilado en runtime, menos bytes de fuentes) y eliminar duplicación que ya
provocó bugs (fade de página copiado en cada HTML).

Alcance funcional:

- Cache de catálogos y dedupe de peticiones.
- Componentes (sidebar) sin round-trip por página.
- Tailwind precompilado o criterio explícito para mantener el CDN.
- Fuentes e iconos ajustados a lo que realmente usa la app.
- CSS/JS compartido y rutas relativas.

### 12.1 Cache de peticiones y catálogos

- [ ] Agregar en `web/js/funciones.js` un helper `getCached(path, ttlMs)` con
      almacenamiento en `sessionStorage` (TTL 30-60 s).
- [ ] Deduplicar peticiones concurrentes en `request()` (mapa de promesas
      in-flight por `method + path`).
- [ ] Aplicar cache a catálogos estables: `cuentas/`, `monedas/`, `tipos/`,
      `subtipos/`, `entidades/`.
- [ ] Invalidar el cache tras mutaciones (`crear*`, `editar*`, `eliminar*`,
      pagos) y al cerrar sesión.
- [ ] Medir peticiones por navegación: objetivo ≤ 8 (hoy ~15).

### 12.2 Componentes reutilizables

- [ ] Cachear `web/components/sidemenu.html` (sessionStorage) o inlinearlo en
      una plantilla compartida.
- [ ] Evitar bloquear el render esperando el sidebar: insertar markup base y
      completar badge/nombre usuario después.
- [ ] Revisar `cargarNombreUsuario()` y `cargarBadgeDeudasMensuales()` para que
      no disparen peticiones redundantes con la página.

### 12.3 Tailwind precompilado

- [ ] Evaluar y decidir (decisión pendiente):
  - [ ] (a) precompilar a `web/css/tailwind.css` con Tailwind CLI y eliminar
        `web/vendor/tailwind.js` del runtime,
  - [ ] (b) mantener el CDN solo en desarrollo y servir CSS compilado en prod.
- [ ] Unificar los `tailwind.config` inline (colores, radios, fuentes) en un
      único archivo de configuración de build.
- [ ] Verificar que las clases generadas dinámicamente en JS (por ejemplo en
      `deudas.js`, `panelControl.js`) estén incluidas en el `content` del build.
- [ ] Comparar tiempo de carga por página antes/después.

### 12.4 Fuentes e iconos

- [ ] Quitar del bundle las familias sin uso real:
      `Hanken Grotesk`, `JetBrains Mono`, `Public Sans`, `Noto Sans`
      (reemplazar por `Inter` o `monospace` del sistema en las páginas que las
      usan).
- [ ] Subsetear `material-symbols` a los iconos usados (parámetro `text=`) o
      migrar esos iconos a Font Awesome ya vendorizado.
- [ ] Eliminar los `.ttf` de Font Awesome y sus `src` en `all.min.css`
      (WebEngine soporta `woff2`).
- [ ] Regenerar `web/css/fonts.css` con `scripts/vendor_assets.py` y verificar
      que no queden referencias rotas.
- [ ] Objetivo: `web/fonts` por debajo de **1 MB**.

### 12.5 CSS/JS compartido

- [ ] Crear `web/css/base.css` con: fade de página (`page-fade-in`),
      `@view-transition`, scrollbars, `custom-modal-backdrop`, `modal-enter` y
      `fade-in-suave`.
- [ ] Hacer que todas las páginas incluyan `base.css` y eliminar el CSS
      duplicado de cada `<style>` / `deudas.css` / `deudasMensuales.css`.
- [ ] Extraer helpers repetidos de `deudas.js` y `deudasMensuales.js` a
      `web/js/formato.js` (montos, fechas, `escaparHtml`) y
      `web/js/modales.js` (abrir/cerrar, foco, `Escape`, click en backdrop).
- [ ] Documentar la regla: el fade y los estilos base **no** se copian por página.

### 12.6 Rutas relativas y CORS

- [ ] Cambiar `CONFIG.baseUrl` a rutas relativas (la UI se sirve desde el mismo
      origen que la API).
- [ ] Restringir CORS en `api/mainApi.py` a
      `["http://127.0.0.1:8000", "http://localhost:8000"]` (o quitarlo si no se
      usa).
- [ ] Verificar login, backup/restaurar y descargas con rutas relativas.

### 12.7 Splash

- [ ] Reducir `web/index.html` a un redirect mínimo (sin Tailwind ni fuentes),
      o resolver el redirect en el servidor.
- [ ] Mantener la validación de sesión actual (`remember_session` + token).

### 12.8 Tests y documentación

- [ ] Prueba manual de cada página en PyQt6 WebEngine (sin `backdrop-filter`).
- [ ] Verificar que no haya FOUC (flash de contenido sin estilos) al navegar.
- [ ] Actualizar `AGENTS.md` con la estructura de `base.css`, el cache de
      catálogos y el build de Tailwind.

### 12.9 Archivos principales

- [ ] `web/js/funciones.js`
- [ ] `web/components/sidemenu.html`
- [ ] `web/js/loadmenu.js`
- [ ] `web/css/base.css` (nuevo)
- [ ] `web/css/deudas.css`
- [ ] `web/css/deudasMensuales.css`
- [ ] `web/js/formato.js` (nuevo)
- [ ] `web/js/modales.js` (nuevo)
- [ ] `web/pages/*.html`
- [ ] `web/index.html`
- [ ] `scripts/vendor_assets.py`
- [ ] `api/mainApi.py`

---

## Fase 13 - Deuda técnica, seguridad y developer experience

Objetivo: cerrar riesgos de seguridad, mejorar el diagnóstico y dejar la suite
de tests y el lint en condiciones de sostener las fases anteriores.

Alcance funcional:

- Superficie de seguridad mínima para una app local.
- Exportaciones sin traer 100k filas al navegador.
- JS de deudas modularizado.
- Suite de tests rápida y ejecutable desde cero.

### 13.1 Seguridad

- [ ] `api/mainApi.py`: no loguear headers completos en modo debug (filtrar
      `Authorization` y `Cookie`).
- [ ] Revisar expiración/rotación del token de sesión y almacenamiento en
      `localStorage` cuando "recordar sesión" está activo.
- [ ] Validar tamaño y tipo de archivo en `POST /datos/restaurar`.
- [ ] Documentar que la API escucha solo en `127.0.0.1`.

### 13.2 Exportaciones

- [ ] Nuevo endpoint `GET /movimientos/export` con `yield_per` / streaming CSV
      en lugar de `cantidad=100000`.
- [ ] Aceptar los mismos filtros que `/movimientos`.
- [ ] Reutilizar el endpoint en `exportarCSV()` de `panelControl.js`.
- [ ] Agregar tests de export (encabezado, BOM, filas).

### 13.3 Modularización del frontend de deudas

- [ ] Separar `web/js/deudas.js` (63 KB) en módulos por responsabilidad:
      estado, render de entidades, render de deudas, pagos, modales.
- [ ] Separar `web/js/deudasMensuales.js` (61 KB) con el mismo criterio.
- [ ] Reutilizar los helpers compartidos de la Fase 12.5.
- [ ] Mantener nombres de funciones públicas que usan los `onclick` existentes.

### 13.4 Suite de tests

- [ ] Documentar/instalar `requirements-dev.txt` en el venv (hoy `pytest` no
      está instalado).
- [ ] Medir la suite con `python -m pytest tests -q --durations=10`.
- [ ] Acelerar `reset_db`: base plantilla sembrada + copia por test, o
      transacción con rollback, en lugar de `drop_all` + `create_all` + seed
      por test.
- [ ] Agregar un test de humo que arranque la app en modo `--api` y consulte
      `/health` y `/health/token`.

### 13.5 Lint y calidad

- [ ] Ampliar `ruff` a `api/`, `bd/` y `web/` (JS no aplica) de forma
      incremental.
- [ ] Corregir imports y líneas largas en los módulos incluidos.
- [ ] Ejecutar `run_lint.ps1` y `run_tests.ps1` como verificación final.

### 13.6 Documentación

- [ ] Actualizar `AGENTS.md` con: comandos de export, cache, PRAGMAs,
      estrategia de sync y estado de la suite.
- [ ] Actualizar `porHacer.md` marcando las fases completadas.

### 13.7 Archivos principales

- [ ] `api/mainApi.py`
- [ ] `api/routers/movimientos.py`
- [ ] `api/routers/datos.py`
- [ ] `web/js/panelControl.js`
- [ ] `web/js/deudas.js`
- [ ] `web/js/deudasMensuales.js`
- [ ] `tests/conftest.py`
- [ ] `tests/test_reportes.py`
- [ ] `pyproject.toml`
- [ ] `run_tests.ps1`
- [ ] `run_lint.ps1`

---

## Decisiones resueltas

- [x] **Fases**: la optimización se divide en datos/API (11), frontend/assets
      (12) y deuda técnica/DX (13). Se implementan en ese orden.
- [x] **Tailwind**: se mantiene el CDN hasta cerrar la Fase 11; la decisión de
      precompilar se toma al inicio de la Fase 12.
- [x] **Backups**: cualquier cambio de PRAGMA o índices debe verificar
      backup/restaurar antes de darse por cerrado.

---

## Decisiones pendientes

- [x] **Índices**: lista final confirmada midiendo con `EXPLAIN QUERY PLAN`
      sobre una base sintética de 35k movimientos / 7.2k cuotas; ver Fase 11.1.
- [ ] **Auto-sync**: elegir entre sincronizar al iniciar, endpoint explícito o
      tarea periódica (Fase 11.3).
- [ ] **Autenticación**: cache en memoria con TTL vs. token firmado sin estado.
- [ ] **Iconos**: subset de Material Symbols vs. migración a Font Awesome.
- [ ] **Tailwind**: precompilado con build vs. CDN en desarrollo + CSS en prod.

---

## Orden de implementación

- [x] Fase 11.1: migración de índices y modelos.
- [ ] Fase 11.2: consultas y agregados.
- [ ] Fase 11.4: PRAGMAs de SQLite y backup/restaurar.
- [ ] Fase 11.3: auto-sync fuera de los GET.
- [ ] Fase 11.5: cache de autenticación.
- [ ] Fase 11.6: tests y cierre de la Fase 11.
- [ ] Fase 12.1-12.2: cache de catálogos y sidebar.
- [ ] Fase 12.5: `base.css` y helpers JS compartidos.
- [ ] Fase 12.4: fuentes e iconos.
- [ ] Fase 12.3: decisión e implementación de Tailwind.
- [ ] Fase 12.6-12.7: rutas relativas, CORS y splash.
- [ ] Fase 12.8: verificación visual en WebEngine.
- [ ] Fase 13.1: seguridad.
- [ ] Fase 13.2: export CSV por streaming.
- [ ] Fase 13.3: modularización de deudas.
- [ ] Fase 13.4-13.5: suite, lint y documentación.
- [ ] Prueba end-to-end final: arranque completo (`python main.py`), navegación
      por todas las páginas y backup/restaurar.

---

## Métricas de éxito

- Peticiones por navegación del dashboard: **≤ 8** (línea base ~15).
- `cuentas/` y `tipos/` pedidos **una sola vez** por carga.
- Ningún GET de deudas mensuales escribe en la base.
- `/movimientos` y `/resumen/*` con índice utilizado (`EXPLAIN QUERY PLAN`).
- `web/vendor/tailwind.js` fuera del runtime o justificado por escrito.
- `web/fonts` por debajo de **1 MB** y sin familias sin uso.
- Suite de tests ejecutable desde un venv limpio y más rápida que la línea base.
- Backup y restaurar funcionando con WAL activo.

---

## Fuera de alcance (por ahora)

- Migrar de SQLite a PostgreSQL u otro motor.
- Framework de frontend con bundler pesado (React/Vue/Svelte).
- Multiusuario concurrente real (la sesión sigue siendo única).
- Sincronización en la nube o API remota.
- Service worker / PWA / modo offline.
- Internacionalización (i18n) y multi-idioma.
- Rediseño visual de las páginas.

---

## Regla de avance

Antes de agregar funciones nuevas, cada cambio importante debe cumplir:

- Medir antes y después (peticiones, tiempo de carga o tiempo de consulta).
- Tener datos persistidos correctamente y migración con `downgrade` verificado.
- Tener validaciones en backend y manejo de error en frontend.
- No depender de datos de ejemplo.
- Mantener separada la lógica de negocio de los routers.
- No introducir `backdrop-filter` (quirk de Qt WebEngine).
- Poder probarse manualmente desde la app y con la suite de tests.
