// ==================== AJUSTES ====================

const THEME_KEY = 'app_theme';

// ==================== TEMA ====================

function aplicarTema(tema) {
    document.documentElement.classList.toggle('dark', tema === 'dark');
    const btnClaro = document.getElementById('btnTemaClaro');
    const btnOscuro = document.getElementById('btnTemaOscuro');
    if (!btnClaro || !btnOscuro) return;

    const activo = 'bg-slate-800 text-white';
    const inactivo = 'text-slate-400';
    btnClaro.className = `flex-1 py-2 rounded-lg font-medium flex items-center justify-center gap-2 transition-all ${tema === 'light' ? activo : inactivo}`;
    btnOscuro.className = `flex-1 py-2 rounded-lg font-medium flex items-center justify-center gap-2 transition-all ${tema === 'dark' ? activo : inactivo}`;
}

function initTema() {
    const temaGuardado = localStorage.getItem(THEME_KEY) || 'dark';
    aplicarTema(temaGuardado);

    document.getElementById('btnTemaClaro')?.addEventListener('click', () => {
        localStorage.setItem(THEME_KEY, 'light');
        aplicarTema('light');
    });
    document.getElementById('btnTemaOscuro')?.addEventListener('click', () => {
        localStorage.setItem(THEME_KEY, 'dark');
        aplicarTema('dark');
    });
}

// ==================== PERFIL ====================

async function cargarPerfil() {
    const inputNombre = document.getElementById('inputNombre');
    const inputApellido = document.getElementById('inputApellido');
    if (!inputNombre) return;

    try {
        const perfil = await get('auth/me');
        if (perfil?.name) {
            inputNombre.value = perfil.name;
        }
        if (perfil?.apellido) {
            inputApellido.value = perfil.apellido;
        }
    } catch (error) {
        console.warn('No se pudo cargar el perfil:', error.message);
    }
}

async function guardarPerfil() {
    const inputNombre = document.getElementById('inputNombre');
    const inputApellido = document.getElementById('inputApellido');
    const btn = document.getElementById('btnGuardarPerfil');
    if (!inputNombre || !btn) return;

    const nombre = inputNombre.value.trim();
    const apellido = inputApellido.value.trim();
    if (!nombre || !apellido) {
        mostrarNotificacion('Completa nombre y apellido.', 'warning');
        return;
    }

    btn.disabled = true;
    btn.textContent = 'Guardando...';

    try {
        await putRequest('auth/me', { name: nombre, apellido });
        mostrarNotificacion('Perfil actualizado correctamente');
        cargarNombreUsuario();
    } catch (error) {
        console.error('Error guardando perfil:', error);
        mostrarNotificacion(error.message || 'Error al guardar el perfil', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Guardar Cambios';
    }
}

// ==================== CONTRASEÑA ====================

async function cambiarContrasena() {
    const btn = document.getElementById('btnCambiarPassword');
    if (!btn) return;

    const actual = document.getElementById('inputPasswActual').value;
    const nueva = document.getElementById('inputPasswNueva').value;
    const confirmar = document.getElementById('inputPasswConfirmar').value;

    if (!actual || !nueva || !confirmar) {
        mostrarNotificacion('Completa todos los campos.', 'warning');
        return;
    }
    if (nueva !== confirmar) {
        mostrarNotificacion('Las contraseñas nuevas no coinciden.', 'warning');
        return;
    }
    if (nueva.length < 4) {
        mostrarNotificacion('La contraseña debe tener al menos 4 caracteres.', 'warning');
        return;
    }

    btn.disabled = true;
    btn.textContent = 'Cambiando...';

    try {
        await putRequest('auth/me/password', { passw_actual: actual, passw_nueva: nueva });
        mostrarNotificacion('Contraseña actualizada correctamente');
        document.getElementById('formPassword').reset();
    } catch (error) {
        console.error('Error cambiando contraseña:', error);
        mostrarNotificacion(error.message || 'Error al cambiar la contraseña', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Cambiar Contraseña';
    }
}

// ==================== MONEDAS ====================

async function cargarMonedas() {
    const tbody = document.getElementById('monedas-tbody');
    if (!tbody) return;

    try {
        const monedas = await get('monedas/');
        if (!monedas || monedas.length === 0) {
            tbody.innerHTML = '<tr><td colspan="2" class="py-8 text-center text-slate-500">Aún no hay monedas registradas.</td></tr>';
            return;
        }
        tbody.innerHTML = monedas.map(m => `
            <tr class="border-b border-border-dark/50 hover:bg-slate-800 transition-colors">
                <td class="py-3 pr-4 text-slate-200">${m.nombre}</td>
                <td class="py-3 pr-4 text-slate-400">${m.simbolo}</td>
            </tr>
        `).join('');
    } catch (error) {
        console.error('Error cargando monedas:', error);
        tbody.innerHTML = '<tr><td colspan="2" class="py-8 text-center text-slate-500">Error al cargar las monedas.</td></tr>';
    }
}

function initModalMoneda() {
    const modal = document.getElementById('modalMoneda');
    const btnNueva = document.getElementById('btnNuevaMoneda');
    const btnGuardar = document.getElementById('btnGuardarMoneda');
    if (!modal || !btnNueva || !btnGuardar) return;

    const abrir = () => {
        document.getElementById('inputMonedaNombre').value = '';
        document.getElementById('inputMonedaSimbolo').value = '';
        modal.classList.remove('hidden');
        document.getElementById('inputMonedaNombre').focus();
    };
    const cerrar = () => modal.classList.add('hidden');

    btnNueva.addEventListener('click', abrir);
    modal.querySelectorAll('[data-cerrar-moneda]').forEach(el => el.addEventListener('click', cerrar));
    modal.addEventListener('click', (e) => { if (e.target === modal) cerrar(); });

    btnGuardar.addEventListener('click', async () => {
        const nombre = document.getElementById('inputMonedaNombre').value.trim();
        const simbolo = document.getElementById('inputMonedaSimbolo').value.trim();
        if (!nombre || !simbolo) {
            mostrarNotificacion('Completa nombre y símbolo.', 'warning');
            return;
        }

        try {
            await post('monedas/', { nombre, simbolo });
            mostrarNotificacion('Moneda creada correctamente');
            cerrar();
            cargarMonedas();
        } catch (error) {
            mostrarNotificacion(error.message || 'Error al crear la moneda', 'error');
        }
    });
}

// ==================== SESIÓN ====================

function initCerrarSesion() {
    const btn = document.getElementById('btnCerrarSesion');
    const modal = document.getElementById('modalCerrarSesion');
    const btnConfirmar = document.getElementById('btnConfirmarSesion');
    if (!btn || !modal || !btnConfirmar) return;

    const abrir = () => modal.classList.remove('hidden');
    const cerrar = () => modal.classList.add('hidden');

    btn.addEventListener('click', abrir);
    modal.querySelectorAll('[data-cerrar-sesion-modal]').forEach(el => el.addEventListener('click', cerrar));
    modal.addEventListener('click', (e) => { if (e.target === modal) cerrar(); });

    btnConfirmar.addEventListener('click', async () => {
        btnConfirmar.disabled = true;
        btnConfirmar.textContent = 'Cerrando...';

        try {
            await deleteRequest('auth');
        } catch (error) {
            console.warn('Error al cerrar sesión en el servidor:', error.message);
        }

        cerrarSesion();
        window.location.href = 'login.html';
    });
}

// ==================== ACERCA DE ====================

async function cargarAcercaDe() {
    const versionEl = document.getElementById('about-version');
    const dbEl = document.getElementById('about-db');
    if (!versionEl) return;

    try {
        const info = await get('health');
        versionEl.textContent = info?.version || '—';
        dbEl.textContent = info?.database || '—';
    } catch (error) {
        console.warn('No se pudo cargar la información del sistema:', error.message);
    }
}

// ==================== DATOS (BACKUP / RESTAURAR) ====================

async function backupDb() {
    const btn = document.getElementById('btnBackup');
    if (!btn) return;

    btn.disabled = true;
    btn.textContent = 'Generando backup...';

    try {
        await downloadFile('datos/backup', 'flujocaja_backup.db');
        mostrarNotificacion('Backup descargado correctamente');
    } catch (error) {
        console.error('Error generando backup:', error);
        mostrarNotificacion(error.message || 'Error al generar el backup', 'error');
    } finally {
        btn.disabled = false;
        btn.textContent = 'Backup de base de datos';
    }
}

function initRestaurarDb() {
    const btn = document.getElementById('btnRestaurar');
    const input = document.getElementById('inputRestaurarDb');
    const modal = document.getElementById('modalRestaurar');
    const btnConfirmar = document.getElementById('btnConfirmarRestaurar');
    if (!btn || !input || !modal || !btnConfirmar) return;

    const cerrar = () => modal.classList.add('hidden');

    btn.addEventListener('click', () => input.click());

    input.addEventListener('change', () => {
        if (input.files && input.files[0]) {
            modal.classList.remove('hidden');
        }
    });

    modal.querySelectorAll('[data-cerrar-restaurar]').forEach(el => el.addEventListener('click', cerrar));
    modal.addEventListener('click', (e) => { if (e.target === modal) cerrar(); });

    btnConfirmar.addEventListener('click', async () => {
        const file = input.files[0];
        if (!file) {
            cerrar();
            return;
        }

        btnConfirmar.disabled = true;
        btnConfirmar.textContent = 'Restaurando...';

        try {
            await uploadFile('datos/restaurar', file);
            mostrarNotificacion('Base de datos restaurada correctamente. Reinicia la aplicación.', 'warning');
            cerrar();
            input.value = '';
        } catch (error) {
            console.error('Error restaurando base de datos:', error);
            mostrarNotificacion(error.message || 'Error al restaurar la base de datos', 'error');
        } finally {
            btnConfirmar.disabled = false;
            btnConfirmar.textContent = 'Restaurar';
        }
    });
}

// ==================== INICIALIZACIÓN ====================

document.addEventListener('DOMContentLoaded', () => {
    initTema();
    cargarPerfil();
    cargarMonedas();
    initModalMoneda();
    initCerrarSesion();
    cargarAcercaDe();
    initRestaurarDb();

    document.getElementById('formPerfil')?.addEventListener('submit', (e) => {
        e.preventDefault();
        guardarPerfil();
    });
    document.getElementById('formPassword')?.addEventListener('submit', (e) => {
        e.preventDefault();
        cambiarContrasena();
    });
    document.getElementById('btnBackup')?.addEventListener('click', backupDb);
});
