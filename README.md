# Flujo de Caja

## 📌 Descripción general

**Flujo de Caja** es un proyecto personal desarrollado en **Python**, orientado al **control detallado de gastos personales**. Surge como una evolución natural de un registro que inicialmente se llevaba en Excel y que, con el tiempo, se volvió difícil de mantener y escalar.

El proyecto se encuentra actualmente en **estado de prototipo en desarrollo**, con foco en construir una base sólida y extensible antes de avanzar hacia una interfaz más compleja.

---

## 🎯 Motivación

Las aplicaciones bancarias suelen entregar información limitada o poco flexible sobre los gastos. Este proyecto nace de la necesidad de:

* Llevar un **registro detallado y personalizado** de los gastos
* Clasificar los gastos por **tipos definidos por el usuario**
* Visualizar de mejor forma el **flujo de caja personal**
* Reemplazar registros en papel o planillas que crecen sin control

---

## ⚙️ ¿Qué hace este proyecto?

Permite llevar un control detallado de:

* Gastos personales
* Tipos de gastos personalizables
* Usuarios del sistema

El sistema organiza la información en **tablas y, a futuro, gráficos**, facilitando el análisis de en qué se gasta más dinero y cómo evoluciona el flujo de caja en el tiempo.

Está pensado tanto para **uso personal** como para personas que disfrutan tener un **control financiero detallado**.

---

## 🧱 Tecnologías y stack

* **Lenguaje:** Python
* **Base de datos:** SQLite
* **Librerías:**

  * `questionary` (interacción por consola)
  * `rich` (mejor visualización en consola)
* **Ejecución:** Local

El proyecto está organizado en **repositorios separados**, siguiendo una aproximación a **microservicios**, aunque por el momento todos los componentes se ejecutan de forma local.

---

## 🏗️ Arquitectura y diseño

* Arquitectura: **Microservicios (en evolución)**
* Organización por capas:

  * Controladores
  * Interfaz por consola (CLI)

Actualmente no existe comunicación externa entre componentes. La separación está pensada para facilitar una futura transición hacia una **API** y nuevas interfaces.

---

## ▶️ Instalación y ejecución

### Requisitos

* Python instalado

### Instalación

Por el momento, basta con **clonar o copiar el proyecto**.

En versiones futuras se planea generar un **build en un solo archivo ejecutable**.

### Dependencias

```bash
pip install -r requirements.txt
```

### Ejecución

```bash
python app.py
```

---

## 🖥️ Uso

La aplicación funciona mediante **interfaz por consola (CLI)**.

### Flujo general

1. Ejecutar la aplicación
2. Si existe un usuario:

   * Iniciar sesión
   * O iniciar automáticamente si está activada la opción de recordar usuario
3. Si no existe un usuario:

   * Crear el primer usuario
4. Una vez logueado, se muestra un menú principal con:

   * **Gastos**
   * **Tipos de gastos**
   * **Configuración**
   * **Salir**

### Opciones del menú

* **Gastos**

  * Registrar gastos
  * Asociar cada gasto a un tipo
* **Tipos de gastos**

  * Crear, editar y eliminar tipos de gastos
* **Configuración**

  * Crear usuarios alternos
  * Activar/desactivar recordar usuario
* **Salir**

---

## ✨ Características actuales

* Gestión de usuarios
* Registro de gastos
* Clasificación por tipos de gastos
* Interfaz por consola mejorada

### Pendiente de implementación

* CRUD completo de gastos
* Visualización mediante gráficos

---

## 🛣️ Roadmap

* Implementación de una **API**
* Nueva interfaz construida sobre la API (web u otra)
* Mejoras en visualización de datos

---

## 🤝 Contribuciones

Por el momento **no se aceptan contribuciones directas**.

Se valoran ideas, sugerencias y mejoras conceptuales.

---

## 📄 Licencia

Proyecto **privado**, sin licencia pública definida por ahora.

---

## 📝 Nota final

Este proyecto está siendo desarrollado con un enfoque **personal pero profesional**, buscando buenas prácticas y una arquitectura que permita crecer y escalar en el futuro.
