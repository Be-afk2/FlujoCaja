
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
 * Valida que un campo no esté vacío.
 * @param {string} fieldKey - Clave del campo a validar
 * @param {string} value - Valor del campo
 * @returns {boolean} True si es válido, False en caso contrario
 */
function validarCampo(fieldKey, value) {
    if (!value || value.length === 0) {
        destacarError(fieldKey);
        return false;
    }
    limpiarError(fieldKey);
    return true;
}

/**
 * Destaca un campo con error (borde rojo).
 * @param {string} fieldKey - Clave del campo a destacar
 */
function destacarError(fieldKey) {
    const inputElement = document.getElementById(CAMPOS_REQUERIDOS[fieldKey].id);
    if (inputElement) {
        inputElement.classList.remove(...CLASE_NORMAL.split(' '));
        inputElement.classList.add(...CLASE_ERROR.split(' '));
        inputElement.setAttribute('aria-invalid', 'true');
    }
}

/**
 * Limpia el estado de error de un campo.
 * @param {string} fieldKey - Clave del campo a limpiar
 */
function limpiarError(fieldKey) {
    const inputElement = document.getElementById(CAMPOS_REQUERIDOS[fieldKey].id);
    if (inputElement) {
        inputElement.classList.remove(...CLASE_ERROR.split(' '));
        inputElement.classList.add(...CLASE_NORMAL.split(' '));
        inputElement.setAttribute('aria-invalid', 'false');
    }
}

/**
 * Valida todos los campos del formulario.
 * @returns {boolean} True si todos los campos son válidos, False en caso contrario
 */
function validarFormulario() {
    const valores = obtenerValoresFormulario();
    let esValido = true;

    // Validar cada campo requerido
    for (const [key, field] of Object.entries(CAMPOS_REQUERIDOS)) {
        if (!validarCampo(key, valores[key])) {
            esValido = false;
        }
    }

    return esValido;
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

/**
 * Alterna la visibilidad de la contraseña.
 */
function togglePasswordVisibility() {
    const inputPassword = document.getElementById(CAMPOS_REQUERIDOS.password.id);
    const btnToggle = document.getElementById('btnTogglePassword');
    
    if (inputPassword.type === 'password') {
        inputPassword.type = 'text';
        btnToggle.innerHTML = '<span class="material-symbols-outlined text-xl">visibility_off</span>';
    } else {
        inputPassword.type = 'password';
        btnToggle.innerHTML = '<span class="material-symbols-outlined text-xl">visibility</span>';
    }
}

/**
 * Limpia los errores cuando el usuario comienza a escribir en un campo.
 */
function limpiarErrorAlEscribir(fieldKey) {
    const inputElement = document.getElementById(CAMPOS_REQUERIDOS[fieldKey].id);
    if (inputElement) {
        inputElement.addEventListener('input', () => {
            limpiarError(fieldKey);
        });
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