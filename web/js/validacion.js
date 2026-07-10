function validarCampo(fieldKey, value) {
    if (!value || value.length === 0) {
        destacarError(fieldKey);
        return false;
    }
    limpiarError(fieldKey);
    return true;
}

function destacarError(fieldKey) {
    const inputElement = document.getElementById(CAMPOS_REQUERIDOS[fieldKey].id);
    if (inputElement) {
        inputElement.classList.remove(...CLASE_NORMAL.split(' '));
        inputElement.classList.add(...CLASE_ERROR.split(' '));
        inputElement.setAttribute('aria-invalid', 'true');
    }
}

function limpiarError(fieldKey) {
    const inputElement = document.getElementById(CAMPOS_REQUERIDOS[fieldKey].id);
    if (inputElement) {
        inputElement.classList.remove(...CLASE_ERROR.split(' '));
        inputElement.classList.add(...CLASE_NORMAL.split(' '));
        inputElement.setAttribute('aria-invalid', 'false');
    }
}

function validarFormulario() {
    const valores = obtenerValoresFormulario();
    let esValido = true;

    for (const [key, field] of Object.entries(CAMPOS_REQUERIDOS)) {
        if (!validarCampo(key, valores[key])) {
            esValido = false;
        }
    }

    return esValido;
}

function limpiarErrorAlEscribir(fieldKey) {
    const inputElement = document.getElementById(CAMPOS_REQUERIDOS[fieldKey].id);
    if (inputElement) {
        inputElement.addEventListener('input', () => {
            limpiarError(fieldKey);
        });
    }
}

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
