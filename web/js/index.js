
// ==================== CONSTANTES ====================
const ROUTES = {
    PANEL_CONTROL: "pages/panelControl.html",
    LOGIN: "pages/login.html",
};

const API_ENDPOINTS = {
    AUTH_CHECK: "auth/",
    TOKEN_LIFE: "health/token",
};


// ==================== INICIALIZACIÓN ====================
document.addEventListener("DOMContentLoaded", async () => {
    mostrarInfoDebug()
    try {
        const sesionValida = await validarYRedireccionarSesion();
        if (!sesionValida) {
            redirigir(ROUTES.LOGIN);
        }
    } catch (error) {
        console.error("Error en validación de sesión:", error);
        redirigir(ROUTES.LOGIN);
    }
});


// ==================== GESTIÓN DE SESIÓN ====================

/**
 * Valida la sesión y redirige al panel de control si es válida.
 * Verifica primero el almacenamiento local, luego la API.
 * @returns {Promise<boolean>} - True si la sesión es válida
 */
async function validarYRedireccionarSesion() {
    // Verificar sesión local primero
    if (verificarSesionLocal()) {
        console.log("✓ Sesión local activa");
        
        // Validar que el token siga siendo válido en la API
        if (await verificarTokenLife()) {
            redirigir(ROUTES.PANEL_CONTROL);
            return true;
        }
    }

    // Si no hay sesión local, verificar en la API
    console.log("⚠ No hay sesión local, verificando API...");
    if (await verificarSesionApi()) {
        console.log("✓ Sesión API activa");
        redirigir(ROUTES.PANEL_CONTROL);
        return true;
    }

    console.log("✗ No hay sesión activa en ningún lugar");
    return false;
}

/**
 * Verifica si hay sesión recordada en localStorage.
 * @returns {boolean} - True si hay sesión recordada
 */
function verificarSesionLocal() {
    return localStorage.getItem("remember_session") === "true";
}

/**
 * Verifica la sesión contra la API.
 * @returns {Promise<boolean>} - True si la sesión es válida en la API
 */
async function verificarSesionApi() {
    try {
        const sesion = await get(API_ENDPOINTS.AUTH_CHECK);
        
        if (sesion?.token) {
            guardarSesion(sesion.token);
            return true;
        }
        return false;
    } catch (error) {
        console.error("Error verificando sesión en API:", error);
        return false;
    }
}

/**
 * Verifica que el token sea válido en la API.
 * @returns {Promise<boolean>} - True si el token es válido
 */
async function verificarTokenLife() {
    try {
        const token = obtenerToken();
        
        if (!token) {
            console.warn("⚠ Token no encontrado");
            cerrarSesion();
            return false;
        }

        const response = await get(API_ENDPOINTS.TOKEN_LIFE);
        console.log("Respuesta de vida del token:", response);
        if (!response?.ok) {
            console.warn("⚠ Token inválido o expirado");
            cerrarSesion();
            return false;
        }

        return true;
    } catch (error) {
        console.error("Error verificando vida del token:", error);
        cerrarSesion();
        return false;
    }
}

function guardarSesion(token) {
    localStorage.setItem("remember_session", "true");
    guardarToken(token);
    console.log("✓ Sesión guardada");
}


// ==================== UTILIDADES ====================

/**
 * Redirige a la URL especificada.
 * @param {string} url - La URL a la que redirigir
 */
function redirigir(url) {
    window.location.href = url;
}

/**
 * Muestra información de depuración sobre la sesión.
 */
function mostrarInfoDebug() {
    console.group("📊 Información de Sesión");
    console.log("Token:", obtenerToken() || "No disponible");
    console.log("Sesión recordada:", localStorage.getItem("remember_session"));
    console.log("Memoria:", performance.memory || "No disponible");
    console.groupEnd();
}

