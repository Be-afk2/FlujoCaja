// ==================== CONFIGURACIÓN ====================
const CONFIG = {
    baseUrl: 'http://127.0.0.1:8000/',
    timeout: 5000,
    headers: {
        'Content-Type': 'application/json'
    }
};

const TOKEN_KEY = "auth_token";

const THEME_KEY = "app_theme";

function aplicarTemaGlobal() {
    const tema = localStorage.getItem(THEME_KEY) || "dark";
    document.documentElement.classList.toggle("dark", tema === "dark");
}

aplicarTemaGlobal();

function guardarToken(token) {
    sessionStorage.setItem(TOKEN_KEY, token);
    if (localStorage.getItem("remember_session") === "true") {
        localStorage.setItem(TOKEN_KEY, token);
    }
}

function obtenerToken() {
    return sessionStorage.getItem(TOKEN_KEY) || localStorage.getItem(TOKEN_KEY);
}

function cerrarSesion() {
    sessionStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem("remember_session");
}

// ==================== UTILIDADES ====================

/**
 * Realiza una petición HTTP genérica a la API.
 * @param {string} path - Ruta de la petición (sin incluir baseUrl)
 * @param {Object} options - Opciones de configuración
 * @param {string} options.method - Método HTTP (GET, POST, PUT, DELETE)
 * @param {Object} options.data - Datos a enviar en el cuerpo (para POST/PUT)
 * @param {Object} options.headers - Headers adicionales a enviar
 * @returns {Promise<Object>} Respuesta parseada como JSON
 * @throws {Error} Si la petición falla o la respuesta no es válida
 */
const PUBLIC_PATHS = ["auth/login", "auth/register", "health"];

async function request(path, { method = 'GET', data = null, headers = {} } = {}) {
    const url = `${CONFIG.baseUrl}${path}`;
    const requestHeaders = { ...CONFIG.headers, ...headers };
    const token = obtenerToken();
    if (token && !PUBLIC_PATHS.includes(path)) {
        requestHeaders["Authorization"] = `Bearer ${token}`;
    }
    
    const options = {
        method,
        headers: requestHeaders,
        signal: AbortSignal.timeout(CONFIG.timeout)
    };

    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);
        
        if (response.status === 401 && !PUBLIC_PATHS.includes(path)) {
            cerrarSesion();
            redirigirLogin();
        }

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ 
                error: `HTTP ${response.status}: ${response.statusText}`,
                status: response.status,
                path: url
            }));
            
            const error = new Error(errorData.error || errorData.message || errorData.detail || 'Error en la petición');
            error.status = errorData.status || response.status;
            error.data = errorData;
            throw error;
        }

        return await response.json();
    } catch (error) {
        console.error(`❌ Error en petición ${method} ${url}:`, error);
        throw error;
    }
}

/**
 * Función para hacer una petición GET a una ruta específica.
 * @param {string} path - La ruta a la cual se realizará la petición.
 * @returns {Promise<Object>} - Una promesa que resuelve con la respuesta de la petición.
 */
async function get(path) {
    return request(path, { method: 'GET' });
}

/**
 * Función para hacer una petición POST a una ruta específica con datos opcionales.
 * @param {string} path - La ruta a la cual se realizará la petición.
 * @param {Object} data - Los datos que se enviarán en la petición (opcional).
 * @returns {Promise<Object>} - Una promesa que resuelve con la respuesta de la petición.
 */
async function post(path, data = {}) {
    return request(path, { method: 'POST', data });
}

/**
 * Función para hacer una petición DELETE a una ruta específica.
 * @param {string} path - La ruta a la cual se realizará la petición.
 * @returns {Promise<Object>} - Una promesa que resuelve con la respuesta de la petición.
 */
async function deleteRequest(path) {
    return request(path, { method: 'DELETE' });
}

/**
 * Función para hacer una petición PUT a una ruta específica con datos.
 * @param {string} path - La ruta a la cual se realizará la petición.
 * @param {Object} data - Los datos que se enviarán en la petición.
 * @returns {Promise<Object>} - Una promesa que resuelve con la respuesta de la petición.
 */
async function putRequest(path, data = {}) {
    return request(path, { method: 'PUT', data });
}

/**
 * Descarga un archivo binario desde la API con el token de sesión.
 * @param {string} path - Ruta del endpoint (ej: 'datos/backup').
 * @param {string} nombreArchivo - Nombre con el que se guarda el archivo.
 */
async function downloadFile(path, nombreArchivo) {
    const token = obtenerToken();
    const response = await fetch(`${CONFIG.baseUrl}${path}`, {
        headers: token ? { "Authorization": `Bearer ${token}` } : {}
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
        throw new Error(errorData.error || 'Error al descargar el archivo');
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = nombreArchivo;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

/**
 * Sube un archivo (multipart) a la API con el token de sesión.
 * @param {string} path - Ruta del endpoint (ej: 'datos/restaurar').
 * @param {File} file - Archivo a enviar.
 * @returns {Promise<Object>} Respuesta JSON.
 */
async function uploadFile(path, file) {
    const token = obtenerToken();
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${CONFIG.baseUrl}${path}`, {
        method: 'POST',
        headers: token ? { "Authorization": `Bearer ${token}` } : {},
        body: formData
    });

    if (!response.ok) {
        const errorData = await response.json().catch(() => ({ error: `HTTP ${response.status}` }));
        throw new Error(errorData.error || 'Error al subir el archivo');
    }

    return response.json();
}

// ==================== HELPERS UI / DATOS ====================

/**
 * Redirige a la pantalla de login resolviendo la ruta según la ubicación actual.
 */
function redirigirLogin() {
    const estaEnPages = window.location.pathname.includes('/pages/');
    window.location.href = estaEnPages ? 'login.html' : 'pages/login.html';
}

/**
 * Formatea un monto como moneda con un símbolo dado.
 * @param {number} monto
 * @param {string} simbolo - Símbolo de la moneda (por defecto '$').
 * @returns {string}
 */
function formatearDinero(monto, simbolo = '$') {
    const numero = Number(monto) || 0;
    return simbolo + numero.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

/**
 * Convierte fecha ISO (YYYY-MM-DD) al formato que espera la API (dd-mm-YYYY).
 * @param {string} iso - Fecha en formato YYYY-MM-DD (de input date) o vacío.
 * @returns {string|null} null si no hay fecha (la API usará hoy).
 */
function fechaParaAPI(iso) {
    if (!iso) return null;
    const [anio, mes, dia] = iso.split('-');
    return `${dia}-${mes}-${anio}`;
}

/**
 * Convierte una fecha ISO (YYYY-MM-DD) a formato de display dd/mm/YYYY.
 * @param {string} iso
 * @returns {string}
 */
function formatearFechaLegible(iso) {
    if (!iso) return '—';
    const [anio, mes, dia] = iso.split('-');
    return `${dia}/${mes}/${anio}`;
}

/**
 * Devuelve la fecha de hoy en formato ISO (YYYY-MM-DD).
 * @returns {string}
 */
function fechaHoyISO() {
    return new Date().toISOString().split('T')[0];
}

/**
 * Aplica el signo a un monto según si es ingreso o gasto.
 * @param {number} monto
 * @param {boolean} esIngreso
 * @returns {number}
 */
function montoConSigno(monto, esIngreso) {
    return esIngreso ? Math.abs(monto) : -Math.abs(monto);
}

/**
 * Alterna la apariencia de pestañas tipo Gasto/Ingreso.
 * @param {string} tabId - ID de la pestaña que se activa.
 * @param {string} activo - Clase CSS de la pestaña activa.
 * @param {string} inactivo - ID de la pestaña que se desactiva.
 */
function alternarTab(tabId, activo, inactivo) {
    document.getElementById(tabId).classList.add(activo);
    document.getElementById(tabId).classList.remove('text-slate-500');
    document.getElementById(inactivo).classList.remove(activo === 'income-active' ? 'expense-active' : 'income-active');
    document.getElementById(inactivo).classList.add('text-slate-500');
}

/**
 * Llena el selector de subtipos según el tipo seleccionado.
 * @param {string} selectId - ID del elemento select.
 * @param {number|null} tipoId - ID del tipo (o null para limpiar).
 * @param {number|null} seleccionado - ID de subtipo a preseleccionar.
 */
async function cargarSubtipos(selectId, tipoId, seleccionado = null) {
    const select = document.getElementById(selectId);
    if (!select) return;
    if (!tipoId) {
        select.innerHTML = '<option value="">Seleccionar subtipo</option>';
        return;
    }
    const resp = await get(`subtipos/?tipo_id=${tipoId}`);
    select.innerHTML = '<option value="">Seleccionar subtipo</option>' +
        (resp.subtipos || []).map(s =>
            `<option value="${s.id}" ${Number(s.id) === Number(seleccionado) ? 'selected' : ''}>${s.nombre}</option>`
        ).join('');
}

/**
 * Llena un <select> con las cuentas del usuario.
 * @param {string} selectId - ID del elemento select.
 * @param {number|null} seleccionado - ID de cuenta a preseleccionar.
 */
async function cargarSelectorCuentas(selectId, seleccionado = null) {
    const select = document.getElementById(selectId);
    if (!select) return;
    const cuentas = await get('cuentas/');
    select.innerHTML = '<option value="">Seleccionar cuenta</option>' +
        cuentas.map(c => `<option value="${c.id}" ${Number(c.id) === Number(seleccionado) ? 'selected' : ''}>${c.nombre}</option>`).join('');
    return cuentas;
}

/**
 * Llena un <select> con los tipos de movimiento.
 * @param {string} selectId - ID del elemento select.
 * @param {number|null} seleccionado - ID de tipo a preseleccionar.
 */
async function cargarSelectorTipos(selectId, seleccionado = null) {
    const select = document.getElementById(selectId);
    if (!select) return;
    const tipos = await get('tipos/?cantidad=50');
    select.innerHTML = '<option value="">Seleccionar tipo</option>' +
        tipos.map(t => `<option value="${t.id}" ${Number(t.id) === Number(seleccionado) ? 'selected' : ''}>${t.nombre}</option>`).join('');
    return tipos;
}

/**
 * Renderiza una tabla de movimientos en un <tbody>.
 * @param {string} tbodyId - ID del tbody destino.
 * @param {Array} movimientos - Lista de MovimientoResponse.
 * @param {Object} opciones
 * @param {Object} opciones.cuentasMap - Mapa id -> nombre de cuenta.
 * @param {Object} opciones.tiposMap - Mapa id -> nombre de tipo.
 * @param {Object} opciones.simbolosMap - Mapa cuenta_id -> símbolo de moneda.
 * @param {boolean} opciones.conAcciones - Si mostrar botones Editar/Eliminar.
 * @param {Function|null} opciones.onEditar - Callback con el movimiento.
 * @param {Function|null} opciones.onEliminar - Callback con el movimiento.
 */
function renderTablaMovimientos(tbodyId, movimientos, { cuentasMap = {}, tiposMap = {}, simbolosMap = {}, conAcciones = false, onEditar = null, onEliminar = null } = {}) {
    const tbody = document.getElementById(tbodyId);
    if (!tbody) return;

    if (!movimientos || movimientos.length === 0) {
        tbody.innerHTML = `<tr><td colspan="${conAcciones ? 5 : 4}" class="px-4 py-8 text-center text-slate-500">No hay movimientos registrados.</td></tr>`;
        return;
    }

    tbody.innerHTML = movimientos.map(m => {
        const esIngreso = Number(m.monto) > 0;
        const simbolo = simbolosMap[m.cuenta_id] || '$';
        const montoHtml = `<span class="font-bold ${esIngreso ? 'text-emerald-500' : 'text-rose-500'}">${esIngreso ? '+' : ''}${formatearDinero(m.monto, simbolo)}</span>`;
        const nombreTipo = tiposMap[m.tipo_id] || `Tipo ${m.tipo_id}`;
        const nombreCuenta = cuentasMap[m.cuenta_id] || `Cuenta ${m.cuenta_id}`;
        const acciones = conAcciones
            ? `<div class="flex gap-2 justify-end">
                 <button type="button" data-accion="editar" data-id="${m.id}" class="px-3 py-1 text-xs font-semibold rounded-lg bg-slate-700 hover:bg-slate-600 text-slate-200 transition-colors">Editar</button>
                 <button type="button" data-accion="eliminar" data-id="${m.id}" class="px-3 py-1 text-xs font-semibold rounded-lg bg-rose-600/20 text-rose-400 hover:bg-rose-600/30 transition-colors">Eliminar</button>
               </div>`
            : '';
        return `<tr class="border-b border-slate-800">
            <td class="px-4 py-3 text-sm text-slate-400 whitespace-nowrap">${formatearFechaLegible(m.fecha)}</td>
            <td class="px-4 py-3 text-sm text-slate-200">${nombreTipo}</td>
            <td class="px-4 py-3 text-sm text-slate-400">${nombreCuenta}</td>
            <td class="px-4 py-3 text-sm text-right">${montoHtml}</td>
            ${conAcciones ? `<td class="px-4 py-3">${acciones}</td>` : ''}
        </tr>`;
    }).join('');

    if (conAcciones) {
        tbody.querySelectorAll('[data-accion]').forEach(btn => {
            const id = Number(btn.getAttribute('data-id'));
            const mov = movimientos.find(x => Number(x.id) === id);
            btn.addEventListener('click', () => {
                if (btn.getAttribute('data-accion') === 'editar' && onEditar) onEditar(mov);
                if (btn.getAttribute('data-accion') === 'eliminar' && onEliminar) onEliminar(mov);
            });
        });
    }
}

