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

## Fase 1 - Configuracion y base tecnica

Objetivo: hacer que la app arranque y persista datos de manera predecible.

- [x] Crear un modulo de configuracion centralizado.
- [x] Mover valores hardcodeados a configuracion:
  - host API,
  - puerto API,
  - ruta de base de datos,
  - modo debug,
  - timeout del frontend.
- [ ] Mover `database.db` fuera del repo, idealmente a `%APPDATA%/FlujoCaja/`.
- [ ] Asegurar que `database.db` no se versiona.
- [x] Separar inicializacion de tablas y carga de datos iniciales.
- [x] Crear seeds controlados para monedas, tipos y tipos de cuenta.
- [x] Preparar una estrategia simple de migraciones.
- [ ] Mejorar manejo de puerto ocupado al iniciar la API.
- [x] Ejecutar Uvicorn sin `--reload` en modo normal.

---

## Fase 2 - Dominio financiero

Objetivo: consolidar cuentas, saldos y movimientos como nucleo de la app.

- [ ] Definir modelo final para movimientos financieros.
- [ ] Completar campos del movimiento:
  - monto,
  - fecha,
  - ingreso o gasto,
  - cuenta,
  - tipo,
  - subtipo opcional,
  - descripcion opcional,
  - usuario propietario.
- [ ] Completar CRUD de gastos/movimientos en backend.
- [ ] Crear endpoints:
  - `GET /movimientos`,
  - `POST /movimientos`,
  - `GET /movimientos/{id}`,
  - `PUT /movimientos/{id}`,
  - `DELETE /movimientos/{id}`.
- [ ] Agregar filtros:
  - fecha desde/hasta,
  - cuenta,
  - tipo,
  - subtipo,
  - ingreso/gasto,
  - paginacion.
- [ ] Actualizar saldo de cuenta al crear un movimiento.
- [ ] Recalcular saldo al editar un movimiento.
- [ ] Revertir saldo al eliminar un movimiento.
- [ ] Validar que cuenta, tipo y subtipo pertenezcan o sean visibles para el usuario.
- [ ] Agregar una capa de servicios para reglas de negocio.

---

## Fase 3 - Autenticacion y sesiones

Objetivo: tener un modelo de sesion claro y seguro para una app local.

- [ ] Verificar que las contrasenas se guarden siempre hasheadas.
- [ ] Evitar guardar o devolver contrasenas en respuestas de API.
- [ ] Decidir estrategia definitiva:
  - token opaco guardado en SQLite,
  - o JWT local.
- [ ] Cambiar `validate_token()` para devolver el usuario autenticado.
- [ ] Evitar depender de una sesion global con `obtener_sesion()`.
- [ ] Leer el usuario actual desde el token `Authorization: Bearer`.
- [ ] Agregar expiracion o renovacion de token.
- [ ] Agregar logout confiable.
- [ ] Manejar `401 Unauthorized` desde el frontend redirigiendo al login.

---

## Fase 4 - API mantenible

Objetivo: ordenar contratos HTTP y respuestas.

- [ ] Revisar prefijos y nombres de rutas.
- [ ] Normalizar respuestas de error.
- [ ] Crear DTOs de entrada y salida para cada recurso.
- [ ] Evitar devolver modelos internos directamente cuando no convenga.
- [ ] Agregar codigos HTTP correctos:
  - `201` al crear,
  - `400` para validaciones,
  - `401` para sesion invalida,
  - `404` para recursos inexistentes.
- [ ] Documentar endpoints principales con OpenAPI.
- [ ] Revisar CORS y limitarlo al uso local si corresponde.

---

## Fase 5 - Frontend conectado

Objetivo: que cada pantalla trabaje con datos reales y estados claros.

- [ ] Mejorar `web/js/funciones.js` como cliente API unico.
- [ ] Agregar automaticamente `Authorization: Bearer <token>`.
- [ ] Centralizar manejo de errores de API.
- [ ] Reemplazar `alert()` por mensajes visuales consistentes.
- [ ] Agregar estados de carga.
- [ ] Agregar estados vacios.
- [ ] Conectar dashboard con metricas reales.
- [ ] Conectar pantalla de cuentas con API real.
- [ ] Conectar pantalla de movimientos con API real.
- [ ] Crear formulario completo para registrar movimiento.
- [ ] Crear formulario para editar movimiento.
- [ ] Agregar confirmacion para eliminar.
- [ ] Crear componentes compartidos:
  - menu lateral,
  - selector de cuenta,
  - selector de tipo,
  - tabla de movimientos,
  - mensajes de error/exito.

---

## Fase 6 - Tests y calidad

Objetivo: poder modificar la app sin romper comportamiento basico.

- [ ] Agregar `pytest`.
- [ ] Crear base SQLite temporal para tests.
- [ ] Testear creacion de usuario.
- [ ] Testear login.
- [ ] Testear creacion de cuenta.
- [ ] Testear creacion de movimiento.
- [ ] Testear actualizacion de saldo al crear/editar/eliminar movimientos.
- [ ] Testear filtros de movimientos.
- [ ] Testear que un usuario no pueda acceder a datos de otro.
- [ ] Agregar script o comando para correr tests.
- [ ] Agregar chequeo basico de formato/lint.

---

## Fase 7 - Reportes y analisis

Objetivo: convertir los datos registrados en informacion util.

- [ ] Dashboard con saldo total por cuenta.
- [ ] Ingresos del mes.
- [ ] Gastos del mes.
- [ ] Flujo neto mensual.
- [ ] Grafico de evolucion por mes.
- [ ] Grafico por categorias.
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
