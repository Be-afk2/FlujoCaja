// ==================== CONFIGURACIÓN ====================
const CONFIG = {
    baseUrl: 'http://127.0.0.1:8000/',
    timeout: 5000,
    headers: {
        'Content-Type': 'application/json'
    }
};

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
async function request(path, { method = 'GET', data = null, headers = {} } = {}) {
    const url = `${CONFIG.baseUrl}${path}`;
    const requestHeaders = { ...CONFIG.headers, ...headers };
    
    const options = {
        method,
        headers: requestHeaders,
        signal: AbortSignal.timeout(CONFIG.timeout)
    };

    // Agregar body solo si hay datos
    if (data && (method === 'POST' || method === 'PUT')) {
        options.body = JSON.stringify(data);
    }

    try {
        const response = await fetch(url, options);
        
        // Validar que la respuesta sea exitosa
        if (!response.ok) {
            const error = await response.json().catch(() => ({ 
                message: `HTTP ${response.status}: ${response.statusText}` 
            }));
            throw new Error(error.message || error.detail || 'Error en la petición');
        }

        return await response.json();
    } catch (error) {
        console.error(`❌ Error en petición ${method} ${url}:`, error);
        throw error;
    }
}

/**
 * Función para hacer una petición GET a una ruta específica con datos opcionales.
 * @param {string} path - La ruta a la cual se realizará la petición.
 * @param {Object} data - Los datos que se enviarán en la petición (opcional).
 * @returns {Promise<Object>} - Una promesa que resuelve con la respuesta de la petición.
 */
async function get(path, data = {}) {
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

// ==================== EVENT LISTENERS ====================

/**
 * Inicializa los listeners de eventos cuando el DOM esté cargado.
 */
function initEventListeners() {
    const btnGet = document.getElementById('btnGet');
    if (btnGet) {
        btnGet.addEventListener('click', handleGetButtonClick);
    }

    const btnPost = document.getElementById('btnPost');
    if (btnPost) {
        btnPost.addEventListener('click', handlePostButtonClick);
    }
}

/**
 * Manejador para el botón GET.
 */
async function handleGetButtonClick() {
    try {
        const response = await get('auth/life');
        console.log('✓ Respuesta GET:', response);
    } catch (error) {
        console.error('✗ Error en GET:', error.message);
    }
}

/**
 * Manejador para el botón POST.
 */
async function handlePostButtonClick() {
    try {
        const data = { clave: 'valor' };
        const response = await post('ruta/especifica', data);
        console.log('✓ Respuesta POST:', response);
    } catch (error) {
        console.error('✗ Error en POST:', error.message);
    }
}

// ==================== INICIALIZACIÓN ====================

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initEventListeners);
} else {
    initEventListeners();
}

