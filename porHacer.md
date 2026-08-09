# FlujoCaja - Roadmap tecnico

## Vision

Convertir el prototipo actual en una aplicacion local mantenible para registrar,
consultar y analizar flujo de caja personal.

La arquitectura objetivo es:

- Backend local con FastAPI.
- Persistencia con SQLite y SQLModel.
- Interfaz web en HTML, JavaScript y Tailwind CSS.
- Ventana de escritorio con PyQt6 WebEngine.
- Version CLI conservada solo como legado o herramienta auxiliar.

---

## Estado actual

El proyecto ya cuenta con:

- API REST local.
- Modelos SQLModel para usuarios, cuentas, monedas, tipos, subtipos y movimientos.
- Base de datos SQLite.
- Interfaz web inicial.
- Login, creacion de usuario y algunas pantallas conectadas parcialmente.
- Arranque integrado desde `main.py`.

Pendientes principales:

- Completar el CRUD de movimientos.
- Conectar todas las pantallas web con datos reales.
- Fortalecer sesiones y autenticacion.
- Ordenar configuracion, rutas de datos y estructura de capas.
- Agregar tests.
- Preparar empaquetado como aplicacion de escritorio.

---

## Fase 0 - Cerrar deuda del prototipo

Objetivo: ordenar lo existente antes de seguir agregando funcionalidad.

- [x] Declarar oficialmente la arquitectura actual en la documentacion.
- [x] Marcar `app.py`, `menus/` y `widget/` como version CLI heredada.
- [x] Revisar archivos con textos o caracteres de codificacion rota.
- [x] Eliminar imports duplicados o no usados.
- [x] Reemplazar `print()` de depuracion por logging.
- [ ] Separar datos de ejemplo de datos reales.
- [x] Revisar nombres inconsistentes: gasto, registro, movimiento.
- [x] Definir si el termino principal sera `movimiento`.

---

## Fase 0.5 — Eliminar codigo duplicado / refactorizar funciones redundantes

Objetivo: reducir mantenimiento eliminando funciones que hacen lo mismo en distintos lugares.

### Funciones identicas o casi identicas (unificar)

- [x] `comprobar_conexion` duplicada en `bd/bd.py` y `app.py` — eliminada de `bd/bd.py` (código muerto)
- [x] `init_db` duplicada en `bd/database.py` y `bd/main.py` — eliminado `bd/main.py`
- [x] `engine` de BD duplicado en `bd/database.py` y `bd/main.py` — eliminado `bd/main.py`
- [x] `CrearUsuario` en `bd/main.py` duplicado de `bd/crud/user.py:crear_usuario()` — eliminado `bd/main.py`
- [x] `guardarsesion` en `app.py` wrapper trivial — reemplazada por `guardar_sesion_bd` directo

### Funciones JS duplicadas (login.js / CrearCuenta.js)

- [x] Extraer a `web/js/validacion.js` compartido: `validarCampo`, `destacarError`, `limpiarError`, `limpiarErrorAlEscribir`, `togglePasswordVisibility`, `validarFormulario` (se deja `obtenerValoresFormulario` por pagina porque usa distintos field keys)

### Funciones de sesion redundantes en `bd/crud/sesion.py`

- [x] Renombrar `obtener_session_bd()` → `crear_session_sqlmodel()`
- [x] Eliminar `validar_token(token)` — reemplazada por `obtener_usuario_por_token()` en `life_token`

### Wrappers API sin logica adicional

- [x] Evaluar capa de wrappers — eliminados los de `moneda.py` (pass-through); mantenidos los de `cuenta.py` porque inyectan `Depends(validate_token)`
- [x] `get_tipo_lista` en `bd/crud/tipo.py` — eliminada; el mapeo `.nombre` se hace en cada caller

---

## Fase 1 - Configuracion y base tecnica

Objetivo: hacer que la app arranque y persista datos de manera predecible.

- [x] Crear un modulo de configuracion centralizado.
- [x] Mover valores hardcodeados a configuracion:
  - host API,
  - puerto API,
  - ruta de base de datos,
  - modo debug,
  - timeout del frontend.
- [x] Mover `database.db` fuera del repo, idealmente a `%APPDATA%/FlujoCaja/`.
- [x] Asegurar que `database.db` no se versiona.
- [x] Separar inicializacion de tablas y carga de datos iniciales.
- [x] Crear seeds controlados para monedas, tipos y tipos de cuenta.
- [x] Preparar una estrategia simple de migraciones.
- [ ] Mejorar manejo de puerto ocupado al iniciar la API.
- [x] Ejecutar Uvicorn sin `--reload` en modo normal.

---

## Fase 2 - Dominio financiero

Objetivo: consolidar cuentas, saldos y movimientos como nucleo de la app.

- [x] Definir modelo final para movimientos financieros.
- [x] Completar campos del movimiento:
  - monto,
  - fecha,
  - ingreso o gasto,
  - cuenta,
  - tipo,
  - subtipo opcional,
  - descripcion opcional,
  - usuario propietario.
- [x] Completar CRUD de gastos/movimientos en backend.
- [x] Crear endpoints:
  - `GET /movimientos`,
  - `POST /movimientos`,
  - `GET /movimientos/{id}`,
  - `PUT /movimientos/{id}`,
  - `DELETE /movimientos/{id}`.
- [x] Agregar filtros:
  - fecha desde/hasta,
  - cuenta,
  - tipo,
  - subtipo,
  - ingreso/gasto,
  - paginacion.
- [x] Actualizar saldo de cuenta al crear un movimiento.
- [x] Recalcular saldo al editar un movimiento.
- [x] Revertir saldo al eliminar un movimiento.
- [x] Validar que cuenta, tipo y subtipo pertenezcan o sean visibles para el usuario.

---

## Fase 3 - Autenticacion y sesiones

Objetivo: tener un modelo de sesion claro y seguro para una app local.

- [x] Verificar que las contrasenas se guarden siempre hasheadas.
- [x] Evitar guardar o devolver contrasenas en respuestas de API.
- [x] Decidir estrategia definitiva:
  - token opaco guardado en SQLite,
  - o JWT local.
- [x] Cambiar `validate_token()` para devolver el usuario autenticado.
- [x] Evitar depender de una sesion global con `obtener_sesion()`.
- [x] Leer el usuario actual desde el token `Authorization: Bearer`.
- [ ] Agregar expiracion o renovacion de token.
- [x] Agregar logout confiable.
- [x] Manejar `401 Unauthorized` desde el frontend redirigiendo al login.

---

## Fase 4 - API mantenible

Objetivo: ordenar contratos HTTP y respuestas.

- [x] Revisar prefijos y nombres de rutas — plurales, sin verbos en path, health checks aparte.
- [x] Normalizar respuestas de error — handler global + handler 422, todos con `{"error", "status", "path"}`.
- [x] Crear DTOs de entrada y salida para cada recurso — `response_model` en todos los endpoints.
- [x] Evitar devolver modelos internos directamente — resuelto via `response_model` en cada endpoint.
- [x] Agregar codigos HTTP correctos:
  - `201` al crear,
  - `400` para validaciones,
  - `401` para sesion invalida,
  - `404` para recursos inexistentes.
- [x] Documentar endpoints principales — `tags` en todos los routers, `summary` en auth/movimientos, metadata en FastAPI.
- [x] Revisar CORS y limitarlo al uso local — restringido a `127.0.0.1:8000` y `localhost:8000`.

---

## Fase 5 - Frontend conectado

Objetivo: que cada pantalla trabaje con datos reales y estados claros.

- [x] Mejorar `web/js/funciones.js` como cliente API unico.
- [x] Agregar automaticamente `Authorization: Bearer <token>`.
- [x] Centralizar manejo de errores de API.
- [x] Reemplazar `alert()` por mensajes visuales consistentes.
- [x] Agregar estados de carga.
- [x] Agregar estados vacios.
- [x] Conectar dashboard con metricas reales.
- [x] Conectar pantalla de cuentas con API real.
- [x] Conectar pantalla de movimientos con API real.
- [x] Crear formulario completo para registrar movimiento.
- [x] Crear formulario para editar movimiento.
- [x] Agregar confirmacion para eliminar.
- [x] Crear componentes compartidos:
  - menu lateral,
  - selector de cuenta,
  - selector de tipo,
  - tabla de movimientos,
  - mensajes de error/exito.

---

## Fase 6 - Tests y calidad

Objetivo: poder modificar la app sin romper comportamiento basico.

- [x] Agregar `pytest`.
- [x] Crear base SQLite temporal para tests.
- [x] Testear creacion de usuario.
- [x] Testear login.
- [x] Testear creacion de cuenta.
- [x] Testear creacion de movimiento.
- [x] Testear actualizacion de saldo al crear/editar/eliminar movimientos.
- [x] Testear filtros de movimientos.
- [x] Testear que un usuario no pueda acceder a datos de otro.
- [x] Agregar script o comando para correr tests.
- [x] Agregar chequeo basico de formato/lint.

---

## Fase 7 - Reportes y analisis

Objetivo: convertir los datos registrados en informacion util.

- [x] Dashboard con saldo total por cuenta.
- [x] Ingresos del mes.
- [x] Gastos del mes.
- [ ] Flujo neto mensual.
- [x] Grafico de evolucion por mes.
- [x] Grafico por categorias.
- [ ] Filtros por cuenta y rango de fecha.
- [ ] Exportar movimientos a CSV.
- [ ] Preparar importacion desde CSV.

---

## Fase 8 - Empaquetado

Objetivo: distribuir la app como aplicacion local usable.

- [ ] Definir modo desarrollo y modo produccion.
- [ ] Empaquetar con PyInstaller u otra herramienta.
- [ ] Incluir frontend estatico en el paquete.
- [ ] Incluir inicializacion de base de datos.
- [ ] Guardar base de datos y logs en carpeta de usuario.
- [ ] Crear backup manual de la base de datos.
- [ ] Documentar instalacion y ejecucion final.

---

## Prioridad inmediata

1. Ordenar configuracion y ruta de base de datos.
2. Completar CRUD de gastos/movimientos.
3. Corregir sesiones para resolver usuario desde token.
4. Conectar pantalla de movimientos con datos reales.
5. Agregar tests del nucleo financiero.
6. Construir dashboard real.
7. Preparar empaquetado.

---

## Regla de avance

Antes de agregar funciones nuevas, cada cambio importante debe cumplir:

- Tener datos persistidos correctamente.
- Tener validaciones en backend.
- Tener manejo de error en frontend.
- No depender de datos de ejemplo.
- Mantener separada la logica de negocio de los routers.
- Poder probarse manualmente desde la app.
