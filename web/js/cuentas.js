
// ==================== CUENTAS ====================

/**
 * Carga las cuentas del usuario y las renderiza como tarjetas.
 */
async function cargarCuentas() {
    const contenedor = document.getElementById('accounts-container');
    if (!contenedor) return;

    contenedor.innerHTML = '<div class="col-span-full flex justify-center p-8 text-slate-500">Cargando cuentas...</div>';

    try {
        const [cuentas, tiposCuenta, monedas] = await Promise.all([
            get('cuentas/'),
            get('cuentas/tipos-cuenta'),
            get('monedas/'),
        ]);

        const tiposMap = {};
        (tiposCuenta || []).forEach(t => { tiposMap[t.id] = t.tipo; });
        const monedasMap = {};
        (monedas || []).forEach(m => { monedasMap[m.id] = m.simbolo; });

        renderCuentas(cuentas, tiposMap, monedasMap);
    } catch (error) {
        console.error('Error cargando cuentas:', error);
        contenedor.innerHTML = '<div class="col-span-full text-center text-slate-500 p-8 border-2 border-dashed border-slate-800 rounded-xl">Error al cargar las cuentas.</div>';
    }
}

/**
 * Renderiza las tarjetas de cuenta dentro de #accounts-container.
 */
function renderCuentas(cuentas, tiposMap, monedasMap) {
    const contenedor = document.getElementById('accounts-container');
    if (!contenedor) return;

    const tarjetaAdd = `
        <div class="border-2 border-dashed border-slate-800 rounded-xl p-6 flex flex-col items-center justify-center text-slate-500 hover:border-primary hover:text-primary transition-all cursor-pointer group"
            data-purpose="add-account-shortcut">
            <div class="w-12 h-12 rounded-full bg-slate-900 flex items-center justify-center group-hover:bg-primary/10 transition-colors mb-3">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewbox="0 0 24 24">
                    <path d="M12 4v16m8-8H4" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
                </svg>
            </div>
            <span class="text-sm font-medium">Añadir otra cuenta</span>
        </div>`;

    if (!cuentas || cuentas.length === 0) {
        contenedor.innerHTML = `
            <div class="col-span-full text-center text-slate-500 p-8 border-2 border-dashed border-slate-800 rounded-xl">
                No tienes cuentas. Añade la primera.
            </div>
            ${tarjetaAdd}`;
        document.querySelector('[data-purpose="add-account-shortcut"]')?.addEventListener('click', abrirModalCuenta);
        return;
    }

    const tarjetas = cuentas.map(c => {
        const simbolo = monedasMap[c.moneda_id] || '$';
        const tipo = tiposMap[c.tipo_id] || 'Cuenta';
        const saldo = Number(c.saldo).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
        return `
        <div class="account-card bg-dark-900 p-6 rounded-xl border border-slate-800 shadow-sm flex flex-col justify-between"
            data-purpose="account-item">
            <div class="flex justify-between items-start mb-4">
                <div class="p-2 bg-blue-500/10 rounded-lg">
                    <svg class="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" viewbox="0 0 24 24">
                        <path d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
                    </svg>
                </div>
                <span class="text-xs font-semibold text-primary">${tipo}</span>
            </div>
            <div>
                <h3 class="text-xs font-medium text-slate-500 uppercase tracking-wider">${c.nombre}</h3>
                <p class="text-2xl font-bold text-white mt-1">${simbolo}${saldo}</p>
            </div>
            <div class="mt-4 pt-4 border-t border-slate-800 flex justify-between items-center">
                <span class="text-xs text-slate-500">${c.descripcion || 'Sin descripción'}</span>
            </div>
        </div>`;
    }).join('');

    contenedor.innerHTML = tarjetas + tarjetaAdd;

    document.querySelector('[data-purpose="add-account-shortcut"]')?.addEventListener('click', abrirModalCuenta);
}

// ==================== MODAL NUEVA CUENTA ====================

/**
 * Abre el modal y llena los selectores de tipo y moneda.
 */
async function abrirModalCuenta() {
    const modal = document.getElementById('modalCuenta');
    if (!modal) return;

    try {
        const [tipos, monedas] = await Promise.all([
            get('cuentas/tipos-cuenta'),
            get('monedas/'),
        ]);

        const selTipo = document.getElementById('inputTipoCuenta');
        selTipo.innerHTML = (tipos || []).map(t => `<option value="${t.id}">${t.tipo}</option>`).join('');

        const selMoneda = document.getElementById('inputMoneda');
        selMoneda.innerHTML = (monedas || []).map(m => `<option value="${m.id}">${m.nombre} (${m.simbolo})</option>`).join('');

        modal.classList.remove('hidden');
    } catch (error) {
        console.error('Error cargando tipos/monedas:', error);
        mostrarNotificacion('Error al cargar el formulario', 'error');
    }
}

function cerrarModalCuenta() {
    const modal = document.getElementById('modalCuenta');
    if (modal) modal.classList.add('hidden');
    const form = document.getElementById('formNuevaCuenta');
    if (form) form.reset();
}

/**
 * Envía la nueva cuenta a la API y recarga la lista.
 */
async function guardarCuenta() {
    const nombre = document.getElementById('inputNombreCuenta').value.trim();
    const descripcion = document.getElementById('inputDescripcionCuenta').value.trim();
    const tipo = document.getElementById('inputTipoCuenta').value;
    const moneda = document.getElementById('inputMoneda').value;

    if (!nombre || !tipo || !moneda) {
        mostrarNotificacion('Completa nombre, tipo y moneda', 'warning');
        return;
    }

    const btnGuardar = document.getElementById('btn-guardar-cuenta');
    if (btnGuardar) {
        btnGuardar.disabled = true;
        btnGuardar.textContent = 'Guardando...';
    }

    try {
        await post('cuentas/', {
            nombre,
            descripcion,
            tipo: Number(tipo),
            moneda: Number(moneda),
        });
        mostrarNotificacion('Cuenta creada exitosamente');
        cerrarModalCuenta();
        cargarCuentas();
    } catch (error) {
        console.error('Error creando cuenta:', error);
        mostrarNotificacion(error.message || 'Error al crear la cuenta', 'error');
    } finally {
        if (btnGuardar) {
            btnGuardar.disabled = false;
            btnGuardar.textContent = 'Guardar';
        }
    }
}

// ==================== INICIALIZACIÓN ====================

function initCuentas() {
    document.getElementById('btn-add-account')?.addEventListener('click', abrirModalCuenta);
    document.querySelectorAll('[data-cerrar-modal]').forEach(btn => btn.addEventListener('click', cerrarModalCuenta));
    document.getElementById('btn-guardar-cuenta')?.addEventListener('click', guardarCuenta);
    cargarCuentas();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCuentas);
} else {
    initCuentas();
}
