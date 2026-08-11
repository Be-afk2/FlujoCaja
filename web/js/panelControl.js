
// ==================== PANEL DE CONTROL ====================

const NOMBRES_MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

// ==================== MÉTRICAS PRINCIPALES ====================

async function cargarDashboard() {
    const ahora = new Date();
    const anio = ahora.getFullYear();
    const mes = ahora.getMonth() + 1;

    try {
        const [resumen, movimientos, cuentas] = await Promise.all([
            get(`resumen/mensual?anio=${anio}&mes=${mes}`),
            get('movimientos/?cantidad=5'),
            get('cuentas/'),
        ]);

        // Métricas del mes (agregar por cuenta)
        const ingresos = (resumen || []).reduce((s, r) => s + (r.total_ingresos || 0), 0);
        const gastos = (resumen || []).reduce((s, r) => s + (r.total_gastos || 0), 0);

        const elIngresos = document.getElementById('ingresosMes');
        const elGastos = document.getElementById('gastosMes');
        if (elIngresos) elIngresos.textContent = formatearDinero(ingresos);
        if (elGastos) elGastos.textContent = formatearDinero(gastos);

        // Flujo neto del mes
        const neto = ingresos - gastos;
        const elNeto = document.getElementById('flujoNeto');
        if (elNeto) {
            elNeto.textContent = formatearDinero(neto);
            elNeto.classList.remove('text-emerald-500', 'text-rose-500');
            elNeto.classList.add(neto >= 0 ? 'text-emerald-500' : 'text-rose-500');
        }

        // Saldo total = suma de saldos de cuentas
        const saldoTotal = (cuentas || []).reduce((s, c) => s + (c.saldo || 0), 0);
        const elSaldo = document.getElementById('saldoTotal');
        if (elSaldo) elSaldo.textContent = formatearDinero(saldoTotal);

        await renderTransaccionesRecientes((movimientos || {}).data || []);
        renderGrafico();
        renderCategoriasGasto();
    } catch (error) {
        console.error('Error cargando dashboard:', error);
    }
}

// ==================== TRANSACCIONES RECIENTES ====================

async function renderTransaccionesRecientes(movimientos) {
    const contenedor = document.getElementById('listaTransacciones');
    if (!contenedor) return;

    if (!movimientos || movimientos.length === 0) {
        contenedor.innerHTML = '<div class="p-6 text-center text-slate-500 text-sm">No hay transacciones recientes.</div>';
        return;
    }

    try {
        const [cuentas, tipos] = await Promise.all([
            get('cuentas/'),
            get('tipos/?cantidad=50'),
        ]);
        const cuentasMap = {};
        cuentas.forEach(c => { cuentasMap[c.id] = c.nombre; });
        const tiposMap = {};
        tipos.forEach(t => { tiposMap[t.id] = t.nombre; });

        contenedor.innerHTML = movimientos.map(m => {
            const esIngreso = Number(m.monto) > 0;
            const iconoClases = esIngreso
                ? 'bg-emerald-500/10 text-emerald-500 group-hover:bg-emerald-500/20'
                : 'bg-slate-800 text-slate-400 group-hover:bg-slate-700';
            const nombreTipo = tiposMap[m.tipo_id] || 'Movimiento';
            const nombreCuenta = cuentasMap[m.cuenta_id] || '';
            return `
            <div class="flex items-center justify-between p-4 hover:bg-slate-800 transition-colors rounded-xl group">
                <div class="flex items-center space-x-4">
                    <div class="w-10 h-10 ${iconoClases} rounded-full flex items-center justify-center">
                        <svg class="h-5 w-5" fill="none" stroke="currentColor" viewbox="0 0 24 24"
                            xmlns="http://www.w3.org/2000/svg">
                            <path d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                                stroke-linecap="round" stroke-linejoin="round" stroke-width="2"></path>
                        </svg>
                    </div>
                    <div>
                        <p class="font-semibold text-slate-200 text-sm">${nombreTipo}</p>
                        <p class="text-xs text-slate-500">${nombreCuenta} • ${formatearFechaLegible(m.fecha)}</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="font-bold ${esIngreso ? 'text-emerald-500' : 'text-slate-200'} text-sm">${esIngreso ? '+' : ''}${formatearDinero(m.monto)}</p>
                </div>
            </div>`;
        }).join('');
    } catch (error) {
        console.error('Error cargando transacciones recientes:', error);
        contenedor.innerHTML = '<div class="p-6 text-center text-slate-500 text-sm">Error al cargar transacciones.</div>';
    }
}

// ==================== GRÁFICO INGRESOS VS GASTOS ====================

function ultimosNMeses(n) {
    const ahora = new Date();
    const res = [];
    for (let i = n - 1; i >= 0; i--) {
        const d = new Date(ahora.getFullYear(), ahora.getMonth() - i, 1);
        res.push({ anio: d.getFullYear(), mes: d.getMonth() + 1, label: NOMBRES_MESES[d.getMonth()] });
    }
    return res;
}

function mesesDelAnioActual() {
    const anio = new Date().getFullYear();
    return NOMBRES_MESES.map((label, i) => ({ anio, mes: i + 1, label }));
}

async function obtenerResumenAnual(anio) {
    const r = await get(`resumen/anual?anio=${anio}`);
    const porMes = {};
    (r || []).forEach(item => {
        const clave = `${item.anio}-${item.mes}`;
        if (!porMes[clave]) porMes[clave] = { ingresos: 0, gastos: 0 };
        porMes[clave].ingresos += item.total_ingresos || 0;
        porMes[clave].gastos += item.total_gastos || 0;
    });
    return porMes;
}

async function renderGrafico() {
    const contenedor = document.getElementById('bar-chart');
    if (!contenedor) return;

    const rango = document.getElementById('rangoGrafico')?.value || '6m';
    const meses = rango === '6m' ? ultimosNMeses(6) : mesesDelAnioActual();

    try {
        const anios = [...new Set(meses.map(m => m.anio))];
        const mapas = await Promise.all(anios.map(obtenerResumenAnual));
        const porMes = Object.assign({}, ...mapas);

        const datos = meses.map(m => ({
            label: m.label,
            ...(porMes[`${m.anio}-${m.mes}`] || { ingresos: 0, gastos: 0 }),
        }));

        const max = Math.max(1, ...datos.flatMap(d => [d.ingresos, d.gastos]));

        contenedor.innerHTML = datos.map(d => {
            const hIng = Math.max(4, Math.round((d.ingresos / max) * 140));
            const hGas = Math.max(4, Math.round((d.gastos / max) * 140));
            return `
            <div class="flex flex-col items-center flex-1 space-y-2">
                <div class="w-full flex justify-center space-x-1 items-end">
                    <div class="w-4 bg-emerald-500 rounded-t-sm" style="height: ${hIng}px;"></div>
                    <div class="w-4 bg-slate-700 rounded-t-sm" style="height: ${hGas}px;"></div>
                </div>
                <span class="text-[10px] text-slate-500 font-medium uppercase tracking-wider">${d.label}</span>
            </div>`;
        }).join('');
    } catch (error) {
        console.error('Error cargando gráfico:', error);
    }
}

// ==================== GASTOS POR CATEGORÍA ====================

async function renderCategoriasGasto() {
    const contenedor = document.getElementById('categoriasGasto');
    if (!contenedor) return;

    try {
        const [resp, tipos] = await Promise.all([
            get('movimientos/?cantidad=200&es_ingreso=false'),
            get('tipos/?cantidad=50'),
        ]);

        const tiposMap = {};
        tipos.forEach(t => { tiposMap[t.id] = t.nombre; });

        const porTipo = {};
        (resp.data || []).forEach(m => {
            const monto = Math.abs(Number(m.monto));
            if (monto > 0) porTipo[m.tipo_id] = (porTipo[m.tipo_id] || 0) + monto;
        });

        const categorias = Object.entries(porTipo)
            .map(([id, monto]) => ({ id: Number(id), monto, nombre: tiposMap[id] || `Tipo ${id}` }))
            .sort((a, b) => b.monto - a.monto);

        if (categorias.length === 0) {
            contenedor.innerHTML = '<p class="text-sm text-slate-500">No hay gastos registrados.</p>';
            return;
        }

        const total = categorias.reduce((s, c) => s + c.monto, 0);

        contenedor.innerHTML = categorias.slice(0, 5).map(c => {
            const pct = Math.round((c.monto / total) * 100);
            return `
            <div class="space-y-1">
                <div class="flex justify-between text-sm mb-1">
                    <span class="font-medium text-slate-300">${c.nombre}</span>
                    <span class="text-slate-500">${formatearDinero(c.monto)} (${pct}%)</span>
                </div>
                <div class="w-full bg-slate-800 rounded-full h-2">
                    <div class="bg-emerald-500 h-2 rounded-full" style="width: ${pct}%"></div>
                </div>
            </div>`;
        }).join('');
    } catch (error) {
        console.error('Error cargando gastos por categoría:', error);
    }
}

// ==================== MOVIMIENTOS (TABLA) ====================

let tipoSeleccionadoEditar = 'expense';
let editandoId = null;
let eliminandoId = null;

function setTipoEditar(type) {
    tipoSeleccionadoEditar = type;
    if (type === 'income') {
        alternarTab('editIncomeTab', 'income-active', 'editExpenseTab');
    } else {
        alternarTab('editExpenseTab', 'expense-active', 'editIncomeTab');
    }
}

function filtrosQuery(cantidad = '50') {
    const params = new URLSearchParams({ cantidad });
    const cuenta = document.getElementById('filtroCuenta')?.value;
    const desde = document.getElementById('filtroDesde')?.value;
    const hasta = document.getElementById('filtroHasta')?.value;
    if (cuenta) params.set('cuenta_id', cuenta);
    if (desde) params.set('fecha_desde', fechaParaAPI(desde));
    if (hasta) params.set('fecha_hasta', fechaParaAPI(hasta));
    return params.toString();
}

function limpiarFiltros() {
    document.getElementById('filtroCuenta').value = '';
    document.getElementById('filtroDesde').value = '';
    document.getElementById('filtroHasta').value = '';
    cargarMovimientos();
}

async function cargarMovimientos() {
    const tbody = document.getElementById('tbodyMovimientos');
    if (!tbody) return;

    tbody.innerHTML = '<tr><td colspan="5" class="px-4 py-8 text-center text-slate-500">Cargando movimientos...</td></tr>';

    try {
        const [resp, cuentas, tipos] = await Promise.all([
            get(`movimientos/?${filtrosQuery()}`),
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

// ==================== EXPORTAR / IMPORTAR CSV ====================

function csvEscape(v) {
    const s = String(v ?? '');
    return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
}

async function exportarCSV() {
    const btn = document.getElementById('btnExportarCSV');
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Generando...';
    }

    try {
        const [resp, cuentas, tipos] = await Promise.all([
            get(`movimientos/?${filtrosQuery('100000')}`),
            get('cuentas/'),
            get('tipos/?cantidad=50'),
        ]);

        const cuentasMap = {};
        cuentas.forEach(c => { cuentasMap[c.id] = c.nombre; });
        const tiposMap = {};
        tipos.forEach(t => { tiposMap[t.id] = t.nombre; });

        const lineas = [['fecha', 'monto', 'tipo', 'cuenta', 'descripcion']];
        (resp.data || []).forEach(m => {
            lineas.push([
                m.fecha,
                m.monto,
                tiposMap[m.tipo_id] || '',
                cuentasMap[m.cuenta_id] || '',
                m.descripcion || '',
            ].map(csvEscape).join(','));
        });

        const csv = '\ufeff' + lineas.join('\r\n');
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `movimientos_${fechaHoyISO()}.csv`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        mostrarNotificacion(`Exportados ${resp.total} movimientos`);
    } catch (error) {
        console.error('Error exportando CSV:', error);
        mostrarNotificacion(error.message || 'Error al exportar CSV', 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Exportar CSV';
        }
    }
}

function parsearCSV(texto) {
    const filas = [];
    const lineas = texto.replace(/^\uFEFF/, '').trim().split(/\r?\n/);
    if (lineas.length < 2) return filas;

    const headers = lineas[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''));
    for (let i = 1; i < lineas.length; i++) {
        const linea = lineas[i].trim();
        if (!linea) continue;

        const valores = [];
        let actual = '';
        let entreComillas = false;
        for (const ch of linea) {
            if (ch === '"') {
                entreComillas = !entreComillas;
            } else if (ch === ',' && !entreComillas) {
                valores.push(actual);
                actual = '';
            } else {
                actual += ch;
            }
        }
        valores.push(actual);

        const fila = {};
        headers.forEach((h, idx) => { fila[h] = (valores[idx] || '').trim(); });
        filas.push(fila);
    }
    return filas;
}

function fechaParaAPICompat(f) {
    if (/^\d{4}-\d{2}-\d{2}$/.test(f)) return fechaParaAPI(f);
    if (/^\d{2}-\d{2}-\d{4}$/.test(f)) return f;
    return null;
}

async function importarCSV(file) {
    const texto = await file.text();
    const filas = parsearCSV(texto);

    if (filas.length === 0) {
        mostrarNotificacion('El archivo CSV está vacío o no tiene encabezado', 'warning');
        return;
    }

    const [cuentas, tipos] = await Promise.all([
        get('cuentas/'),
        get('tipos/?cantidad=50'),
    ]);
    const cuentasPorNombre = {};
    cuentas.forEach(c => { cuentasPorNombre[c.nombre.toLowerCase()] = c.id; });
    const tiposPorNombre = {};
    tipos.forEach(t => { tiposPorNombre[t.nombre.toLowerCase()] = t.id; });

    const items = [];
    let erroresPrevios = 0;
    filas.forEach(f => {
        const cuentaId = cuentasPorNombre[String(f.cuenta || '').toLowerCase()];
        const tipoId = tiposPorNombre[String(f.tipo || '').toLowerCase()];
        const monto = Number(f.monto);
        const fecha = fechaParaAPICompat(f.fecha || '');

        if (!cuentaId || !tipoId || Number.isNaN(monto) || !fecha) {
            erroresPrevios++;
            return;
        }

        items.push({
            monto,
            tipo_id: tipoId,
            cuenta_id: cuentaId,
            descripcion: f.descripcion || null,
            fecha,
        });
    });

    if (items.length === 0) {
        mostrarNotificacion('Ninguna fila válida para importar', 'error');
        return;
    }

    try {
        const resp = await post('movimientos/importar', { filas: items });
        const erroresTotales = resp.errores.length + erroresPrevios;
        const msg = `Importados: ${resp.importados}`;
        mostrarNotificacion(
            erroresTotales > 0 ? `${msg} · Errores: ${erroresTotales}` : msg,
            erroresTotales > 0 ? 'warning' : 'success'
        );
        cargarMovimientos();
    } catch (error) {
        console.error('Error importando CSV:', error);
        mostrarNotificacion(error.message || 'Error al importar CSV', 'error');
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

function initPanel() {
    document.getElementById('rangoGrafico')?.addEventListener('change', renderGrafico);

    document.getElementById('filtroCuenta')?.addEventListener('change', cargarMovimientos);
    document.getElementById('filtroDesde')?.addEventListener('change', cargarMovimientos);
    document.getElementById('filtroHasta')?.addEventListener('change', cargarMovimientos);
    document.getElementById('btnLimpiarFiltros')?.addEventListener('click', limpiarFiltros);
    document.getElementById('btnExportarCSV')?.addEventListener('click', exportarCSV);
    document.getElementById('inputImportarCSV')?.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (file) importarCSV(file);
        e.target.value = '';
    });
    document.querySelectorAll('[data-cerrar-edicion]').forEach(btn => btn.addEventListener('click', cerrarModalEditar));
    document.getElementById('btnGuardarEdicion')?.addEventListener('click', guardarEdicion);
    document.querySelectorAll('[data-cerrar-eliminar]').forEach(btn => btn.addEventListener('click', cerrarModalEliminar));
    document.getElementById('btnConfirmarEliminar')?.addEventListener('click', eliminarMovimiento);

    cargarSelectorCuentas('filtroCuenta').then(() => {
        const select = document.getElementById('filtroCuenta');
        if (select && select.options[0]) select.options[0].textContent = 'Todas';
    });

    cargarDashboard();
    cargarMovimientos();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPanel);
} else {
    initPanel();
}
