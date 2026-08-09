
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

// ==================== INICIALIZACIÓN ====================

function initPanel() {
    document.getElementById('rangoGrafico')?.addEventListener('change', renderGrafico);
    cargarDashboard();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initPanel);
} else {
    initPanel();
}
