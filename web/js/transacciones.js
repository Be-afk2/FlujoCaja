// ==================== TRANSACCIONES ====================

let tipoSeleccionado = 'expense';

// ==================== SELECTORES ====================

async function cargarSelectores() {
    try {
        await Promise.all([
            cargarSelectorCuentas('account'),
            cargarSelectorTipos('category'),
        ]);
    } catch (error) {
        console.error('Error cargando selectores:', error);
    }
}

// ==================== VISTA PREVIA ====================

function switchType(type) {
    tipoSeleccionado = type;
    if (type === 'income') {
        alternarTab('incomeTab', 'income-active', 'expenseTab');
    } else {
        alternarTab('expenseTab', 'expense-active', 'incomeTab');
    }
    updatePreview();
}

function updatePreview() {
    const amount = document.getElementById('amount').value || '0.00';
    const date = document.getElementById('date').value || 'Sin fecha';
    const accountSelect = document.getElementById('account');
    const account = accountSelect.selectedOptions[0]?.textContent || 'Seleccionar cuenta';
    const categorySelect = document.getElementById('category');
    const categoryName = categorySelect.selectedOptions[0]?.textContent || 'Seleccionar Categoría';
    const note = document.getElementById('note').value || 'No hay descripción...';

    const amountEl = document.getElementById('previewAmount');
    if (tipoSeleccionado === 'expense') {
        amountEl.innerText = `-$${amount}`;
        amountEl.classList.remove('text-brand');
        amountEl.classList.add('text-red-500');
    } else {
        amountEl.innerText = `+$${amount}`;
        amountEl.classList.remove('text-red-500');
        amountEl.classList.add('text-brand');
    }

    document.getElementById('previewCategory').innerText = categoryName;
    document.getElementById('previewAccount').innerText = account;
    document.getElementById('previewDate').innerText = date;
    document.getElementById('previewNote').innerText = note;
}

// ==================== CREAR MOVIMIENTO ====================

async function guardarTransaccion() {
    const monto = Number(document.getElementById('amount').value);
    const fecha = document.getElementById('date').value;
    const cuentaId = document.getElementById('account').value;
    const tipoId = document.getElementById('category').value;
    const subtipoId = document.getElementById('subtipo').value;
    const descripcion = document.getElementById('note').value.trim();

    if (!monto || !cuentaId || !tipoId) {
        mostrarNotificacion('Completa monto, cuenta y tipo', 'warning');
        return;
    }

    const btn = document.getElementById('btnGuardarTransaccion');
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Guardando...';
    }

    try {
        await post('movimientos/', {
            monto: montoConSigno(monto, tipoSeleccionado === 'income'),
            tipo_id: Number(tipoId),
            cuenta_id: Number(cuentaId),
            subtipo_id: subtipoId ? Number(subtipoId) : null,
            descripcion: descripcion || null,
            fecha: fechaParaAPI(fecha),
        });
        mostrarNotificacion('Movimiento registrado');
        document.getElementById('transactionForm').reset();
        document.getElementById('date').value = fechaHoyISO();
        cargarSelectores();
    } catch (error) {
        console.error('Error creando movimiento:', error);
        mostrarNotificacion(error.message || 'Error al guardar el movimiento', 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Guardar Transacción';
        }
    }
}

// ==================== INICIALIZACIÓN ====================

function initTransacciones() {
    document.getElementById('date').value = fechaHoyISO();

    document.getElementById('btnGuardarTransaccion')?.addEventListener('click', guardarTransaccion);
    document.getElementById('category')?.addEventListener('change', (e) => {
        cargarSubtipos('subtipo', e.target.value);
        updatePreview();
    });
    document.getElementById('account')?.addEventListener('change', updatePreview);

    cargarSelectores();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTransacciones);
} else {
    initTransacciones();
}