
// ==================== PANEL DE CONTROL ====================

const NOMBRES_MESES = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun', 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic'];

// ==================== ESTADO DE MONEDAS ====================

const MONEDA_STORAGE_KEY = 'panel_moneda';
const DEUDAS_STORAGE_KEY = 'incluir_deudas_totales';

let cuentasGlobales = [];
let monedaPorCuenta = {}; // cuenta_id -> moneda_id
let simboloMoneda = {};  // moneda_id -> simbolo

function incluirDeudasEnTotales() {
    const toggle = document.getElementById('toggleDeudas');
    return toggle ? toggle.checked : true;
}

function restaurarToggleDeudas() {
    const toggle = document.getElementById('toggleDeudas');
    if (!toggle) return;
    const guardado = localStorage.getItem(DEUDAS_STORAGE_KEY);
    toggle.checked = guardado === null ? true : guardado === 'true';
}

function guardarToggleDeudas() {
    const toggle = document.getElementById('toggleDeudas');
    if (toggle) localStorage.setItem(DEUDAS_STORAGE_KEY, String(toggle.checked));
}

function monedaSeleccionada() {
    const sel = document.getElementById('filtroMoneda');
    return sel ? sel.value : '';
}

function simboloPara(cuentaId) {
    return simboloMoneda[monedaPorCuenta[cuentaId]] || '$';
}

async function cargarDatosMaestros() {
    const [cuentas, monedas] = await Promise.all([get('cuentas/'), get('monedas/')]);
    cuentasGlobales = cuentas || [];
    monedaPorCuenta = {};
    simboloMoneda = {};
    (monedas || []).forEach(m => { simboloMoneda[m.id] = m.simbolo || '$'; });
    (cuentas || []).forEach(c => { monedaPorCuenta[c.id] = c.moneda_id; });

    const sel = document.getElementById('filtroMoneda');
    if (sel) {
        const enUso = [...new Set((cuentas || []).map(c => c.moneda_id))];
        sel.innerHTML = enUso.map(id => {
            const m = (monedas || []).find(x => x.id === id);
            return m ? `<option value="${m.id}">${m.nombre} (${m.simbolo})</option>` : '';
        }).join('');

        if (enUso.length > 0) {
            const recordada = localStorage.getItem(MONEDA_STORAGE_KEY);
            const valor = enUso.some(id => String(id) === recordada) ? recordada : String(enUso[0]);
            sel.value = valor;
        }
    }
    return { cuentas, monedas };
}

function guardarMonedaSeleccionada() {
    const valor = monedaSeleccionada();
    if (valor) localStorage.setItem(MONEDA_STORAGE_KEY, valor);
}

// ==================== MÉTRICAS PRINCIPALES ====================

async function cargarDashboard() {
    const ahora = new Date();
    const anio = ahora.getFullYear();
    const mes = ahora.getMonth() + 1;
    const monedaId = monedaSeleccionada();

    try {
        const [resumen, movimientos, cuentas] = await Promise.all([
            get(`resumen/mensual?anio=${anio}&mes=${mes}&moneda_id=${monedaId}`),
            get(`movimientos/?cantidad=5&moneda_id=${monedaId}`),
            get('cuentas/'),
        ]);

        // Moneda específica: sumar solo las cuentas de esa moneda.
        const cuentasFiltradas = (cuentas || []).filter(c => String(c.moneda_id) === String(monedaId));
        const simbolo = simboloMoneda[monedaId] || '$';
        const incluirDeudas = incluirDeudasEnTotales();
        const ingresos = (resumen || []).reduce(
            (s, r) => s + (r.total_ingresos || 0) - (incluirDeudas ? 0 : (r.total_ingresos_deuda || 0)),
            0
        );
        const gastos = (resumen || []).reduce(
            (s, r) => s + (r.total_gastos || 0) - (incluirDeudas ? 0 : (r.total_gastos_deuda || 0)),
            0
        );
        const neto = ingresos - gastos;
        const saldoTotal = (cuentasFiltradas || []).reduce((s, c) => s + (c.saldo || 0), 0);

        pintarTarjeta('saldoTotal', saldoTotal, simbolo);
        pintarTarjeta('ingresosMes', ingresos, simbolo);
        pintarTarjeta('gastosMes', gastos, simbolo);
        pintarTarjeta('flujoNeto', neto, simbolo, neto >= 0 ? 'text-emerald-500' : 'text-rose-500');

        const sufijo = incluirDeudas ? '' : ' · sin deudas';
        const subIngresos = document.getElementById('ingresosMesSub');
        const subGastos = document.getElementById('gastosMesSub');
        const subNeto = document.getElementById('flujoNetoSub');
        if (subIngresos) subIngresos.textContent = `Mes actual${sufijo}`;
        if (subGastos) subGastos.textContent = `Mes actual${sufijo}`;
        if (subNeto) subNeto.textContent = `Ingresos - Gastos${sufijo}`;

        await renderTransaccionesRecientes((movimientos || {}).data || []);
        renderGrafico();
        renderCategoriasGasto();
    } catch (error) {
        console.error('Error cargando dashboard:', error);
    }
}

function pintarTarjeta(id, valor, simbolo, clase = '') {
    const el = document.getElementById(id);
    if (!el) return;
    el.textContent = formatearDinero(valor, simbolo);
    el.classList.remove('text-emerald-500', 'text-rose-500');
    if (clase) el.classList.add(clase);
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
        const simbolosMap = {};
        cuentas.forEach(c => { cuentasMap[c.id] = c.nombre; simbolosMap[c.id] = simboloPara(c.id); });
        const tiposMap = {};
        tipos.forEach(t => { tiposMap[t.id] = t.nombre; });

        contenedor.innerHTML = movimientos.map(m => {
            const esIngreso = Number(m.monto) > 0;
            const iconoClases = esIngreso
                ? 'bg-emerald-500/10 text-emerald-500 group-hover:bg-emerald-500/20'
                : 'bg-slate-800 text-slate-400 group-hover:bg-slate-700';
            const nombreTipo = tiposMap[m.tipo_id] || 'Movimiento';
            const nombreCuenta = cuentasMap[m.cuenta_id] || '';
            const simbolo = simbolosMap[m.cuenta_id] || '$';
            const badgeDeuda = m.es_deuda
                ? '<span class="ml-1.5 px-1.5 py-0.5 rounded text-[10px] font-bold bg-amber-500/15 text-amber-400 border border-amber-500/30">Deuda</span>'
                : '';
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
                        <p class="font-semibold text-slate-200 text-sm">${nombreTipo}${badgeDeuda}</p>
                        <p class="text-xs text-slate-500">${nombreCuenta} • ${formatearFechaLegible(m.fecha)}</p>
                    </div>
                </div>
                <div class="text-right">
                    <p class="font-bold ${esIngreso ? 'text-emerald-500' : 'text-slate-200'} text-sm">${esIngreso ? '+' : ''}${formatearDinero(m.monto, simbolo)}</p>
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

async function obtenerResumenRango(meses, monedaId, incluirDeudas) {
    // `meses` puede venir en orden descendente (ultimosNMeses), asi que el
    // rango se arma ordenando las claves y no por posicion.
    const claves = meses
        .map(m => `${m.anio}-${String(m.mes).padStart(2, '0')}`)
        .sort();
    const desde = claves[0];
    const hasta = claves[claves.length - 1];

    // Una sola peticion para todo el rango (antes: una por cada anio visible).
    const r = await get(`resumen/rango?desde=${desde}&hasta=${hasta}&moneda_id=${monedaId}`);
    const porMes = {};
    (r || []).forEach(item => {
        const clave = `${item.anio}-${item.mes}`;
        if (!porMes[clave]) porMes[clave] = { ingresos: 0, gastos: 0 };
        porMes[clave].ingresos += (item.total_ingresos || 0) - (incluirDeudas ? 0 : (item.total_ingresos_deuda || 0));
        porMes[clave].gastos += (item.total_gastos || 0) - (incluirDeudas ? 0 : (item.total_gastos_deuda || 0));
    });
    return porMes;
}

async function renderGrafico() {
    const contenedor = document.getElementById('bar-chart');
    if (!contenedor) return;

    const rango = document.getElementById('rangoGrafico')?.value || '6m';
    const monedaId = monedaSeleccionada();
    const meses = rango === '6m' ? ultimosNMeses(6) : mesesDelAnioActual();

    try {
        const incluirDeudas = incluirDeudasEnTotales();
        const porMes = await obtenerResumenRango(meses, monedaId, incluirDeudas);

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

    const monedaId = monedaSeleccionada();
    const filtroDeuda = incluirDeudasEnTotales() ? '' : '&es_deuda=false';

    try {
        const [resp, tipos] = await Promise.all([
            get(`movimientos/?cantidad=200&es_ingreso=false&moneda_id=${monedaId}${filtroDeuda}`),
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
        const simbolo = simboloMoneda[monedaId] || '$';

        contenedor.innerHTML = categorias.slice(0, 5).map(c => {
            const pct = Math.round((c.monto / total) * 100);
            return `
            <div class="space-y-1">
                <div class="flex justify-between text-sm mb-1">
                    <span class="font-medium text-slate-300">${c.nombre}</span>
                    <span class="text-slate-500">${formatearDinero(c.monto, simbolo)} (${pct}%)</span>
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
    const params = new URLSearchParams();
    if (cantidad) params.set('cantidad', cantidad);
    const moneda = document.getElementById('filtroMoneda')?.value;
    const cuenta = document.getElementById('filtroCuenta')?.value;
    const desde = document.getElementById('filtroDesde')?.value;
    const hasta = document.getElementById('filtroHasta')?.value;
    if (moneda) params.set('moneda_id', moneda);
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
        const simbolosMap = {};
        cuentas.forEach(c => { cuentasMap[c.id] = c.nombre; simbolosMap[c.id] = simboloPara(c.id); });
        const tiposMap = {};
        tipos.forEach(t => { tiposMap[t.id] = t.nombre; });

        renderTablaMovimientos('tbodyMovimientos', resp.data, {
            cuentasMap,
            tiposMap,
            simbolosMap,
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

async function exportarCSV() {
    const btn = document.getElementById('btnExportarCSV');
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Generando...';
    }

    try {
        // El CSV se arma en el servidor con los filtros activos; ya no hace
        // falta pedir `cantidad=100000` ni cruzar nombres en memoria.
        await downloadFile(
            `movimientos/exportar?${filtrosQuery(null)}`,
            `movimientos_${fechaHoyISO()}.csv`
        );
        mostrarNotificacion('Movimientos exportados');
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

// ==================== PAGOS MENSUALES ====================

let pagosMensualesItems = [];

function panelSimboloMoneda(monedaId) {
    return simboloMoneda[monedaId] || '$';
}

function panelPagoMensualInfo(item) {
    const moneda = panelSimboloMoneda(item.moneda_id);
    const periodo = `${NOMBRES_MESES[(Number(item.mes) || 1) - 1] || ''} ${item.anio}`;
    const estado = item.vencida
        ? `<span class="text-rose-400">Vencida hace ${Math.abs(Number(item.dias_restantes))} días</span>`
        : Number(item.dias_restantes) === 0
            ? '<span class="text-amber-400">Vence hoy</span>'
            : `<span class="text-slate-400">Vence en ${item.dias_restantes} días</span>`;

    return { moneda, periodo, estado };
}

function renderFilaPagoMensual(item) {
    const { moneda, periodo, estado } = panelPagoMensualInfo(item);
    return `
        <div class="flex items-center justify-between gap-3 px-6 py-3 hover:bg-slate-800/60 transition-colors">
            <div class="flex items-center gap-3 min-w-0">
                <div class="w-9 h-9 rounded-lg ${item.vencida ? 'bg-rose-500/10 text-rose-400 border-rose-500/30' : 'bg-slate-700/60 text-slate-300 border-slate-700'} border flex items-center justify-center flex-shrink-0">
                    <i class="fa-solid ${item.vencida ? 'fa-triangle-exclamation' : 'fa-clock'} text-xs"></i>
                </div>
                <div class="min-w-0">
                    <p class="text-sm font-semibold text-white truncate">${escaparHtml(item.descripcion || 'Deuda mensual')}</p>
                    <p class="text-[11px] text-slate-500">
                        Cuota ${item.numero} · ${periodo} · ${estado}
                    </p>
                </div>
            </div>
            <div class="flex items-center gap-3 flex-shrink-0">
                <span class="text-sm font-bold ${item.vencida ? 'text-rose-400' : 'text-slate-200'}">${formatearDinero(item.monto, moneda)}</span>
                <button type="button" data-pagar-mensual="${item.cuota_id}"
                    class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition-colors">
                    <i class="fa-solid fa-check text-[10px]"></i>
                    Pagar
                </button>
            </div>
        </div>`;
}

function renderPagosMensuales(items) {
    const contenedor = document.getElementById('listaPagosMensuales');
    const resumen = document.getElementById('panelPagosMensualesResumen');
    if (!contenedor) return;

    pagosMensualesItems = Array.isArray(items) ? items : [];
    const vencidas = pagosMensualesItems.filter(item => item.vencida);
    const proximas = pagosMensualesItems.filter(item => !item.vencida);

    if (resumen) {
        resumen.textContent = vencidas.length > 0
            ? `${vencidas.length} vencida${vencidas.length === 1 ? '' : 's'} · ${proximas.length} próxima${proximas.length === 1 ? '' : 's'}`
            : `${proximas.length} próxima${proximas.length === 1 ? '' : 's'}`;
    }

    if (pagosMensualesItems.length === 0) {
        contenedor.innerHTML = `
            <div class="p-6 text-center">
                <p class="text-sm text-slate-400">No tenés cuotas mensuales vencidas ni próximas en 7 días.</p>
                <a href="deudasMensuales.html" class="inline-block mt-2 text-xs text-emerald-500 hover:underline font-medium">Gestionar deudas mensuales</a>
            </div>`;
        return;
    }

    const seccion = (titulo, clase, lista) => {
        if (lista.length === 0) return '';
        return `
            <div>
                <div class="px-6 py-2 bg-slate-900/60 border-b border-slate-800">
                    <span class="text-[10px] font-bold uppercase tracking-wider ${clase}">${titulo} (${lista.length})</span>
                </div>
                ${lista.map(renderFilaPagoMensual).join('')}
            </div>`;
    };

    contenedor.innerHTML = `
        ${seccion('Vencidas', 'text-rose-400', vencidas)}
        ${seccion('Próximas 7 días', 'text-amber-400', proximas)}`;
}

async function cargarPagosMensuales() {
    const contenedor = document.getElementById('listaPagosMensuales');
    if (!contenedor) return;

    const moneda = monedaSeleccionada();
    const query = new URLSearchParams({ dias: '7' });
    if (moneda) query.set('moneda_id', moneda);

    try {
        const items = await get(`deudas-mensuales/proximas?${query.toString()}`);
        renderPagosMensuales(items);
    } catch (error) {
        console.error('Error cargando pagos mensuales:', error);
        contenedor.innerHTML = `
            <div class="p-6 text-center text-sm text-slate-500">
                No se pudieron cargar los pagos mensuales.
            </div>`;
    }
}

async function abrirModalPagoMensual(cuotaId) {
    const item = pagosMensualesItems.find(pago => Number(pago.cuota_id) === Number(cuotaId));
    if (!item) return;

    const { moneda, periodo, estado } = panelPagoMensualInfo(item);
    document.getElementById('panelPagoMensualCuotaId').value = item.cuota_id;
    document.getElementById('panelPagoMensualInfo').innerHTML = `
        <i class="fa-solid fa-circle-info text-slate-500 mr-1"></i>
        ${escaparHtml(item.descripcion || 'Deuda mensual')} · Cuota ${item.numero} (${periodo}) · ${estado}<br>
        <span class="text-slate-400">Monto: ${formatearDinero(item.monto, moneda)}</span>`;
    document.getElementById('panelPagoMensualFecha').value = fechaHoyISO();
    document.getElementById('panelPagoMensualDescripcion').value = '';

    await cargarSelectorCuentas('panelPagoMensualCuenta', cuentasGlobales[0]?.id || null, cuentasGlobales);
    document.getElementById('modalPagoMensual').classList.remove('hidden');
}

function cerrarModalPagoMensual() {
    document.getElementById('modalPagoMensual')?.classList.add('hidden');
}

async function confirmarPagoMensual(event) {
    event.preventDefault();

    const cuotaId = Number(document.getElementById('panelPagoMensualCuotaId').value);
    const cuentaId = Number(document.getElementById('panelPagoMensualCuenta').value);
    const fecha = document.getElementById('panelPagoMensualFecha').value;
    const descripcion = document.getElementById('panelPagoMensualDescripcion').value.trim();

    if (!cuotaId) return;
    if (!cuentaId) {
        mostrarNotificacion('Seleccioná una cuenta para el pago', 'warning');
        return;
    }

    const boton = document.getElementById('btnConfirmarPagoMensual');
    if (boton) {
        boton.disabled = true;
        boton.textContent = 'Pagando...';
    }

    try {
        await post(`deudas-mensuales/cuotas/${cuotaId}/pagar`, {
            cuenta_id: cuentaId,
            fecha: fechaParaAPI(fecha),
            descripcion: descripcion || null,
        });
        mostrarNotificacion('Cuota mensual pagada');
        cerrarModalPagoMensual();
        window.dispatchEvent(new CustomEvent('deudas-mensuales-actualizadas'));
        cargarPagosMensuales();
        cargarDashboard();
        cargarMovimientos();
    } catch (error) {
        console.error('Error pagando cuota mensual:', error);
        mostrarNotificacion(error.message || 'No se pudo pagar la cuota mensual', 'error');
    } finally {
        if (boton) {
            boton.disabled = false;
            boton.textContent = 'Confirmar pago';
        }
    }
}

// ==================== INICIALIZACIÓN ====================

function initPanel() {
    restaurarToggleDeudas();
    document.getElementById('toggleDeudas')?.addEventListener('change', () => {
        guardarToggleDeudas();
        cargarDashboard();
    });
    document.getElementById('rangoGrafico')?.addEventListener('change', renderGrafico);
    document.getElementById('filtroMoneda')?.addEventListener('change', () => {
        guardarMonedaSeleccionada();
        cargarDashboard();
        cargarMovimientos();
        cargarPagosMensuales();
    });

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

    document.getElementById('listaPagosMensuales')?.addEventListener('click', (event) => {
        const boton = event.target.closest('[data-pagar-mensual]');
        if (boton) abrirModalPagoMensual(boton.dataset.pagarMensual);
    });
    document.querySelectorAll('[data-cerrar-pago-mensual]').forEach(btn => btn.addEventListener('click', cerrarModalPagoMensual));
    document.getElementById('formPagoMensual')?.addEventListener('submit', confirmarPagoMensual);
    document.getElementById('modalPagoMensual')?.addEventListener('click', (event) => {
        if (event.target.id === 'modalPagoMensual') cerrarModalPagoMensual();
    });

    cargarSelectorCuentas('filtroCuenta').then(() => {
        const select = document.getElementById('filtroCuenta');
        if (select && select.options[0]) select.options[0].textContent = 'Todas';
    });

    cargarDatosMaestros().then(async () => {
        try {
            await sincronizarDeudasMensuales();
        } catch (error) {
            console.error('Error sincronizando cuotas mensuales:', error);
        }
        await Promise.all([
            cargarDashboard(),
            cargarMovimientos(),
            cargarPagosMensuales(),
        ]);
    });
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPanel);
} else {
    initPanel();
}
