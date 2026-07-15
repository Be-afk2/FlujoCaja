// ==================== VALIDACIÓN DE FORMULARIO ====================

const CAMPOS_REQUERIDOS = {
    username: {
        id: 'inputUsername',
        nombre: 'Nombre de usuario'
    },
    password: {
        id: 'inputPassword',
        nombre: 'Contraseña'
    }
};

const CLASE_ERROR = 'border-red-500 focus:ring-red-500/50 focus:border-red-500';
const CLASE_NORMAL = 'border-slate-200 dark:border-slate-700 focus:ring-primary/20 focus:border-primary';

// ==================== VALIDACIÓN ====================

/**
 * Obtiene los valores de los campos del formulario.
 * @returns {Object} Objeto con los valores de username, password y recordar
 */
function obtenerValoresFormulario() {
    return {
        username: document.getElementById(CAMPOS_REQUERIDOS.username.id).value.trim(),
        password: document.getElementById(CAMPOS_REQUERIDOS.password.id).value.trim(),
        recordar: document.getElementById('inputRecordar').checked
    };
}

// ==================== FUNCIONES DE LOGIN ====================

/**
 * Realiza el login del usuario.
 * Valida que todos los campos estén llenos antes de enviar.
 */
async function Login() {
    // Validar formulario
    if (!validarFormulario()) {
        console.warn('⚠ Formulario incompleto. Completa todos los campos.');
        return;
    }

    const valores = obtenerValoresFormulario();
    
    try {
        console.log('📤 Enviando solicitud de login...');
        const response = await post('auth/login', {
            name: valores.username,
            passw: valores.password,
            recordar: valores.recordar
        });
        console.log('✓ Respuesta recibida:', response);
        if (response) {
            console.log('✓ Login exitoso:', response);
            
            // Guardar token si existe
            if (response.token) {
                localStorage.setItem("remember_session", valores.recordar);
                guardarToken(response.token);
                console.log('✓ Token guardado');
            }

            // Mostrar mensaje de éxito
            alert('✓ Sesión iniciada exitosamente');
            
            // Redirigir al panel de control
            setTimeout(() => {
                window.location.href = './panelControl.html';
            }, 500);
        }
    } catch (error) {
        console.error('✗ Error al iniciar sesión:', error);
        
        // Extraer mensaje de error detallado
        let mensajeError = 'Error al iniciar sesión';
        
        // Si el error tiene datos de respuesta API
        if (error.data) {
            console.error('📋 Datos del error:', error.data);
            mensajeError = error.data.error || error.message || mensajeError;
        }
        // Si el error tiene mensaje
        else if (error.message) {
            mensajeError = error.message;
        }
        
        // Validar errores específicos por código de estado
        if (error.status === 404) {
            mensajeError = 'Usuario o contraseña incorrectos';
            console.warn('⚠ Intento de login fallido: credenciales inválidas');
        } else if (error.status === 400) {
            mensajeError = 'Solicitud inválida. Intenta nuevamente.';
        } else if (error.status === 500) {
            mensajeError = 'Error del servidor. Intenta más tarde.';
        } else if (error.message.includes('timeout') || error.message.includes('Timeout')) {
            mensajeError = 'Tiempo de conexión agotado. Intenta nuevamente.';
        }
        
        alert(`✗ ${mensajeError}`);
    }
}

// ==================== INICIALIZACIÓN ====================

/**
 * Inicializa los event listeners del formulario.
 */
function initLoginForm() {
    // Botón login
    const btnLogin = document.getElementById('btnLogin');
    if (btnLogin) {
        btnLogin.addEventListener('click', Login);
    }

    // Botón toggle password
    const btnTogglePassword = document.getElementById('btnTogglePassword');
    if (btnTogglePassword) {
        btnTogglePassword.addEventListener('click', (e) => {
            e.preventDefault();
            togglePasswordVisibility();
        });
    }

    // Listeners para limpiar errores al escribir
    Object.keys(CAMPOS_REQUERIDOS).forEach(fieldKey => {
        limpiarErrorAlEscribir(fieldKey);
    });

    // Permitir submit con Enter
    const formLogin = document.getElementById('formLogin');
    if (formLogin) {
        formLogin.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                Login();
            }
        });
    }

    console.log('✓ Login.js inicializado correctamente');
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initLoginForm);
} else {
    initLoginForm();
}
