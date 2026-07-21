// ==================== CONFIGURACIÓN ====================
const CONFIG = {
    baseUrl: 'http://127.0.0.1:8000/',
    timeout: 5000,
    headers: {
        'Content-Type': 'application/json'
    }
};

const TOKEN_KEY = "auth_token";

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
const PUBLIC_PATHS = ["auth/", "auth/login", "auth/register", "health"];

async function request(path, { method = 'GET', data = null, headers = {} } = {}) {
    const url = `${CONFIG.baseUrl}${path}`;
    const requestHeaders = { ...CONFIG.headers, ...headers };
    console.log("-------------------url-------------------")
    console.log(url)
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
        
        if (response.status === 401) {
            cerrarSesion();
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

