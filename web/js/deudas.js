// ==================== ESTADO ====================

const deudasState = {
    entidades: [],
    entidad: null,
    entidadSeleccionadaId: null,
    monedas: [],
    cuentas: [],
    monedasMap: {},
    cuentasMap: {},
    filtroMoneda: "todas",
    filtroTipoEntidad: "todas",
    busquedaEntidad: "",
    filtroDireccion: "todas",
    filtroEstado: "todas",
    filtroOrden: "vencimiento",
    historialAbierto: new Set(),
    cargaDetalleToken: 0,
    deudaObjetivoParaPago: null,
    pagoAEditar: null,
    entidadParaEliminar: null,
    deudaParaEliminar: null,
    pagoParaEliminar: null,
};

const deudasEl = id => document.getElementById(id);

let busquedaTimer = null;

// ==================== HELPERS ====================

function esc(valor) {
    return typeof escaparHtml === "function" ? escaparHtml(valor) : String(valor ?? "");
}

function aNumero(valor) {
    const numero = Number(valor);
    return Number.isFinite(numero) ? numero : 0;
}

function formatearNumero(valor) {
    return aNumero(valor).toLocaleString("es-AR", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
    });
}

function monedaInfo(monedaId) {
    return deudasState.monedasMap[Number(monedaId)] || null;
}

function monedaSimbolo(monedaId) {
    return monedaInfo(monedaId)?.simbolo || "$";
}

function formatoMoneda(monto, monedaId) {
    return `${monedaSimbolo(monedaId)} ${formatearNumero(monto)}`;
}

function formatoAgregado(monto) {
    return `Σ ${formatearNumero(monto)}`;
}

function fechaLegible(fecha) {
    return fecha ? formatearFechaLegible(String(fecha).slice(0, 10)) : "—";
}

function fechaInput(fecha) {
    return fecha ? String(fecha).slice(0, 10) : "";
}

function tipoEntidadLabel(tipo) {
    return { persona: "Persona", empresa: "Empresa", otro: "Otro" }[tipo] || "Otro";
}

function estadoLabel(estado) {
    return { pendiente: "Pendiente", vencida: "Vencida", pagada: "Pagada" }[estado] || estado;
}

function iniciales(nombre) {
    return String(nombre || "")
        .trim()
        .split(/\s+/)
        .filter(Boolean)
        .map(parte => parte[0])
        .slice(0, 2)
        .join("")
        .toUpperCase() || "?";
}

function cuentaPorId(cuentaId) {
    return deudasState.cuentasMap[Number(cuentaId)] || null;
}

function buscarDeuda(deudaId) {
    const deuda = (deudasState.entidad?.deudas || []).find(item => Number(item.id) === Number(deudaId));
    return deuda || null;
}

function abrirModal(id) {
    const modal = deudasEl(id);
    if (!modal) return;
    modal.classList.remove("hidden");
    const primerCampo = modal.querySelector("input, select, textarea");
    if (primerCampo) primerCampo.focus();
}

function cerrarModal(id) {
    deudasEl(id)?.classList.add("hidden");
}

function bloquearBoton(boton, bloqueado, texto) {
    if (!boton) return;
    boton.disabled = bloqueado;
    if (texto) boton.textContent = texto;
    boton.classList.toggle("opacity-50", bloqueado);
    boton.classList.toggle("cursor-not-allowed", bloqueado);
}

// ==================== RESUMEN GLOBAL ====================

function renderResumenGlobal() {
    const filtro = deudasState.filtroMoneda;
    const todas = filtro === "todas";
    const monedaId = todas ? null : Number(filtro);

    let aFavor = 0;
    let enContra = 0;
    let pendientesTotal = 0;

    deudasState.entidades.forEach(entidad => {
        pendientesTotal += aNumero(entidad.deudas_pendientes);
        (entidad.saldos || []).forEach(saldo => {
            if (!todas && Number(saldo.moneda_id) !== monedaId) return;
            aFavor += aNumero(saldo.a_favor);
            enContra += aNumero(saldo.en_contra);
        });
    });

    const neto = aFavor - enContra;
    const elAFavor = deudasEl("resumenAFavor");
    const elEnContra = deudasEl("resumenEnContra");
    const elNeto = deudasEl("resumenNeto");
    const elPendientes = deudasEl("resumenPendientes");
    const badgeNeto = deudasEl("badgeNetoIcon");

    if (elAFavor) {
        elAFavor.textContent = todas ? formatoAgregado(aFavor) : formatoMoneda(aFavor, monedaId);
        elAFavor.title = todas ? "Suma nominal de todas las monedas, sin conversión" : "";
    }
    if (elEnContra) {
        elEnContra.textContent = todas ? formatoAgregado(enContra) : formatoMoneda(enContra, monedaId);
        elEnContra.title = todas ? "Suma nominal de todas las monedas, sin conversión" : "";
    }
    if (elNeto) {
        const signo = neto > 0 ? "+" : neto < 0 ? "-" : "";
        elNeto.textContent = `${signo}${todas ? formatoAgregado(Math.abs(neto)) : formatoMoneda(Math.abs(neto), monedaId)}`;
        elNeto.title = todas ? "Suma nominal de todas las monedas, sin conversión" : "";
        elNeto.className = neto > 0
            ? "text-lg sm:text-2xl font-bold text-emerald-400 tracking-tight"
            : neto < 0
                ? "text-lg sm:text-2xl font-bold text-rose-400 tracking-tight"
                : "text-lg sm:text-2xl font-bold text-slate-200 tracking-tight";
    }
    if (badgeNeto) {
        badgeNeto.className = neto > 0
            ? "w-8 h-8 rounded-lg bg-emerald-500/10 text-emerald-400 flex items-center justify-center text-sm border border-emerald-500/20"
            : neto < 0
                ? "w-8 h-8 rounded-lg bg-rose-500/10 text-rose-400 flex items-center justify-center text-sm border border-rose-500/20"
                : "w-8 h-8 rounded-lg bg-slate-700/60 text-slate-300 flex items-center justify-center text-sm border border-slate-700";
    }
    if (elPendientes) elPendientes.textContent = String(pendientesTotal);
}

// ==================== LISTA DE ENTIDADES ====================

function saldoEntidad(entidad) {
    const filtro = deudasState.filtroMoneda;
    if (filtro !== "todas") {
        const saldo = (entidad.saldos || []).find(item => Number(item.moneda_id) === Number(filtro));
        return {
            neto: aNumero(saldo?.neto),
            monedaId: Number(filtro),
            todas: false,
        };
    }

    return {
        neto: (entidad.saldos || []).reduce((total, saldo) => total + aNumero(saldo.neto), 0),
        monedaId: null,
        todas: true,
    };
}

function renderListaEntidades() {
    const contenedor = deudasEl("listaEntidades");
    const contador = deudasEl("contadorEntidades");
    if (!contenedor) return;

    const busqueda = deudasState.busquedaEntidad.trim().toLowerCase();
    const filtradas = deudasState.entidades.filter(entidad => {
        const coincideTexto = String(entidad.nombre || "").toLowerCase().includes(busqueda)
            || String(entidad.descripcion || "").toLowerCase().includes(busqueda);
        const coincideTipo = deudasState.filtroTipoEntidad === "todas"
            || entidad.tipo === deudasState.filtroTipoEntidad;
        return coincideTexto && coincideTipo;
    });

    if (contador) contador.textContent = String(filtradas.length);

    if (deudasState.entidades.length === 0) {
        contenedor.innerHTML = `
            <div class="text-center py-10 px-4 border border-dashed border-slate-800 rounded-xl bg-slate-950/40">
                <i class="fa-solid fa-user-group text-slate-600 text-3xl mb-2"></i>
                <p class="text-sm font-semibold text-slate-300">No hay entidades todavía</p>
                <p class="text-xs text-slate-500 mt-1 mb-3">Creá la primera para empezar a organizar deudas.</p>
                <button type="button" data-accion="nueva-entidad" class="px-3.5 py-1.5 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold rounded-lg text-xs">
                    + Crear primera entidad
                </button>
            </div>`;
        return;
    }

    if (filtradas.length === 0) {
        contenedor.innerHTML = `
            <div class="text-center py-8 px-4 border border-slate-800 rounded-xl bg-slate-950/40">
                <i class="fa-solid fa-magnifying-glass text-slate-600 text-2xl mb-2"></i>
                <p class="text-xs font-semibold text-slate-300">No se encontraron entidades con ese filtro</p>
                <p class="text-[11px] text-slate-500 mt-1">Probá con otro término de búsqueda.</p>
            </div>`;
        return;
    }

    contenedor.innerHTML = filtradas.map(entidad => {
        const saldo = saldoEntidad(entidad);
        const pendientes = aNumero(entidad.deudas_pendientes);
        const seleccionada = Number(entidad.id) === Number(deudasState.entidadSeleccionadaId);
        const signo = saldo.neto > 0 ? "+" : saldo.neto < 0 ? "-" : "";
        const saldoClase = saldo.neto > 0 ? "text-emerald-400" : saldo.neto < 0 ? "text-rose-400" : "text-slate-400";
        const saldoTexto = saldo.todas
            ? formatoAgregado(Math.abs(saldo.neto))
            : formatoMoneda(Math.abs(saldo.neto), saldo.monedaId);
        const iconoTipo = entidad.tipo === "empresa" ? "fa-building" : entidad.tipo === "persona" ? "fa-user" : "fa-asterisk";
        const proximo = entidad.proximo_vencimiento ? fechaLegible(entidad.proximo_vencimiento) : null;

        return `
            <div data-entidad-id="${entidad.id}" class="p-3.5 rounded-xl border transition-all cursor-pointer ${
                seleccionada
                    ? "bg-emerald-500/5 border-emerald-500 shadow-md shadow-emerald-950/20"
                    : "bg-slate-950/60 border-slate-800 hover:border-slate-700 hover:bg-slate-950"
            }">
                <div class="flex items-start justify-between gap-3">
                    <div class="flex items-center gap-3 min-w-0">
                        <div class="w-10 h-10 rounded-xl ${
                            seleccionada
                                ? "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40"
                                : "bg-slate-800 text-slate-300 border border-slate-700"
                        } flex items-center justify-center font-bold text-sm flex-shrink-0">
                            ${esc(iniciales(entidad.nombre))}
                        </div>
                        <div class="min-w-0">
                            <h4 class="font-bold text-sm text-white truncate">${esc(entidad.nombre)}</h4>
                            <div class="flex items-center gap-2 text-[11px] text-slate-400 mt-0.5">
                                <span class="inline-flex items-center gap-1">
                                    <i class="fa-solid ${iconoTipo} text-[10px]"></i>
                                    ${tipoEntidadLabel(entidad.tipo)}
                                </span>
                                <span>•</span>
                                <span>${pendientes} ${pendientes === 1 ? "deuda" : "deudas"}</span>
                            </div>
                        </div>
                    </div>

                    <div class="text-right flex-shrink-0">
                        <div class="text-xs font-bold ${saldoClase}" title="${saldo.todas ? "Suma nominal de todas las monedas, sin conversión" : ""}">
                            ${signo}${saldoTexto}
                        </div>
                        ${proximo
                            ? `<div class="text-[10px] text-slate-500 mt-0.5" title="Próximo vencimiento">
                                   <i class="fa-regular fa-clock text-[9px]"></i> ${proximo}
                               </div>`
                            : `<div class="text-[10px] text-slate-600 mt-0.5">Al día</div>`}
                    </div>
                </div>
            </div>`;
    }).join("");
}

// ==================== DETALLE DE ENTIDAD ====================

async function cargarDetalleEntidad(entidadId, silencioso = false) {
    const token = ++deudasState.cargaDetalleToken;
    const skeleton = deudasEl("detalleSkeleton");
    const content = deudasEl("detalleContent");
    const cargaInicial = !deudasState.entidad;

    if (!entidadId) {
        deudasState.entidad = null;
        renderDetalleEntidad();
        return;
    }

    if (!silencioso) {
        if (cargaInicial) {
            skeleton?.classList.remove("hidden");
            content?.classList.add("hidden");
        } else {
            content?.classList.add("opacity-60", "pointer-events-none");
        }
    }

    try {
        const entidad = await get(`entidades/${entidadId}`);
        if (token !== deudasState.cargaDetalleToken) return;
        deudasState.entidad = entidad;
        renderDetalleEntidad();
    } catch (error) {
        if (token !== deudasState.cargaDetalleToken) return;
        deudasState.entidad = null;
        renderDetalleEntidad();
        mostrarNotificacion(error.message || "No se pudo cargar la entidad", "error");
    } finally {
        if (!silencioso) {
            if (cargaInicial) {
                skeleton?.classList.add("hidden");
                content?.classList.remove("hidden");
            } else {
                content?.classList.remove("opacity-60", "pointer-events-none");
            }
        }
    }
}

async function seleccionarEntidad(entidadId) {
    deudasState.entidadSeleccionadaId = Number(entidadId);
    renderListaEntidades();
    await cargarDetalleEntidad(entidadId);
}

function renderDetalleEntidad() {
    const real = deudasEl("detalleReal");
    const vacio = deudasEl("detalleVacio");
    const entidad = deudasState.entidad;

    if (!entidad) {
        real?.classList.add("hidden");
        vacio?.classList.remove("hidden");
        return;
    }

    vacio?.classList.add("hidden");
    real?.classList.remove("hidden");

    deudasEl("detalleNombre").textContent = entidad.nombre || "Entidad";
    deudasEl("detalleDescripcion").textContent = entidad.descripcion || "Sin descripción adicional";
    deudasEl("detalleBadgeTipo").textContent = tipoEntidadLabel(entidad.tipo);
    deudasEl("detalleAvatar").textContent = iniciales(entidad.nombre);

    renderSaldosEntidad(entidad);
    renderDeudasEntidad(entidad);
}

function renderSaldosEntidad(entidad) {
    const contenedor = deudasEl("detalleSaldosContainer");
    if (!contenedor) return;

    const saldos = [...(entidad.saldos || [])].sort((a, b) => Number(a.moneda_id) - Number(b.moneda_id));
    if (saldos.length === 0) {
        contenedor.innerHTML = `
            <div class="col-span-3 p-3 rounded-xl bg-slate-950/60 border border-slate-800 text-xs text-slate-400 text-center">
                Esta entidad no registra compromisos pendientes.
            </div>`;
        return;
    }

    contenedor.innerHTML = saldos.map(saldo => {
        const monedaId = Number(saldo.moneda_id);
        const info = monedaInfo(monedaId);
        const neto = aNumero(saldo.neto);
        const positivo = neto >= 0;

        return `
            <div class="p-3.5 rounded-xl bg-slate-950/80 border border-slate-800 flex flex-col justify-between">
                <div class="flex items-center justify-between text-xs font-semibold text-slate-400 mb-2">
                    <span>${esc(info?.nombre || `Moneda ${monedaId}`)}</span>
                    <span class="text-[11px] px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">${esc(info?.simbolo || "$")}</span>
                </div>
                <div class="space-y-1 text-xs">
                    <div class="flex justify-between text-slate-400">
                        <span>A favor:</span>
                        <span class="text-emerald-400 font-bold">${formatoMoneda(saldo.a_favor, monedaId)}</span>
                    </div>
                    <div class="flex justify-between text-slate-400">
                        <span>En contra:</span>
                        <span class="text-rose-400 font-bold">${formatoMoneda(saldo.en_contra, monedaId)}</span>
                    </div>
                    <div class="flex justify-between pt-1 border-t border-slate-800 text-xs font-bold">
                        <span class="text-slate-300">Neto:</span>
                        <span class="${positivo ? "text-emerald-400" : "text-rose-400"}">${positivo ? "+" : "-"}${formatoMoneda(Math.abs(neto), monedaId)}</span>
                    </div>
                </div>
            </div>`;
    }).join("");
}

function renderDeudasEntidad(entidad) {
    const contenedor = deudasEl("listaDeudasContainer");
    if (!contenedor) return;

    let deudas = [...(entidad.deudas || [])];

    if (deudasState.filtroDireccion !== "todas") {
        deudas = deudas.filter(deuda => deuda.direccion === deudasState.filtroDireccion);
    }
    if (deudasState.filtroEstado !== "todas") {
        deudas = deudas.filter(deuda => deuda.estado === deudasState.filtroEstado);
    }
    if (deudasState.filtroMoneda !== "todas") {
        deudas = deudas.filter(deuda => Number(deuda.moneda_id) === Number(deudasState.filtroMoneda));
    }

    if (deudasState.filtroOrden === "vencimiento") {
        deudas.sort((a, b) => String(a.vencimiento || "9999-12-31").localeCompare(String(b.vencimiento || "9999-12-31")));
    } else if (deudasState.filtroOrden === "monto") {
        deudas.sort((a, b) => aNumero(b.monto_original) - aNumero(a.monto_original));
    } else {
        deudas.sort((a, b) => String(b.fecha || "").localeCompare(String(a.fecha || "")));
    }

    if (deudas.length === 0) {
        contenedor.innerHTML = `
            <div class="p-8 text-center bg-slate-950/40 rounded-xl border border-dashed border-slate-800">
                <i class="fa-solid fa-receipt text-slate-600 text-3xl mb-2"></i>
                <p class="text-sm font-semibold text-slate-300">No hay deudas registradas con los filtros aplicados</p>
                <p class="text-xs text-slate-500 mt-1 mb-3">Probá cambiando los filtros o creá una nueva deuda.</p>
                <button type="button" data-accion="nueva-deuda" class="px-3.5 py-1.5 bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold rounded-lg text-xs">
                    + Nueva deuda
                </button>
            </div>`;
        return;
    }

    contenedor.innerHTML = deudas.map(deuda => {
        const monedaId = Number(deuda.moneda_id);
        const original = aNumero(deuda.monto_original);
        const pendiente = Math.max(0, aNumero(deuda.pendiente));
        const abonado = Math.max(0, aNumero(deuda.total_abonos));
        const porcentaje = original > 0 ? Math.min(100, Math.round((abonado / original) * 100)) : 0;
        const esCobrar = deuda.direccion === "cobrar";
        const pagos = deuda.pagos || [];
        const abierto = deudasState.historialAbierto.has(Number(deuda.id));

        let estadoClase = "bg-slate-700 text-slate-300";
        if (deuda.estado === "pendiente") estadoClase = "bg-amber-500/10 text-amber-400 border border-amber-500/30";
        if (deuda.estado === "vencida") estadoClase = "bg-rose-500/10 text-rose-400 border border-rose-500/30";

        const filasPagos = pagos.map(pago => {
            const cuenta = cuentaPorId(pago.cuenta_id);
            const monedaDistinta = cuenta && Number(cuenta.moneda_id) !== monedaId;
            return `
                <tr class="hover:bg-slate-900/60">
                    <td class="py-2 font-medium">${fechaLegible(pago.fecha)}</td>
                    <td class="py-2 font-bold text-emerald-400">${formatoMoneda(pago.monto, monedaId)}</td>
                    <td class="py-2 text-slate-400">
                        ${esc(cuenta?.nombre || `Cuenta ${pago.cuenta_id}`)}
                        ${monedaDistinta ? `<i class="fa-solid fa-triangle-exclamation text-amber-400 ml-1" title="Cuenta en otra moneda, sin conversión"></i>` : ""}
                    </td>
                    <td class="py-2 text-slate-400 truncate max-w-[140px]">${esc(pago.descripcion || "Sin nota")}</td>
                    <td class="py-2 text-right space-x-1">
                        <button type="button" data-accion="editar-pago" data-deuda-id="${deuda.id}" data-pago-id="${pago.id}" title="Editar abono" class="p-1 hover:text-white text-slate-400">
                            <i class="fa-solid fa-pen text-[11px]"></i>
                        </button>
                        <button type="button" data-accion="eliminar-pago" data-deuda-id="${deuda.id}" data-pago-id="${pago.id}" title="Eliminar abono" class="p-1 hover:text-rose-400 text-slate-400">
                            <i class="fa-solid fa-trash-can text-[11px]"></i>
                        </button>
                    </td>
                </tr>`;
        }).join("");

        return `
            <div class="bg-slate-950/70 border border-slate-800 rounded-2xl p-4 sm:p-5 transition-all hover:border-slate-700 shadow-sm" id="deudaCard-${deuda.id}">
                <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-3 border-b border-slate-800/80">
                    <div class="flex items-center gap-2 flex-wrap">
                        <span class="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-bold ${
                            esCobrar
                                ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"
                                : "bg-rose-500/10 text-rose-400 border border-rose-500/30"
                        }">
                            <i class="fa-solid ${esCobrar ? "fa-arrow-down-left" : "fa-arrow-up-right"} text-[10px]"></i>
                            ${esCobrar ? "Me deben" : "Yo debo"}
                        </span>
                        <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold ${estadoClase}">
                            ${estadoLabel(deuda.estado)}
                        </span>
                        <span class="text-xs text-slate-400">Reg: ${fechaLegible(deuda.fecha)}</span>
                    </div>

                    <div class="flex items-center gap-2">
                        ${pendiente > 0
                            ? `<button type="button" data-accion="pagar" data-deuda-id="${deuda.id}" class="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold bg-emerald-500 hover:bg-emerald-600 text-slate-950 transition-colors shadow-sm">
                                   <i class="fa-solid ${esCobrar ? "fa-arrow-down" : "fa-arrow-up"} text-[10px]"></i>
                                   <span>${esCobrar ? "Registrar cobro" : "Registrar pago"}</span>
                               </button>`
                            : `<span class="text-xs font-semibold text-slate-500 px-2 py-1 bg-slate-900 rounded-lg">
                                   <i class="fa-solid fa-check text-emerald-500"></i> Liquidada
                               </span>`}
                        <button type="button" data-accion="editar-deuda" data-deuda-id="${deuda.id}" title="Editar deuda" class="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors">
                            <i class="fa-solid fa-pen-to-square text-xs"></i>
                        </button>
                        <button type="button" data-accion="eliminar-deuda" data-deuda-id="${deuda.id}" title="Eliminar deuda" class="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors">
                            <i class="fa-solid fa-trash text-xs"></i>
                        </button>
                    </div>
                </div>

                <div class="py-3 grid grid-cols-1 md:grid-cols-12 gap-4 items-center">
                    <div class="md:col-span-7">
                        <h4 class="font-bold text-sm sm:text-base text-white">${esc(deuda.descripcion || "Deuda sin descripción")}</h4>
                        <div class="flex items-center gap-3 text-xs text-slate-400 mt-1">
                            <span>Vencimiento:
                                <strong class="${deuda.estado === "vencida" ? "text-rose-400 font-semibold" : "text-slate-300"}">${fechaLegible(deuda.vencimiento)}</strong>
                            </span>
                        </div>
                    </div>

                    <div class="md:col-span-5 flex flex-col sm:items-end justify-center">
                        <div class="flex items-baseline gap-2">
                            <span class="text-xs text-slate-400">Pendiente:</span>
                            <span class="text-lg font-bold ${esCobrar ? "text-emerald-400" : "text-rose-400"}">${formatoMoneda(pendiente, monedaId)}</span>
                        </div>
                        <div class="text-[11px] text-slate-500">Original: ${formatoMoneda(original, monedaId)}</div>
                    </div>
                </div>

                <div class="space-y-1">
                    <div class="flex justify-between text-[11px] text-slate-400 font-medium">
                        <span>Progreso de amortización: ${porcentaje}%</span>
                        <span>Abonado: ${formatoMoneda(abonado, monedaId)}</span>
                    </div>
                    <div class="w-full bg-slate-900 rounded-full h-2 overflow-hidden border border-slate-800">
                        <div class="h-full bg-emerald-500 rounded-full transition-all duration-300" style="width: ${porcentaje}%"></div>
                    </div>
                </div>

                <div class="mt-3 pt-3 border-t border-slate-900 flex items-center justify-between">
                    <button type="button" data-accion="historial" data-deuda-id="${deuda.id}" class="text-xs text-slate-400 hover:text-emerald-400 font-semibold flex items-center gap-1.5 transition-colors">
                        <i class="fa-solid fa-clock-rotate-left"></i>
                        <span>Ver historial (${pagos.length} abonos)</span>
                        <i class="fa-solid fa-chevron-down text-[10px] transition-transform ${abierto ? "rotate-180" : ""}"></i>
                    </button>
                    <span class="text-[11px] text-slate-500">ID #${deuda.id}</span>
                </div>

                <div id="historialPagos-${deuda.id}" class="${abierto ? "" : "hidden"} mt-3 pt-3 border-t border-slate-800 space-y-2">
                    ${pagos.length === 0
                        ? `<p class="text-xs text-slate-500 italic py-2">Todavía no hay pagos registrados para esta deuda.</p>`
                        : `<div class="overflow-x-auto">
                               <table class="w-full text-left text-xs">
                                   <thead>
                                       <tr class="text-slate-500 border-b border-slate-800">
                                           <th class="pb-2 font-semibold">Fecha</th>
                                           <th class="pb-2 font-semibold">Monto</th>
                                           <th class="pb-2 font-semibold">Cuenta</th>
                                           <th class="pb-2 font-semibold">Nota</th>
                                           <th class="pb-2 font-semibold text-right">Acciones</th>
                                       </tr>
                                   </thead>
                                   <tbody class="divide-y divide-slate-800/60 text-slate-300">${filasPagos}</tbody>
                               </table>
                           </div>`}
                </div>
            </div>`;
    }).join("");
}

function toggleHistorial(deudaId) {
    const id = Number(deudaId);
    const abierto = deudasState.historialAbierto.has(id);
    const contenedor = deudasEl(`historialPagos-${id}`);

    if (abierto) {
        deudasState.historialAbierto.delete(id);
        contenedor?.classList.add("hidden");
    } else {
        deudasState.historialAbierto.add(id);
        contenedor?.classList.remove("hidden");
    }

    const boton = document.querySelector(`[data-accion="historial"][data-deuda-id="${id}"]`);
    boton?.querySelector(".fa-chevron-down")?.classList.toggle("rotate-180", !abierto);
}

// ==================== MODAL ENTIDAD ====================

function abrirModalEntidad(editar = false) {
    const entidad = editar ? deudasState.entidad : null;
    if (editar && !entidad) return;

    deudasEl("errorNombreEntidad")?.classList.add("hidden");
    deudasEl("entidadEditId").value = entidad ? entidad.id : "";
    deudasEl("inputNombreEntidad").value = entidad?.nombre || "";
    deudasEl("selectTipoEntidad").value = entidad?.tipo || "persona";
    deudasEl("textareaDescripcionEntidad").value = entidad?.descripcion || "";
    deudasEl("modalEntidadTitulo").innerHTML = entidad
        ? '<i class="fa-solid fa-pen-to-square text-emerald-400"></i> <span>Editar Entidad</span>'
        : '<i class="fa-solid fa-user-plus text-emerald-400"></i> <span>Nueva Entidad</span>';

    abrirModal("modalEntidad");
}

async function guardarEntidad(event) {
    event.preventDefault();

    const id = deudasEl("entidadEditId").value;
    const nombre = deudasEl("inputNombreEntidad").value.trim();
    const tipo = deudasEl("selectTipoEntidad").value;
    const descripcion = deudasEl("textareaDescripcionEntidad").value.trim();

    if (!nombre) {
        deudasEl("errorNombreEntidad")?.classList.remove("hidden");
        deudasEl("inputNombreEntidad")?.focus();
        return;
    }

    const boton = deudasEl("btnGuardarEntidad");
    const textoOriginal = boton?.textContent || "Guardar entidad";
    bloquearBoton(boton, true, "Guardando...");

    try {
        if (id) {
            await putRequest(`entidades/${id}`, { nombre, tipo, descripcion });
            mostrarNotificacion(`Entidad "${nombre}" actualizada.`);
        } else {
            const creada = await post("entidades/", { nombre, tipo, descripcion });
            deudasState.entidadSeleccionadaId = creada.id;
            mostrarNotificacion(`Entidad "${nombre}" creada.`);
        }
        cerrarModal("modalEntidad");
        await recargarTodo();
    } catch (error) {
        mostrarNotificacion(error.message || "No se pudo guardar la entidad", "error");
    } finally {
        bloquearBoton(boton, false, textoOriginal);
    }
}

// ==================== MODAL DEUDA ====================

function poblarSelectEntidadesDeuda(seleccionadaId) {
    const select = deudasEl("selectEntidadDeuda");
    if (!select) return;

    if (deudasState.entidades.length === 0) {
        select.innerHTML = '<option value="">Sin entidades</option>';
        select.disabled = true;
        return;
    }

    select.disabled = false;
    select.innerHTML = deudasState.entidades
        .map(entidad => `<option value="${entidad.id}">${esc(entidad.nombre)} (${tipoEntidadLabel(entidad.tipo).toLowerCase()})</option>`)
        .join("");

    if (seleccionadaId != null) select.value = String(seleccionadaId);
}

function setDireccionDeuda(direccion) {
    deudasEl("inputDireccionDeuda").value = direccion;
    const botonCobrar = deudasEl("btnDirCobrar");
    const botonPagar = deudasEl("btnDirPagar");

    if (direccion === "cobrar") {
        botonCobrar.className = "py-2 px-3 rounded-lg text-xs font-bold flex items-center justify-center gap-2 text-emerald-400 bg-emerald-500/10 border border-emerald-500/40 transition-all";
        botonPagar.className = "py-2 px-3 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 text-slate-400 hover:text-slate-200 transition-all";
    } else {
        botonPagar.className = "py-2 px-3 rounded-lg text-xs font-bold flex items-center justify-center gap-2 text-rose-400 bg-rose-500/10 border border-rose-500/40 transition-all";
        botonCobrar.className = "py-2 px-3 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 text-slate-400 hover:text-slate-200 transition-all";
    }

    actualizarExplicacionMovimiento();
}

function actualizarExplicacionMovimiento() {
    const direccion = deudasEl("inputDireccionDeuda").value;
    const texto = deudasEl("textoMovimientoDinamico");
    const selectCuenta = deudasEl("selectCuentaInicial");
    const selectMoneda = deudasEl("selectMonedaDeuda");
    const cuenta = cuentaPorId(selectCuenta?.value);
    const advertencia = deudasEl("advertenciaMonedaCuenta");

    if (texto) {
        if (direccion === "cobrar") {
            texto.className = "p-2.5 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs flex items-center gap-2";
            texto.innerHTML = '<i class="fa-solid fa-arrow-up text-xs"></i> <span>El dinero sale de tu cuenta hacia la entidad.</span>';
        } else {
            texto.className = "p-2.5 rounded-lg bg-rose-500/10 border border-rose-500/20 text-rose-400 text-xs flex items-center gap-2";
            texto.innerHTML = '<i class="fa-solid fa-arrow-down text-xs"></i> <span>El dinero entra a tu cuenta desde la entidad.</span>';
        }
    }

    const monedaDeuda = Number(selectMoneda?.value);
    const monedaDistinta = cuenta && monedaDeuda && Number(cuenta.moneda_id) !== monedaDeuda;
    advertencia?.classList.toggle("hidden", !monedaDistinta);
}

async function abrirModalDeuda(deudaId = null) {
    if (deudasState.entidades.length === 0) {
        mostrarNotificacion("Primero creá una entidad para registrar deudas.", "warning");
        abrirModalEntidad(false);
        return;
    }

    const deuda = deudaId ? buscarDeuda(deudaId) : null;
    if (deudaId && !deuda) {
        mostrarNotificacion("No se encontró la deuda seleccionada.", "error");
        return;
    }

    const tieneCuentas = deudasState.cuentas.length > 0;
    const esEdicion = Boolean(deuda);
    const titulo = deudasEl("modalDeudaTitulo");
    const botonSubmit = deudasEl("btnSubmitDeuda");
    const check = deudasEl("checkMovimientoInicial");
    const contenedorCuenta = deudasEl("contenedorCuentaInicial");
    const avisoSinCuentas = deudasEl("avisoSinCuentasInicial");
    const avisoBloqueo = deudasEl("avisoEdicionBloqueada");
    const bloqueMovimiento = deudasEl("bloqueMovimientoInicial");
    const inputMonto = deudasEl("inputMontoDeuda");
    const selectMoneda = deudasEl("selectMonedaDeuda");

    deudasEl("errorMontoDeuda")?.classList.add("hidden");
    poblarSelectEntidadesDeuda(esEdicion ? deuda.entidad_id : deudasState.entidadSeleccionadaId);

    if (esEdicion) {
        titulo.innerHTML = '<i class="fa-solid fa-pen-to-square text-emerald-400"></i> <span>Editar Deuda</span>';
        deudasEl("deudaEditId").value = deuda.id;
        deudasEl("selectEntidadDeuda").disabled = true;
        setDireccionDeuda(deuda.direccion);
        inputMonto.value = deuda.monto_original;
        await cargarSelectorMonedas("selectMonedaDeuda", deuda.moneda_id, deudasState.monedas);
        deudasEl("inputFechaDeuda").value = fechaInput(deuda.fecha) || fechaHoyISO();
        deudasEl("inputVencimientoDeuda").value = fechaInput(deuda.vencimiento);
        deudasEl("textareaDescripcionDeuda").value = deuda.descripcion || "";

        const tienePagos = (deuda.pagos || []).length > 0;
        inputMonto.disabled = tienePagos;
        selectMoneda.disabled = tienePagos;
        deudasEl("btnDirCobrar").disabled = tienePagos;
        deudasEl("btnDirPagar").disabled = tienePagos;
        avisoBloqueo?.classList.toggle("hidden", !tienePagos);
        bloqueMovimiento?.classList.add("hidden");
        botonSubmit.textContent = "Guardar cambios";
    } else {
        titulo.innerHTML = '<i class="fa-solid fa-file-invoice-dollar text-emerald-400"></i> <span>Nueva Deuda</span>';
        deudasEl("deudaEditId").value = "";
        deudasEl("selectEntidadDeuda").disabled = false;
        setDireccionDeuda("cobrar");
        inputMonto.value = "";
        inputMonto.disabled = false;
        const monedaInicial = deudasState.filtroMoneda === "todas"
            ? (deudasState.monedas[0]?.id || null)
            : Number(deudasState.filtroMoneda);
        await cargarSelectorMonedas("selectMonedaDeuda", monedaInicial, deudasState.monedas);
        selectMoneda.disabled = false;
        deudasEl("btnDirCobrar").disabled = false;
        deudasEl("btnDirPagar").disabled = false;
        deudasEl("inputFechaDeuda").value = fechaHoyISO();
        deudasEl("inputVencimientoDeuda").value = "";
        deudasEl("textareaDescripcionDeuda").value = "";

        await cargarSelectorCuentas("selectCuentaInicial", null, deudasState.cuentas);
        check.disabled = !tieneCuentas;
        deudasEl("selectCuentaInicial").disabled = !tieneCuentas;
        avisoSinCuentas?.classList.toggle("hidden", tieneCuentas);
        contenedorCuenta.classList.toggle("hidden", !tieneCuentas);
        check.checked = tieneCuentas;
        if (tieneCuentas) contenedorCuenta.classList.remove("hidden");

        avisoBloqueo?.classList.add("hidden");
        bloqueMovimiento?.classList.remove("hidden");
        botonSubmit.textContent = "Crear deuda";
    }

    actualizarExplicacionMovimiento();
    abrirModal("modalDeuda");
}

async function guardarDeuda(event) {
    event.preventDefault();

    const deudaId = deudasEl("deudaEditId").value ? Number(deudasEl("deudaEditId").value) : null;
    const deudaExistente = deudaId ? buscarDeuda(deudaId) : null;
    const tienePagos = Boolean(deudaExistente && (deudaExistente.pagos || []).length > 0);
    const entidadId = deudaId
        ? deudaExistente?.entidad_id
        : Number(deudasEl("selectEntidadDeuda").value);
    const direccion = deudasEl("inputDireccionDeuda").value;
    const monto = Number(deudasEl("inputMontoDeuda").value);
    const monedaId = Number(deudasEl("selectMonedaDeuda").value);
    const fecha = deudasEl("inputFechaDeuda").value;
    const vencimiento = deudasEl("inputVencimientoDeuda").value;
    const descripcion = deudasEl("textareaDescripcionDeuda").value.trim();

    if (!entidadId) {
        mostrarNotificacion("Seleccioná una entidad.", "warning");
        return;
    }
    if (!Number.isFinite(monto) || monto <= 0) {
        deudasEl("errorMontoDeuda")?.classList.remove("hidden");
        deudasEl("inputMontoDeuda")?.focus();
        return;
    }
    if (!monedaId) {
        mostrarNotificacion("Seleccioná una moneda.", "warning");
        return;
    }

    const boton = deudasEl("btnSubmitDeuda");
    const textoOriginal = boton?.textContent || "Guardar";
    bloquearBoton(boton, true, "Guardando...");

    try {
        if (deudaId) {
            const payload = {
                descripcion,
                fecha: fecha ? fechaParaAPI(fecha) : null,
                vencimiento: vencimiento ? fechaParaAPI(vencimiento) : null,
            };
            if (!tienePagos) {
                payload.monto_original = monto;
                payload.moneda_id = monedaId;
                payload.direccion = direccion;
            }
            await putRequest(`deudas/${deudaId}`, payload);
            mostrarNotificacion("Deuda actualizada.");
        } else {
            const check = deudasEl("checkMovimientoInicial");
            const cuentaId = check.checked ? Number(deudasEl("selectCuentaInicial").value) : null;
            if (check.checked && !cuentaId) {
                mostrarNotificacion("Seleccioná la cuenta para el movimiento inicial.", "warning");
                return;
            }

            const payload = {
                entidad_id: entidadId,
                direccion,
                monto_original: monto,
                moneda_id: monedaId,
                descripcion,
                fecha: fecha ? fechaParaAPI(fecha) : null,
                vencimiento: vencimiento ? fechaParaAPI(vencimiento) : null,
                cuenta_inicial_id: cuentaId,
            };
            await post("deudas/", payload);
            mostrarNotificacion(`Deuda de ${formatoMoneda(monto, monedaId)} registrada.`);
        }

        cerrarModal("modalDeuda");
        deudasState.entidadSeleccionadaId = entidadId;
        await recargarTodo();
    } catch (error) {
        mostrarNotificacion(error.message || "No se pudo guardar la deuda", "error");
    } finally {
        bloquearBoton(boton, false, textoOriginal);
    }
}

// ==================== MODAL PAGO ====================

function actualizarAvisoMonedaPago() {
    const cuenta = cuentaPorId(deudasEl("selectCuentaPago")?.value);
    const deuda = deudasState.deudaObjetivoParaPago;
    const aviso = deudasEl("avisoMonedaPago");
    const distinta = cuenta && deuda && Number(cuenta.moneda_id) !== Number(deuda.moneda_id);
    aviso?.classList.toggle("hidden", !distinta);
}

function calcularRestantePago() {
    const deuda = deudasState.deudaObjetivoParaPago;
    if (!deuda) return;

    const monto = Number(deudasEl("inputMontoPago").value);
    const disponible = aNumero(deuda.pendiente) + (deudasState.pagoAEditar ? aNumero(deudasState.pagoAEditar.monto) : 0);
    const excede = Number.isFinite(monto) && monto > disponible + 1e-9;
    const cuentaSeleccionada = Boolean(deudasEl("selectCuentaPago")?.value);
    const valido = Number.isFinite(monto) && monto > 0 && !excede && cuentaSeleccionada;

    deudasEl("errorMontoPago")?.classList.toggle("hidden", !excede);
    deudasEl("avisoCancelacion")?.classList.toggle("hidden", !(valido && Math.abs(disponible - monto) < 1e-9));

    const restante = Math.max(0, disponible - (Number.isFinite(monto) ? monto : 0));
    const contexto = deudasEl("pagoContextoRestante");
    if (contexto) {
        if (excede) {
            contexto.textContent = "Monto excedido";
            contexto.className = "font-bold text-rose-400";
        } else {
            contexto.textContent = formatoMoneda(restante, deuda.moneda_id);
            contexto.className = "font-bold text-emerald-400";
        }
    }

    bloquearBoton(deudasEl("btnSubmitPago"), !valido);
}

async function abrirModalPago(deudaId, pagoId = null) {
    const deuda = buscarDeuda(deudaId);
    if (!deuda) {
        mostrarNotificacion("No se encontró la deuda seleccionada.", "error");
        return;
    }

    const pago = pagoId ? (deuda.pagos || []).find(item => Number(item.id) === Number(pagoId)) : null;
    if (pagoId && !pago) {
        mostrarNotificacion("No se encontró el abono seleccionado.", "error");
        return;
    }

    deudasState.deudaObjetivoParaPago = deuda;
    deudasState.pagoAEditar = pago;

    const tieneCuentas = deudasState.cuentas.length > 0;
    const cuentaSeleccionada = pago ? pago.cuenta_id : deudasState.cuentas[0]?.id;
    await cargarSelectorCuentas("selectCuentaPago", cuentaSeleccionada, deudasState.cuentas);

    const esCobrar = deuda.direccion === "cobrar";
    const titulo = deudasEl("modalPagoTitulo");
    titulo.innerHTML = pago
        ? '<i class="fa-solid fa-pen-to-square text-emerald-400"></i> <span>Editar Abono</span>'
        : esCobrar
            ? '<i class="fa-solid fa-arrow-down-left text-emerald-400"></i> <span>Registrar Cobro</span>'
            : '<i class="fa-solid fa-arrow-up-right text-rose-400"></i> <span>Registrar Pago</span>';

    deudasEl("pagoDeudaId").value = deuda.id;
    deudasEl("pagoEditId").value = pago ? pago.id : "";
    deudasEl("pagoContextoDeuda").textContent = deuda.descripcion || "Deuda sin descripción";
    deudasEl("pagoContextoPendiente").textContent = formatoMoneda(deuda.pendiente, deuda.moneda_id);
    deudasEl("inputMontoPago").value = pago ? pago.monto : "";
    deudasEl("inputFechaPago").value = pago ? fechaInput(pago.fecha) : fechaHoyISO();
    deudasEl("textareaNotaPago").value = pago?.descripcion || "";

    deudasEl("selectCuentaPago").disabled = !tieneCuentas;
    deudasEl("avisoSinCuentasPago")?.classList.toggle("hidden", tieneCuentas);
    deudasEl("btnSubmitPago").textContent = pago
        ? "Guardar cambios"
        : esCobrar ? "Registrar cobro" : "Registrar pago";

    actualizarAvisoMonedaPago();
    calcularRestantePago();
    abrirModal("modalPago");
}

async function guardarPago(event) {
    event.preventDefault();

    const deuda = deudasState.deudaObjetivoParaPago;
    if (!deuda) return;

    const monto = Number(deudasEl("inputMontoPago").value);
    const cuentaId = Number(deudasEl("selectCuentaPago").value);
    const fecha = deudasEl("inputFechaPago").value;
    const nota = deudasEl("textareaNotaPago").value.trim();
    const disponible = aNumero(deuda.pendiente) + (deudasState.pagoAEditar ? aNumero(deudasState.pagoAEditar.monto) : 0);

    if (!Number.isFinite(monto) || monto <= 0) {
        mostrarNotificacion("Ingresá un monto mayor a 0.", "warning");
        return;
    }
    if (monto > disponible + 1e-9) {
        mostrarNotificacion("El monto no puede superar el pendiente de la deuda.", "error");
        return;
    }
    if (!cuentaId) {
        mostrarNotificacion("Seleccioná una cuenta para registrar el movimiento.", "warning");
        return;
    }

    const boton = deudasEl("btnSubmitPago");
    const textoOriginal = boton?.textContent || "Guardar";
    bloquearBoton(boton, true, "Guardando...");

    try {
        const payload = {
            monto,
            cuenta_id: cuentaId,
            fecha: fecha ? fechaParaAPI(fecha) : null,
            descripcion: nota,
        };

        let respuesta;
        if (deudasState.pagoAEditar) {
            respuesta = await putRequest(`deudas/${deuda.id}/pagos/${deudasState.pagoAEditar.id}`, payload);
            mostrarNotificacion("Abono actualizado.");
        } else {
            respuesta = await post(`deudas/${deuda.id}/pagos`, payload);
            mostrarNotificacion(
                deuda.direccion === "cobrar"
                    ? `Cobro de ${formatoMoneda(monto, deuda.moneda_id)} registrado.`
                    : `Pago de ${formatoMoneda(monto, deuda.moneda_id)} registrado.`
            );
        }

        if (respuesta?.moneda_distinta) {
            mostrarNotificacion("La cuenta usa una moneda distinta. No se aplicó conversión.", "warning");
        }

        cerrarModal("modalPago");
        await recargarTodo();
    } catch (error) {
        mostrarNotificacion(error.message || "No se pudo registrar el abono", "error");
    } finally {
        bloquearBoton(boton, false, textoOriginal);
    }
}

// ==================== ELIMINACIONES ====================

function abrirEliminarEntidad() {
    const entidad = deudasState.entidad;
    if (!entidad) return;

    deudasState.entidadParaEliminar = entidad;
    const tieneDeudas = (entidad.deudas || []).length > 0;
    deudasEl("eliminarEntidadBloqueado")?.classList.toggle("hidden", !tieneDeudas);
    deudasEl("eliminarEntidadPermitido")?.classList.toggle("hidden", tieneDeudas);
    deudasEl("nombreEntidadBloqueada").textContent = entidad.nombre;
    deudasEl("nombreEntidadAEliminar").textContent = entidad.nombre;

    abrirModal("modalEliminarEntidad");
}

async function confirmarEliminarEntidad() {
    const entidad = deudasState.entidadParaEliminar;
    if (!entidad) return;

    const boton = deudasEl("btnConfirmarEliminarEntidad");
    bloquearBoton(boton, true, "Eliminando...");

    try {
        await deleteRequest(`entidades/${entidad.id}`);
        mostrarNotificacion(`Entidad "${entidad.nombre}" eliminada.`);
        cerrarModal("modalEliminarEntidad");
        deudasState.entidadSeleccionadaId = null;
        deudasState.entidad = null;
        deudasState.entidadParaEliminar = null;
        await recargarTodo();
    } catch (error) {
        mostrarNotificacion(error.message || "No se pudo eliminar la entidad", "error");
    } finally {
        bloquearBoton(boton, false, "Eliminar");
    }
}

function abrirEliminarDeuda(deudaId) {
    const deuda = buscarDeuda(deudaId);
    if (!deuda) return;

    deudasState.deudaParaEliminar = deuda;
    deudasEl("detalleDeudaEliminar").innerHTML = `
        <strong>${esc(deuda.descripcion || "Deuda sin descripción")}</strong> ·
        Original: ${formatoMoneda(deuda.monto_original, deuda.moneda_id)} ·
        Pendiente: ${formatoMoneda(deuda.pendiente, deuda.moneda_id)}`;

    abrirModal("modalEliminarDeuda");
}

async function confirmarEliminarDeuda() {
    const deuda = deudasState.deudaParaEliminar;
    if (!deuda) return;

    const boton = deudasEl("btnConfirmarEliminarDeuda");
    bloquearBoton(boton, true, "Eliminando...");

    try {
        await deleteRequest(`deudas/${deuda.id}`);
        mostrarNotificacion("Deuda eliminada y saldos revertidos.");
        cerrarModal("modalEliminarDeuda");
        deudasState.deudaParaEliminar = null;
        deudasState.historialAbierto.delete(Number(deuda.id));
        await recargarTodo();
    } catch (error) {
        mostrarNotificacion(error.message || "No se pudo eliminar la deuda", "error");
    } finally {
        bloquearBoton(boton, false, "Eliminar deuda");
    }
}

function abrirEliminarPago(deudaId, pagoId) {
    const deuda = buscarDeuda(deudaId);
    const pago = deuda ? (deuda.pagos || []).find(item => Number(item.id) === Number(pagoId)) : null;
    if (!deuda || !pago) return;

    deudasState.pagoParaEliminar = { deuda, pago };
    const cuenta = cuentaPorId(pago.cuenta_id);
    deudasEl("detallePagoEliminar").innerHTML = `
        Monto: <strong>${formatoMoneda(pago.monto, deuda.moneda_id)}</strong> ·
        Fecha: ${fechaLegible(pago.fecha)} ·
        Cuenta: ${esc(cuenta?.nombre || `Cuenta ${pago.cuenta_id}`)}`;

    abrirModal("modalEliminarPago");
}

async function confirmarEliminarPago() {
    const objetivo = deudasState.pagoParaEliminar;
    if (!objetivo) return;

    const boton = deudasEl("btnConfirmarEliminarPago");
    bloquearBoton(boton, true, "Eliminando...");

    try {
        await deleteRequest(`deudas/${objetivo.deuda.id}/pagos/${objetivo.pago.id}`);
        mostrarNotificacion("Pago eliminado y saldo restaurado.");
        cerrarModal("modalEliminarPago");
        deudasState.pagoParaEliminar = null;
        await recargarTodo();
    } catch (error) {
        mostrarNotificacion(error.message || "No se pudo eliminar el pago", "error");
    } finally {
        bloquearBoton(boton, false, "Eliminar pago");
    }
}

// ==================== CARGA Y EVENTOS ====================

async function recargarTodo() {
    const entidades = await get("entidades/");
    deudasState.entidades = Array.isArray(entidades) ? entidades : [];

    const existeSeleccionada = deudasState.entidades.some(
        entidad => Number(entidad.id) === Number(deudasState.entidadSeleccionadaId)
    );
    if (!existeSeleccionada) {
        deudasState.entidadSeleccionadaId = deudasState.entidades[0]?.id ?? null;
    }

    renderResumenGlobal();
    renderListaEntidades();

    if (deudasState.entidadSeleccionadaId != null) {
        await cargarDetalleEntidad(deudasState.entidadSeleccionadaId, true);
    } else {
        deudasState.entidad = null;
        renderDetalleEntidad();
    }
}

function configurarFiltroMonedas() {
    const select = deudasEl("filtroMoneda");
    if (!select) return;

    const guardado = localStorage.getItem("filtroMoneda");
    const existeGuardado = guardado === "todas"
        || deudasState.monedas.some(moneda => String(moneda.id) === String(guardado));

    deudasState.filtroMoneda = existeGuardado
        ? guardado
        : deudasState.monedas[0] ? String(deudasState.monedas[0].id) : "todas";

    select.innerHTML = '<option value="todas">Todas las monedas</option>'
        + deudasState.monedas
            .map(moneda => `<option value="${moneda.id}">${esc(moneda.nombre)} (${esc(moneda.simbolo)})</option>`)
            .join("");
    select.value = deudasState.filtroMoneda;
}

function actualizarTabsTipo() {
    document.querySelectorAll(".tab-tipo").forEach(boton => {
        const activo = boton.dataset.tipo === deudasState.filtroTipoEntidad;
        boton.className = activo
            ? "tab-tipo flex-1 py-1.5 text-xs font-semibold rounded-lg text-slate-200 bg-slate-800 shadow-sm transition-all text-center"
            : "tab-tipo flex-1 py-1.5 text-xs font-semibold rounded-lg text-slate-400 hover:text-slate-200 transition-all text-center";
    });
}

async function cargarCatalogos() {
    const [monedas, cuentas] = await Promise.all([
        get("monedas/"),
        get("cuentas/"),
    ]);

    deudasState.monedas = Array.isArray(monedas) ? monedas : [];
    deudasState.cuentas = Array.isArray(cuentas) ? cuentas : [];
    deudasState.monedasMap = Object.fromEntries(
        deudasState.monedas.map(moneda => [Number(moneda.id), moneda])
    );
    deudasState.cuentasMap = Object.fromEntries(
        deudasState.cuentas.map(cuenta => [Number(cuenta.id), cuenta])
    );

    configurarFiltroMonedas();
}

function enlazarEventos() {
    deudasEl("btnNuevaEntidad")?.addEventListener("click", () => abrirModalEntidad(false));
    deudasEl("btnNuevaEntidadMini")?.addEventListener("click", () => abrirModalEntidad(false));
    deudasEl("btnEditarEntidad")?.addEventListener("click", () => abrirModalEntidad(true));
    deudasEl("btnEliminarEntidad")?.addEventListener("click", abrirEliminarEntidad);
    deudasEl("btnNuevaDeuda")?.addEventListener("click", () => abrirModalDeuda());

    deudasEl("formEntidad")?.addEventListener("submit", guardarEntidad);
    deudasEl("formDeuda")?.addEventListener("submit", guardarDeuda);
    deudasEl("formPago")?.addEventListener("submit", guardarPago);

    deudasEl("btnConfirmarEliminarEntidad")?.addEventListener("click", confirmarEliminarEntidad);
    deudasEl("btnConfirmarEliminarDeuda")?.addEventListener("click", confirmarEliminarDeuda);
    deudasEl("btnConfirmarEliminarPago")?.addEventListener("click", confirmarEliminarPago);

    deudasEl("btnDirCobrar")?.addEventListener("click", () => setDireccionDeuda("cobrar"));
    deudasEl("btnDirPagar")?.addEventListener("click", () => setDireccionDeuda("pagar"));

    deudasEl("checkMovimientoInicial")?.addEventListener("change", event => {
        const contenedor = deudasEl("contenedorCuentaInicial");
        if (deudasState.cuentas.length === 0) {
            event.target.checked = false;
            contenedor?.classList.remove("hidden");
        } else {
            contenedor?.classList.toggle("hidden", !event.target.checked);
        }
        actualizarExplicacionMovimiento();
    });

    deudasEl("selectMonedaDeuda")?.addEventListener("change", actualizarExplicacionMovimiento);
    deudasEl("selectCuentaInicial")?.addEventListener("change", actualizarExplicacionMovimiento);
    deudasEl("selectCuentaPago")?.addEventListener("change", () => {
        actualizarAvisoMonedaPago();
        calcularRestantePago();
    });
    deudasEl("inputMontoPago")?.addEventListener("input", calcularRestantePago);

    deudasEl("filtroMoneda")?.addEventListener("change", event => {
        deudasState.filtroMoneda = event.target.value;
        localStorage.setItem("filtroMoneda", deudasState.filtroMoneda);
        renderResumenGlobal();
        renderListaEntidades();
        renderDetalleEntidad();
    });

    deudasEl("buscarEntidad")?.addEventListener("input", event => {
        deudasState.busquedaEntidad = event.target.value;
        clearTimeout(busquedaTimer);
        busquedaTimer = setTimeout(renderListaEntidades, 150);
    });

    document.querySelectorAll(".tab-tipo").forEach(boton => {
        boton.addEventListener("click", () => {
            deudasState.filtroTipoEntidad = boton.dataset.tipo;
            actualizarTabsTipo();
            renderListaEntidades();
        });
    });

    deudasEl("filtroDireccion")?.addEventListener("change", event => {
        deudasState.filtroDireccion = event.target.value;
        renderDeudasEntidad(deudasState.entidad);
    });
    deudasEl("filtroEstado")?.addEventListener("change", event => {
        deudasState.filtroEstado = event.target.value;
        renderDeudasEntidad(deudasState.entidad);
    });
    deudasEl("filtroOrden")?.addEventListener("change", event => {
        deudasState.filtroOrden = event.target.value;
        renderDeudasEntidad(deudasState.entidad);
    });

    deudasEl("listaEntidades")?.addEventListener("click", event => {
        if (event.target.closest('[data-accion="nueva-entidad"]')) {
            abrirModalEntidad(false);
            return;
        }
        const tarjeta = event.target.closest("[data-entidad-id]");
        if (tarjeta) seleccionarEntidad(Number(tarjeta.dataset.entidadId));
    });

    deudasEl("listaDeudasContainer")?.addEventListener("click", event => {
        const accion = event.target.closest("[data-accion]");
        if (!accion) return;

        const tipo = accion.dataset.accion;
        const deudaId = accion.dataset.deudaId ? Number(accion.dataset.deudaId) : null;
        const pagoId = accion.dataset.pagoId ? Number(accion.dataset.pagoId) : null;

        if (tipo === "nueva-deuda") abrirModalDeuda();
        if (tipo === "historial") toggleHistorial(deudaId);
        if (tipo === "pagar") abrirModalPago(deudaId);
        if (tipo === "editar-deuda") abrirModalDeuda(deudaId);
        if (tipo === "eliminar-deuda") abrirEliminarDeuda(deudaId);
        if (tipo === "editar-pago") abrirModalPago(deudaId, pagoId);
        if (tipo === "eliminar-pago") abrirEliminarPago(deudaId, pagoId);
    });

    document.querySelectorAll(".modal-cerrar").forEach(boton => {
        boton.addEventListener("click", () => {
            const modalId = boton.dataset.modal || boton.closest('[role="dialog"]')?.id;
            if (modalId) cerrarModal(modalId);
        });
    });

    document.querySelectorAll('[role="dialog"]').forEach(modal => {
        modal.addEventListener("click", event => {
            if (event.target === modal) cerrarModal(modal.id);
        });
    });

    window.addEventListener("keydown", event => {
        if (event.key === "Escape") {
            document.querySelectorAll('[role="dialog"]').forEach(modal => modal.classList.add("hidden"));
        }
    });
}

async function initDeudas() {
    enlazarEventos();

    try {
        await cargarCatalogos();
        await recargarTodo();
    } catch (error) {
        console.error("Error inicializando deudas:", error);
        mostrarNotificacion(error.message || "No se pudieron cargar las deudas", "error");
        const contenedor = deudasEl("listaEntidades");
        if (contenedor) {
            contenedor.innerHTML = `
                <div class="text-center py-8 px-4 border border-rose-500/30 rounded-xl bg-rose-500/5 text-rose-400 text-xs">
                    No se pudieron cargar las entidades. Revisá la conexión con la API.
                </div>`;
        }
    }
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initDeudas);
} else {
    initDeudas();
}
