
// ==================== VALIDACIÓN DE FORMULARIO ====================

const CAMPOS_REQUERIDOS = {
    nombre: {
        id: 'inputNombre',
        nombre: 'Nombre'
    },
    apellido: {
        id: 'inputApellido',
        nombre: 'Apellido'
    },
    password: {
        id: 'inputPassword',
        nombre: 'Contraseña'
    }
};

const CLASE_ERROR = 'border-red-500 focus:ring-red-500/50 focus:border-red-500';
const CLASE_NORMAL = 'border-navy-light focus:ring-primary/50 focus:border-primary';

/**
 * Obtiene los valores de los campos del formulario.
 * @returns {Object} Objeto con los valores de nombre, apellido y password
 */
function obtenerValoresFormulario() {
    return {
        nombre: document.getElementById(CAMPOS_REQUERIDOS.nombre.id).value.trim(),
        apellido: document.getElementById(CAMPOS_REQUERIDOS.apellido.id).value.trim(),
        password: document.getElementById(CAMPOS_REQUERIDOS.password.id).value.trim()
    };
}

/**
 * Crea una cuenta con los datos del formulario.
 * Valida que todos los campos estén llenos antes de enviar.
 */
async function crearCuenta() {
    // Validar formulario
    if (!validarFormulario()) {
        console.warn('⚠ Formulario incompleto. Completa todos los campos.');
        return;
    }

    const valores = obtenerValoresFormulario();
    
    try {
        console.log('📤 Enviando solicitud de registro...');
        const response = await post('auth/create', {
            name: valores.nombre,
            apellido: valores.apellido,
            passw: valores.password
        });

        if (response) {
            console.log('✓ Cuenta creada exitosamente:', response);
            // Aquí puedes redirigir al usuario o mostrar un mensaje de éxito
            alert('✓ Cuenta creada exitosamente');
            // Limpiar formulario
            document.getElementById('formCrearCuenta').reset();
        }
    } catch (error) {
        console.error('✗ Error al crear cuenta:', error);
        alert(`✗ Error: ${error.message}`);
    }
}

// ==================== INICIALIZACIÓN ====================

/**
 * Inicializa los event listeners del formulario.
 */
function initCrearCuentaForm() {
    // Botón crear cuenta
    const btnCrearCuenta = document.getElementById('btnCrearCuenta');
    if (btnCrearCuenta) {
        btnCrearCuenta.addEventListener('click', crearCuenta);
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
}

// Inicializar cuando el DOM esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCrearCuentaForm);
} else {
    initCrearCuentaForm();
}