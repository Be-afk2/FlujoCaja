
// ==================== TRANSACCIONES ====================

let tipoSeleccionado = 'expense';
let tipoSeleccionadoEditar = 'expense';
let editandoId = null;
let eliminandoId = null;

// ==================== UTILIDADES ====================

function fechaHoyISO() {
    return new Date().toISOString().split('T')[0];
}

function montoConSigno(monto, esIngreso) {
    return esIngreso ? Math.abs(monto) : -Math.abs(monto);
}

function alternarTab(tabId, activo, inactivo) {
    document.getElementById(tabId).classList.add(activo);
    document.getElementById(tabId).classList.remove('text-slate-500');
    document.getElementById(inactivo).classList.remove(activo === 'income-active' ? 'expense-active' : 'income-active');
    document.getElementById(inactivo).classList.add('text-slate-500');
}

// ==================== SELECTORES ====================

/**
 * Llena el selector de subtipos según el tipo seleccionado.
 */
async function cargarSubtipos(selectId, tipoId, seleccionado = null) {
    const select = document.getElementById(selectId);
    if (!select) return;
    if (!tipoId) {
        select.innerHTML = '<option value="">Seleccionar subtipo</option>';
        return;
    }
    const resp = await get(`subtipos/?tipo_id=${tipoId}`);
    select.innerHTML = '<option value="">Seleccionar subtipo</option>' +
        (resp.subtipos || []).map(s =>
            `<option value="${s.id}" ${Number(s.id) === Number(seleccionado) ? 'selected' : ''}>${s.nombre}</option>`
        ).join('');
}

async function cargarSelectores() {
    try {
        await Promise.all([
            cargarSelectorCuentas('account'),
            cargarSelectorTipos('category'),
        ]);
    } catch (error) {
        console.error('Error cargando selectores:', error);
    }
    cargarMovimientos();
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

function setTipoEditar(type) {
    tipoSeleccionadoEditar = type;
    if (type === 'income') {
        alternarTab('editIncomeTab', 'income-active', 'editExpenseTab');
    } else {
        alternarTab('editExpenseTab', 'expense-active', 'editIncomeTab');
    }
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

// ==================== LISTAR MOVIMIENTOS ====================

async function cargarMovimientos() {
    const tbody = document.getElementById('tbodyMovimientos');
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="5" class="px-4 py-8 text-center text-slate-500">Cargando movimientos...</td></tr>';

    try {
        const [resp, cuentas, tipos] = await Promise.all([
            get('movimientos/?cantidad=50'),
            get('cuentas/'),
            get('tipos/?cantidad=50'),
        ]);

        const cuentasMap = {};
        cuentas.forEach(c => { cuentasMap[c.id] = c.nombre; });
        const tiposMap = {};
        tipos.forEach(t => { tiposMap[t.id] = t.nombre; });

        renderTablaMovimientos('tbodyMovimientos', resp.data, {
            cuentasMap,
            tiposMap,
            conAcciones: true,
            onEditar: abrirModalEditar,
            onEliminar: confirmarEliminar,
        });

        const totalEl = document.getElementById('totalMovimientos');
        if (totalEl) totalEl.textContent = `Total: ${resp.total}`;
    } catch (error) {
        console.error('Error cargando movimientos:', error);
        tbody.innerHTML = '<tr><td colspan="5" class="px-4 py-8 text-center text-slate-500">Error al cargar movimientos.</td></tr>';
    }
}

// ==================== EDITAR MOVIMIENTO ====================

async function abrirModalEditar(mov) {
    editandoId = mov.id;
    const esIngreso = Number(mov.monto) > 0;

    document.getElementById('editAmount').value = Math.abs(mov.monto);
    document.getElementById('editDate').value = mov.fecha;
    document.getElementById('editNote').value = mov.descripcion || '';

    setTipoEditar(esIngreso ? 'income' : 'expense');

    try {
        await cargarSelectorCuentas('editAccount', mov.cuenta_id);
        await cargarSelectorTipos('editCategory', mov.tipo_id);
        await cargarSubtipos('editSubtipo', mov.tipo_id, mov.subtipo_id);
    } catch (error) {
        console.error('Error cargando selectores de edición:', error);
    }

    document.getElementById('modalEditar').classList.remove('hidden');
}

function cerrarModalEditar() {
    editandoId = null;
    document.getElementById('modalEditar').classList.add('hidden');
    const form = document.getElementById('formEditar');
    if (form) form.reset();
}

async function guardarEdicion() {
    if (!editandoId) return;

    const monto = Number(document.getElementById('editAmount').value);
    const fecha = document.getElementById('editDate').value;
    const cuentaId = document.getElementById('editAccount').value;
    const tipoId = document.getElementById('editCategory').value;
    const subtipoId = document.getElementById('editSubtipo').value;
    const descripcion = document.getElementById('editNote').value.trim();

    if (!monto || !cuentaId || !tipoId) {
        mostrarNotificacion('Completa monto, cuenta y tipo', 'warning');
        return;
    }

    const btn = document.getElementById('btnGuardarEdicion');
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Guardando...';
    }

    try {
        await putRequest(`movimientos/${editandoId}`, {
            monto: montoConSigno(monto, tipoSeleccionadoEditar === 'income'),
            tipo_id: Number(tipoId),
            cuenta_id: Number(cuentaId),
            subtipo_id: subtipoId ? Number(subtipoId) : null,
            descripcion: descripcion || null,
            fecha: fechaParaAPI(fecha),
        });
        mostrarNotificacion('Movimiento actualizado');
        cerrarModalEditar();
        cargarMovimientos();
    } catch (error) {
        console.error('Error actualizando movimiento:', error);
        mostrarNotificacion(error.message || 'Error al actualizar el movimiento', 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Guardar Cambios';
        }
    }
}

// ==================== ELIMINAR MOVIMIENTO ====================

function confirmarEliminar(mov) {
    eliminandoId = mov.id;
    document.getElementById('modalEliminar').classList.remove('hidden');
}

function cerrarModalEliminar() {
    eliminandoId = null;
    document.getElementById('modalEliminar').classList.add('hidden');
}

async function eliminarMovimiento() {
    if (!eliminandoId) return;

    const btn = document.getElementById('btnConfirmarEliminar');
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Eliminando...';
    }

    try {
        await deleteRequest(`movimientos/${eliminandoId}`);
        mostrarNotificacion('Movimiento eliminado');
        cerrarModalEliminar();
        cargarMovimientos();
    } catch (error) {
        console.error('Error eliminando movimiento:', error);
        mostrarNotificacion(error.message || 'Error al eliminar el movimiento', 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Eliminar';
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
    document.getElementById('editCategory')?.addEventListener('change', (e) => {
        cargarSubtipos('editSubtipo', e.target.value);
    });
    document.getElementById('btnGuardarEdicion')?.addEventListener('click', guardarEdicion);
    document.querySelectorAll('[data-cerrar-edicion]').forEach(btn => btn.addEventListener('click', cerrarModalEditar));
    document.querySelectorAll('[data-cerrar-eliminar]').forEach(btn => btn.addEventListener('click', cerrarModalEliminar));
    document.getElementById('btnConfirmarEliminar')?.addEventListener('click', eliminarMovimiento);

    cargarSelectores();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initTransacciones);
} else {
    initTransacciones();
}
