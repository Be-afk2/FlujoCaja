// ==================== ESTADO ====================

const dmState = {
    deudas: [],
    detalle: null,
    seleccionadaId: null,
    monedas: [],
    cuentas: [],
    tipos: [],
    entidades: [],
    monedasMap: {},
    cuentasMap: {},
    tiposMap: {},
    entidadesMap: {},
    filtros: {
        moneda: "todas",
        tipo: "todas",
        estado: "todas",
        modalidad: "todas",
        busqueda: "",
    },
    resumen: null,
    canceladasAbierto: false,
    cargaDetalleToken: 0,
    busquedaTimer: null,
    deudaEditando: null,
    cuotaObjetivo: null,
    pagoEditando: null,
    loteItems: [],
    loteDeudaId: null,
    deudaParaCancelar: null,
    deudaParaEliminar: null,
    pagoParaEliminar: null,
    entidadInicial: null,
    nuevaAlIniciar: false,
};

const MESES_CORTOS = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"];

const dmEl = id => document.getElementById(id);

// ==================== HELPERS ====================

function dmEsc(valor) {
    return typeof escaparHtml === "function" ? escaparHtml(valor) : String(valor ?? "");
}

function dmNum(valor) {
    const numero = Number(valor);
    return Number.isFinite(numero) ? numero : 0;
}

function dmNotificarCambio() {
    window.dispatchEvent(new CustomEvent("deudas-mensuales-actualizadas"));
}

function dmFormatearNumero(valor) {
    return dmNum(valor).toLocaleString("es-AR", {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2,
    });
}

function dmMoneda(monedaId) {
    return dmState.monedasMap[Number(monedaId)] || null;
}

function dmSimbolo(monedaId) {
    return dmMoneda(monedaId)?.simbolo || "$";
}

function dmImporte(monto, monedaId) {
    return `${dmSimbolo(monedaId)} ${dmFormatearNumero(monto)}`;
}

function dmImporteFiltro(monto) {
    if (dmState.filtros.moneda === "todas") {
        return `Σ ${dmFormatearNumero(monto)}`;
    }
    return dmImporte(monto, Number(dmState.filtros.moneda));
}

function dmFechaLegible(fecha) {
    if (!fecha) return "—";
    return typeof formatearFechaLegible === "function"
        ? formatearFechaLegible(String(fecha).slice(0, 10))
        : String(fecha).slice(0, 10);
}

function dmFechaInput(fecha) {
    return fecha ? String(fecha).slice(0, 10) : "";
}

function dmHoyISO() {
    return typeof fechaHoyISO === "function"
        ? fechaHoyISO()
        : new Date().toISOString().split("T")[0];
}

function dmTipoNombre(tipoId) {
    return dmState.tiposMap[Number(tipoId)]?.nombre || `Categoría ${tipoId}`;
}

function dmEntidadNombre(entidadId) {
    if (!entidadId) return null;
    return dmState.entidadesMap[Number(entidadId)]?.nombre || `Entidad ${entidadId}`;
}

function dmCuentaNombre(cuentaId) {
    return dmState.cuentasMap[Number(cuentaId)]?.nombre || `Cuenta ${cuentaId}`;
}

function dmCuentaMoneda(cuentaId) {
    return Number(dmState.cuentasMap[Number(cuentaId)]?.moneda_id);
}

function dmModalidadLabel(modalidad) {
    return modalidad === "cuotas" ? "Plan en cuotas" : "Recurrente";
}

function dmEstadoDeudaLabel(estado) {
    return estado === "cancelada" ? "Cancelada" : "Activa";
}

function dmEstadoCuota(cuota) {
    if (cuota.estado === "pagada") return "Pagada";
    if (cuota.estado === "cancelada") return "Cancelada";
    if (String(cuota.fecha_limite) < dmHoyISO()) return "Vencida";
    if (String(cuota.fecha_aparicion) > dmHoyISO()) return "Futura";
    return "Pendiente";
}

function dmClaseEstadoCuota(cuota) {
    const estado = dmEstadoCuota(cuota);
    if (estado === "Vencida") return "bg-rose-500/10 text-rose-400 border border-rose-500/30";
    if (estado === "Pagada") return "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30";
    if (estado === "Cancelada") return "bg-slate-700 text-slate-400 border border-slate-600";
    if (estado === "Futura") return "bg-sky-500/10 text-sky-300 border border-sky-500/30";
    return "bg-amber-500/10 text-amber-300 border border-amber-500/30";
}

function dmEstadoPagoLabel(estadoPago) {
    return {
        antes_de_tiempo: "Antes de tiempo",
        al_dia: "Al día",
        atrasada: "Atrasada",
    }[estadoPago] || "";
}

function dmPeriodo(cuota) {
    const mes = MESES_CORTOS[(Number(cuota.mes) || 1) - 1] || "";
    return `${mes} ${cuota.anio}`;
}

function dmDiasRespectoHoy(fecha) {
    if (!fecha) return 0;
    const objetivo = new Date(`${String(fecha).slice(0, 10)}T00:00:00`);
    const hoy = new Date(`${dmHoyISO()}T00:00:00`);
    return Math.round((objetivo - hoy) / 86400000);
}

function dmDiasTexto(fecha) {
    const dias = dmDiasRespectoHoy(fecha);
    if (dias < 0) return `Vencida hace ${Math.abs(dias)} ${Math.abs(dias) === 1 ? "día" : "días"}`;
    if (dias === 0) return "Vence hoy";
    return `Vence en ${dias} ${dias === 1 ? "día" : "días"}`;
}

function dmBloquearBoton(boton, bloqueado, texto) {
    if (!boton) return;
    if (!boton.dataset.textoOriginal) boton.dataset.textoOriginal = boton.textContent;
    boton.disabled = bloqueado;
    boton.textContent = texto;
    boton.classList.toggle("opacity-50", bloqueado);
    boton.classList.toggle("cursor-not-allowed", bloqueado);
}

function dmRestaurarBoton(boton) {
    if (!boton) return;
    boton.disabled = false;
    if (boton.dataset.textoOriginal) boton.textContent = boton.dataset.textoOriginal;
    boton.classList.remove("opacity-50", "cursor-not-allowed");
}

function dmAbrirModal(id) {
    const modal = dmEl(id);
    if (!modal) return;
    modal.classList.remove("hidden");
    const primerCampo = modal.querySelector("input:not([type=hidden]), select, textarea");
    if (primerCampo) primerCampo.focus();
}

function dmCerrarModal(id) {
    dmEl(id)?.classList.add("hidden");
}

function dmQueryLista() {
    const params = new URLSearchParams();
    const { moneda, tipo, modalidad } = dmState.filtros;
    if (moneda !== "todas") params.set("moneda_id", moneda);
    if (tipo !== "todas") params.set("tipo_id", tipo);
    if (modalidad !== "todas") params.set("modalidad", modalidad);
    return params.toString();
}

function dmQueryResumen() {
    if (dmState.filtros.moneda === "todas") return "";
    return `moneda_id=${encodeURIComponent(dmState.filtros.moneda)}`;
}

// ==================== RESUMEN ====================

function dmRenderResumen() {
    const resumen = dmState.resumen;
    if (!resumen) return;

    const vencidas = resumen.vencidas || { cantidad: 0, monto: 0 };
    const proximas = resumen.proximas || { cantidad: 0, monto: 0 };

    dmEl("dmResumenCompromiso").textContent = dmImporteFiltro(resumen.compromiso_mensual);
    dmEl("dmResumenCompromisoSub").textContent = `${resumen.cuotas_mes || 0} ${resumen.cuotas_mes === 1 ? "cuota" : "cuotas"} este mes`;
    dmEl("dmResumenPendiente").textContent = dmImporteFiltro(resumen.pendiente_total);
    dmEl("dmResumenPendienteSub").textContent = resumen.pagado_mes > 0
        ? `Pagado este mes: ${dmImporteFiltro(resumen.pagado_mes)}`
        : "Incluye cuotas futuras de planes";

    dmEl("dmResumenVencidas").textContent = String(vencidas.cantidad || 0);
    dmEl("dmResumenVencidasSub").textContent = vencidas.cantidad > 0
        ? `Requieren atención: ${dmImporteFiltro(vencidas.monto)}`
        : "Sin cuotas vencidas";
    dmEl("dmCardVencidas").className = vencidas.cantidad > 0
        ? "p-4 md:p-5 rounded-2xl bg-rose-500/10 border border-rose-500/30 flex flex-col justify-between shadow-sm"
        : "p-4 md:p-5 rounded-2xl bg-slate-800/90 border border-slate-800 flex flex-col justify-between shadow-sm";

    dmEl("dmResumenProximas").textContent = String(proximas.cantidad || 0);
    dmEl("dmResumenProximasSub").textContent = proximas.cantidad > 0
        ? `Monto: ${dmImporteFiltro(proximas.monto)}`
        : "Sin vencimientos próximos";

    const boton = dmEl("dmBtnPagarAtrasadas");
    if (boton) {
        boton.classList.toggle("hidden", !(vencidas.cantidad > 0));
        boton.classList.toggle("inline-flex", vencidas.cantidad > 0);
        dmEl("dmBtnPagarAtrasadasTexto").textContent = `Pagar atrasadas (${vencidas.cantidad})`;
    }
}

// ==================== LISTADO ====================

function dmDeudasFiltradasPorEstado() {
    const estado = dmState.filtros.estado;
    const busqueda = dmState.filtros.busqueda.trim().toLowerCase();

    let deudas = dmState.deudas.filter(deuda => {
        if (!busqueda) return true;
        const texto = [
            deuda.descripcion,
            dmTipoNombre(deuda.tipo_id),
            dmEntidadNombre(deuda.entidad_id),
        ].join(" ").toLowerCase();
        return texto.includes(busqueda);
    });

    if (estado === "vencidas") {
        deudas = deudas.filter(deuda => deuda.estado === "activa" && dmNum(deuda.vencidas) > 0);
    } else if (estado === "activas") {
        deudas = deudas.filter(deuda => deuda.estado === "activa");
    } else if (estado === "canceladas") {
        deudas = deudas.filter(deuda => deuda.estado === "cancelada");
    }
    return deudas;
}

function dmClaveProxima(deuda) {
    return String(deuda.proxima?.fecha_limite || "9999-12-31");
}

function dmTarjetaDeuda(deuda) {
    const seleccionada = Number(deuda.id) === Number(dmState.seleccionadaId);
    const vencida = deuda.estado === "activa" && dmNum(deuda.vencidas) > 0;
    const cancelada = deuda.estado === "cancelada";
    const monedaId = Number(deuda.moneda_id);
    const progreso = deuda.modalidad === "cuotas" && dmNum(deuda.monto_total) > 0
        ? Math.min(100, Math.round((dmNum(deuda.pagado) / dmNum(deuda.monto_total)) * 100))
        : null;
    const entidad = dmEntidadNombre(deuda.entidad_id);
    const proxima = deuda.proxima;

    const borde = cancelada
        ? "border-l-slate-600"
        : vencida
            ? "border-l-rose-500"
            : "border-l-emerald-500";

    const fondo = seleccionada
        ? "bg-slate-800 ring-1 ring-emerald-500/60"
        : "bg-slate-800/70 hover:bg-slate-800";

    const estadoBadge = cancelada
        ? '<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-700 text-slate-400 border border-slate-600">Cancelada</span>'
        : vencida
            ? `<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-rose-500/15 text-rose-400 border border-rose-500/30">${deuda.vencidas} vencida${deuda.vencidas === 1 ? "" : "s"}</span>`
            : '<span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">Al día</span>';

    return `
        <div data-dm-id="${deuda.id}" class="p-3.5 rounded-xl border border-slate-800 border-l-4 ${borde} ${fondo} cursor-pointer transition-all">
            <div class="flex items-start justify-between gap-3">
                <div class="min-w-0">
                    <h4 class="font-bold text-sm text-white truncate">${dmEsc(deuda.descripcion || "Deuda mensual")}</h4>
                    <div class="flex items-center gap-1.5 flex-wrap text-[11px] text-slate-400 mt-1">
                        <span class="inline-flex items-center gap-1"><i class="fa-solid fa-tag text-[9px]"></i>${dmEsc(dmTipoNombre(deuda.tipo_id))}</span>
                        ${entidad ? `<span>•</span><span class="inline-flex items-center gap-1"><i class="fa-solid fa-user text-[9px]"></i>${dmEsc(entidad)}</span>` : ""}
                        <span>•</span>
                        <span class="px-1.5 py-0.5 rounded bg-slate-900 text-slate-300 border border-slate-700">${dmModalidadLabel(deuda.modalidad)}</span>
                    </div>
                </div>
                <div class="text-right flex-shrink-0">
                    <div class="text-sm font-bold ${cancelada ? "text-slate-400" : vencida ? "text-rose-400" : "text-emerald-400"}">
                        ${dmImporte(deuda.pendiente, monedaId)}
                    </div>
                    <div class="text-[10px] text-slate-500 mt-0.5">${deuda.modalidad === "cuotas" ? `Cuota ${dmImporte(deuda.monto_cuota, monedaId)}` : "por mes"}</div>
                </div>
            </div>

            <div class="flex items-center justify-between gap-2 mt-2.5">
                <div class="flex items-center gap-2 flex-wrap">
                    ${estadoBadge}
                    ${proxima && !cancelada
                        ? `<span class="text-[10px] text-slate-500"><i class="fa-regular fa-clock text-[9px]"></i> ${dmFechaLegible(proxima.fecha_limite)}</span>`
                        : cancelada
                            ? `<span class="text-[10px] text-slate-500">Cancelada ${dmFechaLegible(deuda.fecha_cancelacion)}</span>`
                            : '<span class="text-[10px] text-slate-500">Sin próxima cuota</span>'}
                </div>
                ${progreso !== null ? `<span class="text-[10px] text-slate-400">${progreso}% pagado</span>` : ""}
            </div>

            ${progreso !== null
                ? `<div class="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden border border-slate-800 mt-2">
                       <div class="h-full bg-emerald-500 rounded-full" style="width: ${progreso}%"></div>
                   </div>`
                : ""}
        </div>`;
}

function dmRenderLista() {
    const filtradas = dmDeudasFiltradasPorEstado();
    const vencidas = filtradas
        .filter(deuda => deuda.estado === "activa" && dmNum(deuda.vencidas) > 0)
        .sort((a, b) => dmClaveProxima(a).localeCompare(dmClaveProxima(b)));
    const activas = filtradas
        .filter(deuda => deuda.estado === "activa" && dmNum(deuda.vencidas) === 0)
        .sort((a, b) => dmClaveProxima(a).localeCompare(dmClaveProxima(b)));
    const canceladas = filtradas
        .filter(deuda => deuda.estado === "cancelada")
        .sort((a, b) => String(b.fecha_cancelacion || "").localeCompare(String(a.fecha_cancelacion || "")));

    dmEl("dmContadorLista").textContent = `${filtradas.length} ${filtradas.length === 1 ? "deuda registrada" : "deudas registradas"}`;
    dmEl("dmBadgeVencidas").textContent = String(vencidas.length);
    dmEl("dmBadgeActivas").textContent = String(activas.length);
    dmEl("dmBadgeCanceladas").textContent = String(canceladas.length);

    dmEl("dmSeccionVencidas").classList.toggle("hidden", vencidas.length === 0);
    dmEl("dmSeccionActivas").classList.toggle("hidden", activas.length === 0);
    dmEl("dmSeccionCanceladas").classList.toggle("hidden", canceladas.length === 0);

    dmEl("dmListaVencidas").innerHTML = vencidas.map(dmTarjetaDeuda).join("");
    dmEl("dmListaActivas").innerHTML = activas.map(dmTarjetaDeuda).join("");
    dmEl("dmListaCanceladas").innerHTML = canceladas.map(dmTarjetaDeuda).join("");

    const abierto = dmState.canceladasAbierto || dmState.filtros.estado === "canceladas";
    dmEl("dmListaCanceladas").classList.toggle("hidden", !abierto);
    dmEl("dmChevronCanceladas")?.classList.toggle("rotate-180", abierto);

    dmEl("dmListaVacia").classList.toggle("hidden", filtradas.length > 0);
    dmEl("dmBtnLimpiarFiltros").classList.toggle("hidden", !dmHayFiltros());
    dmEl("dmBtnLimpiarFiltros").classList.toggle("inline-flex", dmHayFiltros());
}

function dmHayFiltros() {
    const { moneda, tipo, estado, modalidad, busqueda } = dmState.filtros;
    return moneda !== "todas"
        || tipo !== "todas"
        || estado !== "todas"
        || modalidad !== "todas"
        || Boolean(busqueda.trim());
}

// ==================== DETALLE ====================

function dmMetrica(titulo, valor, detalle, icono, clase) {
    return `
        <div class="p-3.5 rounded-xl bg-slate-950/70 border border-slate-800">
            <div class="flex items-center justify-between">
                <span class="text-[10px] font-bold uppercase tracking-wider text-slate-500">${titulo}</span>
                <i class="fa-solid ${icono} text-xs ${clase}"></i>
            </div>
            <div class="text-base font-bold text-white mt-1.5">${valor}</div>
            <div class="text-[10px] text-slate-500 mt-0.5">${detalle}</div>
        </div>`;
}

function dmFilaCuota(cuota, deuda) {
    const estado = dmEstadoCuota(cuota);
    const monedaId = Number(deuda.moneda_id);
    const vencida = estado === "Vencida";
    const pagos = cuota.pagos || [];
    const fechaLimite = cuota.fecha_limite;

    let acciones = "";
    if (cuota.estado === "pendiente") {
        acciones = `
            <button type="button" data-dm-accion="pagar-cuota" data-cuota-id="${cuota.id}"
                class="inline-flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg text-[11px] font-bold bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition-colors">
                <i class="fa-solid fa-check text-[10px]"></i> Pagar
            </button>`;
    } else if (cuota.estado === "pagada" && pagos.length > 0) {
        const pago = pagos[pagos.length - 1];
        acciones = `
            <div class="flex items-center gap-1">
                <button type="button" data-dm-accion="editar-pago" data-cuota-id="${cuota.id}" data-pago-id="${pago.id}" title="Editar pago"
                    class="p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition-colors">
                    <i class="fa-solid fa-pen text-[11px]"></i>
                </button>
                <button type="button" data-dm-accion="eliminar-pago" data-cuota-id="${cuota.id}" data-pago-id="${pago.id}" title="Eliminar pago"
                    class="p-1.5 rounded-lg text-slate-400 hover:text-rose-400 hover:bg-slate-800 transition-colors">
                    <i class="fa-solid fa-trash-can text-[11px]"></i>
                </button>
            </div>`;
    }

    return `
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 p-3 rounded-xl bg-slate-950/60 border border-slate-800 ${vencida ? "border-rose-500/30" : ""}">
            <div class="flex items-center gap-3 min-w-0">
                <div class="w-9 h-9 rounded-lg ${vencida ? "bg-rose-500/10 text-rose-400 border-rose-500/30" : "bg-slate-800 text-slate-300 border-slate-700"} border flex items-center justify-center text-xs font-bold flex-shrink-0">
                    ${cuota.numero}
                </div>
                <div class="min-w-0">
                    <div class="flex items-center gap-1.5 flex-wrap">
                        <span class="text-sm font-semibold text-white">Cuota ${cuota.numero} · ${dmPeriodo(cuota)}</span>
                        <span class="px-1.5 py-0.5 rounded text-[10px] font-semibold ${dmClaseEstadoCuota(cuota)}">${estado}</span>
                    </div>
                    <div class="text-[11px] text-slate-500 mt-0.5">
                        Aparece ${dmFechaLegible(cuota.fecha_aparicion)} · Vence ${dmFechaLegible(fechaLimite)}
                        ${cuota.estado === "pendiente" ? ` · ${dmDiasTexto(fechaLimite)}` : ""}
                        ${cuota.estado === "pagada" && cuota.estado_pago ? ` · ${dmEstadoPagoLabel(cuota.estado_pago)}` : ""}
                    </div>
                </div>
            </div>

            <div class="flex items-center justify-between sm:justify-end gap-3">
                <span class="text-sm font-bold ${vencida ? "text-rose-400" : "text-slate-200"}">${dmImporte(cuota.monto, monedaId)}</span>
                ${acciones}
            </div>
        </div>`;
}

function dmGrupoCuotas(titulo, icono, claseTitulo, cuotas, deuda) {
    if (!cuotas.length) return "";
    return `
        <div class="space-y-2">
            <div class="flex items-center gap-1.5 px-1">
                <i class="fa-solid ${icono} text-xs ${claseTitulo}"></i>
                <span class="text-[11px] font-bold uppercase tracking-wider ${claseTitulo}">${titulo}</span>
                <span class="px-1.5 py-0.5 rounded-full text-[10px] bg-slate-800 text-slate-400">${cuotas.length}</span>
            </div>
            <div class="space-y-2">${cuotas.map(cuota => dmFilaCuota(cuota, deuda)).join("")}</div>
        </div>`;
}

function dmRenderDetalle() {
    const deuda = dmState.detalle;
    const vacio = dmEl("dmDetalleVacio");
    const contenido = dmEl("dmDetalleContenido");

    if (!deuda) {
        vacio.classList.remove("hidden");
        contenido.classList.add("hidden");
        contenido.innerHTML = "";
        return;
    }

    vacio.classList.add("hidden");
    contenido.classList.remove("hidden");

    const hoy = dmHoyISO();
    const cuotas = deuda.cuotas || [];
    const vencidas = cuotas
        .filter(cuota => cuota.estado === "pendiente" && String(cuota.fecha_limite) < hoy)
        .sort((a, b) => String(a.fecha_limite).localeCompare(String(b.fecha_limite)));
    const pendientes = cuotas
        .filter(cuota => cuota.estado === "pendiente" && String(cuota.fecha_limite) >= hoy)
        .sort((a, b) => String(a.fecha_limite).localeCompare(String(b.fecha_limite)));
    const pagadas = cuotas
        .filter(cuota => cuota.estado === "pagada")
        .sort((a, b) => String(b.fecha_limite).localeCompare(String(a.fecha_limite)));
    const canceladas = cuotas
        .filter(cuota => cuota.estado === "cancelada")
        .sort((a, b) => String(a.fecha_limite).localeCompare(String(b.fecha_limite)));

    const monedaId = Number(deuda.moneda_id);
    const cancelada = deuda.estado === "cancelada";
    const esPlan = deuda.modalidad === "cuotas";
    const entidad = dmEntidadNombre(deuda.entidad_id);
    const proxima = deuda.proxima;

    const pagos = cuotas
        .flatMap(cuota => (cuota.pagos || []).map(pago => ({ pago, cuota })))
        .sort((a, b) => String(b.pago.fecha).localeCompare(String(a.pago.fecha)) || Number(b.pago.id) - Number(a.pago.id));

    const accionesCabecera = [
        proxima && !cancelada
            ? `<button type="button" data-dm-accion="pagar-proxima" class="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-emerald-500 hover:bg-emerald-400 text-slate-950 transition-colors">
                   <i class="fa-solid fa-check text-[10px]"></i> Pagar cuota ${proxima.numero}
               </button>`
            : "",
        !cancelada && dmNum(deuda.vencidas) > 0
            ? `<button type="button" data-dm-accion="pagar-atrasadas" class="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold bg-rose-500/15 hover:bg-rose-500/25 text-rose-400 border border-rose-500/30 transition-colors">
                   <i class="fa-solid fa-triangle-exclamation text-[10px]"></i> Pagar atrasadas
               </button>`
            : "",
        `<button type="button" data-dm-accion="editar" class="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-slate-950 hover:bg-slate-800 border border-slate-700 text-slate-200 transition-colors">
            <i class="fa-solid fa-pen-to-square text-[10px] text-slate-400"></i> Editar
        </button>`,
        !cancelada
            ? `<button type="button" data-dm-accion="cancelar" class="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-amber-500/10 hover:bg-amber-500/20 border border-amber-500/30 text-amber-300 transition-colors">
                   <i class="fa-solid fa-ban text-[10px]"></i> Cancelar
               </button>`
            : "",
        `<button type="button" data-dm-accion="eliminar" class="inline-flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-semibold bg-rose-500/10 hover:bg-rose-500/20 border border-rose-500/30 text-rose-400 transition-colors">
            <i class="fa-solid fa-trash-can text-[10px]"></i> Eliminar
        </button>`,
    ].join("");

    const historial = pagos.length === 0
        ? '<p class="text-xs text-slate-500 italic py-2">Todavía no hay pagos registrados.</p>'
        : `<div class="overflow-x-auto">
               <table class="w-full text-left text-xs">
                   <thead>
                       <tr class="text-slate-500 border-b border-slate-800">
                           <th class="pb-2 font-semibold">Fecha</th>
                           <th class="pb-2 font-semibold">Cuota</th>
                           <th class="pb-2 font-semibold">Monto</th>
                           <th class="pb-2 font-semibold">Cuenta</th>
                           <th class="pb-2 font-semibold">Nota</th>
                           <th class="pb-2 font-semibold text-right">Acciones</th>
                       </tr>
                   </thead>
                   <tbody class="divide-y divide-slate-800/60 text-slate-300">
                       ${pagos.map(({ pago, cuota }) => {
                           const distinta = dmCuentaMoneda(pago.cuenta_id) !== monedaId;
                           return `
                               <tr class="hover:bg-slate-900/60">
                                   <td class="py-2 font-medium">${dmFechaLegible(pago.fecha)}</td>
                                   <td class="py-2 text-slate-400">${cuota.numero} · ${dmPeriodo(cuota)}</td>
                                   <td class="py-2 font-bold text-emerald-400">${dmImporte(pago.monto, monedaId)}</td>
                                   <td class="py-2 text-slate-400">
                                       ${dmEsc(dmCuentaNombre(pago.cuenta_id))}
                                       ${distinta ? '<i class="fa-solid fa-triangle-exclamation text-amber-400 ml-1" title="Cuenta en otra moneda, sin conversión"></i>' : ""}
                                   </td>
                                   <td class="py-2 text-slate-400 truncate max-w-[140px]">${dmEsc(pago.descripcion || "Sin nota")}</td>
                                   <td class="py-2 text-right space-x-1">
                                       <button type="button" data-dm-accion="editar-pago" data-cuota-id="${cuota.id}" data-pago-id="${pago.id}" title="Editar pago" class="p-1 hover:text-white text-slate-400">
                                           <i class="fa-solid fa-pen text-[11px]"></i>
                                       </button>
                                       <button type="button" data-dm-accion="eliminar-pago" data-cuota-id="${cuota.id}" data-pago-id="${pago.id}" title="Eliminar pago" class="p-1 hover:text-rose-400 text-slate-400">
                                           <i class="fa-solid fa-trash-can text-[11px]"></i>
                                       </button>
                                   </td>
                               </tr>`;
                       }).join("")}
                   </tbody>
               </table>
           </div>`;

    contenido.innerHTML = `
        <div class="bg-slate-800/80 border border-slate-800 rounded-2xl p-4 sm:p-5 space-y-4">
            <div class="flex flex-col gap-3">
                <div class="flex items-start justify-between gap-3 flex-wrap">
                    <div class="min-w-0">
                        <div class="flex items-center gap-2 flex-wrap">
                            <h2 class="text-lg sm:text-xl font-bold text-white tracking-tight">${dmEsc(deuda.descripcion || "Deuda mensual")}</h2>
                            <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold ${cancelada ? "bg-slate-700 text-slate-400 border border-slate-600" : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/30"}">
                                ${dmEstadoDeudaLabel(deuda.estado)}
                            </span>
                            <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-900 text-slate-300 border border-slate-700">${dmModalidadLabel(deuda.modalidad)}</span>
                            <span class="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-slate-900 text-slate-300 border border-slate-700">${dmEsc(dmMoneda(monedaId)?.nombre || "Moneda")}</span>
                        </div>
                        <p class="text-xs text-slate-400 mt-1">
                            ${dmEsc(dmTipoNombre(deuda.tipo_id))}
                            ${entidad ? ` · ${dmEsc(entidad)}` : ""}
                            · Inicio ${dmFechaLegible(deuda.fecha_inicio)}
                            ${esPlan ? ` · ${deuda.cuotas_totales} cuotas` : ""}
                        </p>
                    </div>
                </div>
                <div class="flex items-center gap-2 flex-wrap">${accionesCabecera}</div>
            </div>

            <div class="grid grid-cols-2 lg:grid-cols-4 gap-2.5">
                ${dmMetrica("Cuota", dmImporte(deuda.monto_cuota, monedaId), esPlan ? `Total ${dmImporte(deuda.monto_total, monedaId)}` : "Monto mensual", "fa-coins", "text-emerald-400")}
                ${dmMetrica("Pendiente", dmImporte(deuda.pendiente, monedaId), esPlan ? "Incluye cuotas futuras" : "Cuotas ya aparecidas", "fa-wallet", "text-sky-400")}
                ${dmMetrica("Pagado", dmImporte(deuda.pagado, monedaId), `${pagadas.length} ${pagadas.length === 1 ? "cuota pagada" : "cuotas pagadas"}`, "fa-circle-check", "text-emerald-400")}
                ${dmMetrica("Vencidas", String(deuda.vencidas || 0), deuda.vencidas > 0 ? dmImporte(deuda.vencidas_monto, monedaId) : "Sin atrasos", "fa-triangle-exclamation", deuda.vencidas > 0 ? "text-rose-400" : "text-slate-500")}
            </div>

            <div class="space-y-4 pt-1">
                ${dmGrupoCuotas("Cuotas vencidas", "fa-circle-exclamation", "text-rose-400", vencidas, deuda)}
                ${dmGrupoCuotas("Próximas cuotas", "fa-clock", "text-amber-300", pendientes, deuda)}
                ${dmGrupoCuotas("Cuotas pagadas", "fa-circle-check", "text-emerald-400", pagadas, deuda)}
                ${dmGrupoCuotas("Cuotas canceladas", "fa-ban", "text-slate-400", canceladas, deuda)}
                ${cuotas.length === 0 ? '<p class="text-xs text-slate-500 italic">Esta deuda todavía no tiene cuotas generadas.</p>' : ""}
            </div>

            <div class="pt-3 border-t border-slate-800 space-y-2">
                <div class="flex items-center justify-between">
                    <h4 class="text-[11px] font-bold uppercase tracking-wider text-slate-400">Historial de pagos</h4>
                    <span class="text-[10px] text-slate-500">${pagos.length} ${pagos.length === 1 ? "pago" : "pagos"}</span>
                </div>
                ${historial}
            </div>
        </div>`;
}

async function dmCargarDetalle(deudaId, silencioso = false) {
    if (!deudaId) {
        dmState.detalle = null;
        dmRenderDetalle();
        return;
    }

    const token = ++dmState.cargaDetalleToken;
    const contenido = dmEl("dmDetalleContenido");
    if (!silencioso && dmState.detalle) contenido.classList.add("opacity-60", "pointer-events-none");

    try {
        const detalle = await get(`deudas-mensuales/${deudaId}`);
        if (token !== dmState.cargaDetalleToken) return;
        dmState.detalle = detalle;
        dmRenderDetalle();
    } catch (error) {
        if (token !== dmState.cargaDetalleToken) return;
        dmState.detalle = null;
        dmRenderDetalle();
        mostrarNotificacion(error.message || "No se pudo cargar la deuda mensual", "error");
    } finally {
        if (!silencioso) contenido.classList.remove("opacity-60", "pointer-events-none");
    }
}

async function dmSeleccionarDeuda(deudaId) {
    dmState.seleccionadaId = Number(deudaId);
    dmRenderLista();
    const url = new URL(window.location.href);
    url.searchParams.set("deuda", deudaId);
    url.searchParams.delete("nueva");
    window.history.replaceState(null, "", url.toString());
    await dmCargarDetalle(deudaId);
}

// ==================== CARGA PRINCIPAL ====================

async function dmCargarTodo() {
    try {
        const query = dmQueryLista();
        const queryResumen = dmQueryResumen();
        const [deudas, resumen] = await Promise.all([
            get(`deudas-mensuales/${query ? `?${query}` : ""}`),
            get(`deudas-mensuales/resumen${queryResumen ? `?${queryResumen}` : ""}`),
        ]);

        dmState.deudas = Array.isArray(deudas) ? deudas : [];
        dmState.resumen = resumen || null;

        const existe = dmState.deudas.some(deuda => Number(deuda.id) === Number(dmState.seleccionadaId));
        if (!existe) {
            dmState.seleccionadaId = dmState.deudas[0]?.id ?? null;
        }

        dmRenderResumen();
        dmRenderLista();

        if (dmState.seleccionadaId != null) {
            await dmCargarDetalle(dmState.seleccionadaId, true);
        } else {
            dmState.detalle = null;
            dmRenderDetalle();
        }
    } catch (error) {
        console.error("Error cargando deudas mensuales:", error);
        mostrarNotificacion(error.message || "No se pudieron cargar las deudas mensuales", "error");
        dmEl("dmListaVacia").classList.remove("hidden");
    }
}

// ==================== CATÁLOGOS Y FILTROS ====================

function dmPoblarFiltros() {
    const selectMoneda = dmEl("dmFiltroMoneda");
    selectMoneda.innerHTML = '<option value="todas">Todas las monedas</option>'
        + dmState.monedas.map(moneda => `<option value="${moneda.id}">${dmEsc(moneda.nombre)} (${dmEsc(moneda.simbolo)})</option>`).join("");

    const selectTipo = dmEl("dmFiltroTipo");
    selectTipo.innerHTML = '<option value="todas">Todas las categorías</option>'
        + dmState.tipos.map(tipo => `<option value="${tipo.id}">${dmEsc(tipo.nombre)}</option>`).join("");
}

function dmPoblarEntidades() {
    const select = dmEl("dmEntidad");
    select.innerHTML = '<option value="">Sin entidad</option>'
        + dmState.entidades.map(entidad => `<option value="${entidad.id}">${dmEsc(entidad.nombre)}</option>`).join("");
}

async function dmCargarCatalogos() {
    const [monedas, cuentas, tipos, entidades] = await Promise.all([
        get("monedas/"),
        get("cuentas/"),
        get("tipos/?cantidad=50"),
        get("entidades/"),
    ]);

    dmState.monedas = Array.isArray(monedas) ? monedas : [];
    dmState.cuentas = Array.isArray(cuentas) ? cuentas : [];
    dmState.tipos = Array.isArray(tipos) ? tipos : [];
    dmState.entidades = Array.isArray(entidades) ? entidades : [];

    dmState.monedasMap = Object.fromEntries(dmState.monedas.map(moneda => [Number(moneda.id), moneda]));
    dmState.cuentasMap = Object.fromEntries(dmState.cuentas.map(cuenta => [Number(cuenta.id), cuenta]));
    dmState.tiposMap = Object.fromEntries(dmState.tipos.map(tipo => [Number(tipo.id), tipo]));
    dmState.entidadesMap = Object.fromEntries(dmState.entidades.map(entidad => [Number(entidad.id), entidad]));

    dmPoblarFiltros();
    dmPoblarEntidades();

    const selectMonedaModal = dmEl("dmMoneda");
    selectMonedaModal.innerHTML = '<option value="">Seleccionar moneda</option>'
        + dmState.monedas.map(moneda => `<option value="${moneda.id}">${dmEsc(moneda.nombre)} (${dmEsc(moneda.simbolo)})</option>`).join("");

    const selectTipoModal = dmEl("dmTipo");
    selectTipoModal.innerHTML = '<option value="">Seleccionar categoría</option>'
        + dmState.tipos.map(tipo => `<option value="${tipo.id}">${dmEsc(tipo.nombre)}</option>`).join("");

    await Promise.all([
        cargarSelectorCuentas("dmCuentaDefault", null, dmState.cuentas),
        cargarSelectorCuentas("dmPagoCuenta", null, dmState.cuentas),
        cargarSelectorCuentas("dmLoteCuenta", null, dmState.cuentas),
    ]);

    dmEl("dmCuentaDefault").options[0].textContent = "Sin cuenta predeterminada";
}

function dmLimpiarFiltros() {
    dmState.filtros = {
        moneda: "todas",
        tipo: "todas",
        estado: "todas",
        modalidad: "todas",
        busqueda: "",
    };
    dmEl("dmFiltroMoneda").value = "todas";
    dmEl("dmFiltroTipo").value = "todas";
    dmEl("dmFiltroEstado").value = "todas";
    dmEl("dmFiltroModalidad").value = "todas";
    dmEl("dmBusqueda").value = "";
    dmCargarTodo();
}

// ==================== MODAL DEUDA ====================

function dmSetModoFormulario(modo) {
    dmEl("dmModoForm").value = modo;
    const esPlan = modo === "cuotas";

    dmEl("dmCampoMontoCuota").classList.toggle("hidden", esPlan);
    dmEl("dmCamposPlan").classList.toggle("hidden", !esPlan);

    const activo = "py-2 px-3 rounded-lg text-xs font-bold flex items-center justify-center gap-2 transition-all text-emerald-400 bg-emerald-500/10 border border-emerald-500/40";
    const inactivo = "py-2 px-3 rounded-lg text-xs font-semibold flex items-center justify-center gap-2 transition-all text-slate-400 hover:text-slate-200";
    dmEl("dmTabRecurrente").className = esPlan ? inactivo : activo;
    dmEl("dmTabPlan").className = esPlan ? activo : inactivo;
}

function dmHabilitarCamposEstructura(habilitado) {
    ["dmFechaInicio", "dmMontoTotal", "dmCuotasTotales", "dmTabRecurrente", "dmTabPlan"].forEach(id => {
        const el = dmEl(id);
        if (el) el.disabled = !habilitado;
    });
    dmEl("dmAvisoEstructura").classList.toggle("hidden", habilitado);
}

async function dmAbrirModalDeuda(deudaId = null) {
    const deuda = deudaId
        ? dmState.deudas.find(item => Number(item.id) === Number(deudaId))
            || (Number(dmState.detalle?.id) === Number(deudaId) ? dmState.detalle : null)
        : null;

    if (deudaId && !deuda) {
        mostrarNotificacion("No se encontró la deuda seleccionada.", "error");
        return;
    }

    dmState.deudaEditando = deuda;
    dmEl("dmErrorDeuda").classList.add("hidden");
    dmEl("dmAvisoEstructura").classList.add("hidden");
    dmEl("dmMoneda").disabled = false;
    dmEl("dmCampoMontoCuota").querySelector("input").disabled = false;
    dmHabilitarCamposEstructura(true);
    dmEl("dmBtnGuardarDeuda").textContent = deuda ? "Guardar cambios" : "Crear deuda";
    dmEl("dmModalDeudaTitulo").innerHTML = deuda
        ? '<i class="fa-solid fa-pen-to-square text-emerald-400"></i><span>Editar deuda mensual</span>'
        : '<i class="fa-solid fa-hand-holding-dollar text-emerald-400"></i><span>Nueva deuda mensual</span>';

    if (!deuda) {
        dmEl("dmDeudaId").value = "";
        dmEl("dmDescripcion").value = "";
        dmEl("dmTipo").value = dmState.filtros.tipo !== "todas" ? dmState.filtros.tipo : (dmState.tipos[0]?.id || "");
        dmEl("dmEntidad").value = dmState.entidadInicial ? String(dmState.entidadInicial) : "";
        dmEl("dmMoneda").value = dmState.filtros.moneda !== "todas"
            ? dmState.filtros.moneda
            : (dmState.monedas[0]?.id || "");
        dmEl("dmFechaInicio").value = dmHoyISO();
        dmEl("dmDiaAparicion").value = "1";
        dmEl("dmDiaLimite").value = "5";
        dmEl("dmMontoCuota").value = "";
        dmEl("dmMontoTotal").value = "";
        dmEl("dmCuotasTotales").value = "6";
        dmEl("dmCuentaDefault").value = "";
        dmSetModoFormulario("recurrente");

        const tipoId = dmEl("dmTipo").value;
        if (tipoId) await cargarSubtipos("dmSubtipo", tipoId, null);
        else dmEl("dmSubtipo").innerHTML = '<option value="">Sin subtipo</option>';
    } else {
        dmEl("dmDeudaId").value = deuda.id;
        dmEl("dmDescripcion").value = deuda.descripcion || "";
        dmEl("dmTipo").value = deuda.tipo_id;
        await cargarSubtipos("dmSubtipo", deuda.tipo_id, deuda.subtipo_id);
        dmEl("dmEntidad").value = deuda.entidad_id ? String(deuda.entidad_id) : "";
        dmEl("dmMoneda").value = String(deuda.moneda_id);
        dmEl("dmMoneda").disabled = true;
        dmEl("dmFechaInicio").value = dmFechaInput(deuda.fecha_inicio);
        dmEl("dmDiaAparicion").value = deuda.dia_aparicion;
        dmEl("dmDiaLimite").value = deuda.dia_limite;
        dmEl("dmMontoCuota").value = deuda.modalidad === "recurrente" ? deuda.monto_cuota : "";
        dmEl("dmMontoTotal").value = deuda.monto_total ?? "";
        dmEl("dmCuotasTotales").value = deuda.cuotas_totales ?? "";
        dmEl("dmCuentaDefault").value = deuda.cuenta_pago_default_id ? String(deuda.cuenta_pago_default_id) : "";
        dmSetModoFormulario(deuda.modalidad);

        const tienePagos = dmNum(deuda.pagado) > 0;
        dmHabilitarCamposEstructura(!tienePagos);
        if (deuda.modalidad === "cuotas") {
            dmEl("dmCampoMontoCuota").querySelector("input").disabled = true;
        }
    }

    dmAbrirModal("dmModalDeuda");
}

async function dmGuardarDeuda(event) {
    event.preventDefault();

    const id = dmEl("dmDeudaId").value ? Number(dmEl("dmDeudaId").value) : null;
    const modo = dmEl("dmModoForm").value;
    const descripcion = dmEl("dmDescripcion").value.trim();
    const tipoId = Number(dmEl("dmTipo").value);
    const subtipoId = dmEl("dmSubtipo").value ? Number(dmEl("dmSubtipo").value) : null;
    const entidadId = dmEl("dmEntidad").value ? Number(dmEl("dmEntidad").value) : null;
    const monedaId = Number(dmEl("dmMoneda").value);
    const fechaInicio = dmEl("dmFechaInicio").value;
    const diaAparicion = Number(dmEl("dmDiaAparicion").value);
    const diaLimite = Number(dmEl("dmDiaLimite").value);
    const cuentaDefault = dmEl("dmCuentaDefault").value ? Number(dmEl("dmCuentaDefault").value) : null;

    const error = mensaje => {
        const el = dmEl("dmErrorDeuda");
        el.textContent = mensaje;
        el.classList.remove("hidden");
        mostrarNotificacion(mensaje, "warning");
    };

    if (!descripcion) return error("Ingresá una descripción.");
    if (!tipoId) return error("Seleccioná una categoría.");
    if (!id && !monedaId) return error("Seleccioná una moneda.");
    if (!fechaInicio) return error("Indicá la fecha de inicio.");
    if (!(diaAparicion >= 1 && diaAparicion <= 31) || !(diaLimite >= 1 && diaLimite <= 31)) {
        return error("Los días deben estar entre 1 y 31.");
    }

    const payload = {
        descripcion,
        tipo_id: tipoId,
        dia_aparicion: diaAparicion,
        dia_limite: diaLimite,
        fecha_inicio: fechaParaAPI(fechaInicio),
    };

    if (entidadId) payload.entidad_id = entidadId;
    if (subtipoId) payload.subtipo_id = subtipoId;
    if (cuentaDefault) payload.cuenta_pago_default_id = cuentaDefault;

    if (!id) {
        payload.modalidad = modo;
        payload.moneda_id = monedaId;
    }

    if (modo === "cuotas") {
        const montoTotal = Number(dmEl("dmMontoTotal").value);
        const cuotasTotales = Number(dmEl("dmCuotasTotales").value);
        if (!(montoTotal > 0)) return error("El monto total del plan debe ser mayor que cero.");
        if (!(cuotasTotales >= 1)) return error("El plan debe tener al menos una cuota.");
        payload.monto_total = montoTotal;
        payload.cuotas_totales = cuotasTotales;
    } else {
        const montoCuota = Number(dmEl("dmMontoCuota").value);
        if (!(montoCuota > 0)) return error("El monto mensual debe ser mayor que cero.");
        payload.monto_cuota = montoCuota;
    }

    const boton = dmEl("dmBtnGuardarDeuda");
    dmBloquearBoton(boton, true, "Guardando...");

    try {
        if (id) {
            await putRequest(`deudas-mensuales/${id}`, payload);
            mostrarNotificacion("Deuda mensual actualizada.");
        } else {
            const creada = await post("deudas-mensuales/", payload);
            dmState.seleccionadaId = creada.id;
            mostrarNotificacion("Deuda mensual creada.");
        }
        dmCerrarModal("dmModalDeuda");
        dmState.entidadInicial = null;
        dmState.nuevaAlIniciar = false;
        dmNotificarCambio();
        await dmCargarTodo();
    } catch (err) {
        mostrarNotificacion(err.message || "No se pudo guardar la deuda mensual", "error");
    } finally {
        dmRestaurarBoton(boton);
    }
}

// ==================== MODAL PAGO ====================

async function dmAbrirModalPago(cuotaId, pagoId = null) {
    const cuota = (dmState.detalle?.cuotas || []).find(item => Number(item.id) === Number(cuotaId));
    if (!cuota) {
        mostrarNotificacion("No se encontró la cuota seleccionada.", "error");
        return;
    }

    const pago = pagoId
        ? (cuota.pagos || []).find(item => Number(item.id) === Number(pagoId))
        : null;

    dmState.cuotaObjetivo = cuota;
    dmState.pagoEditando = pago;

    dmEl("dmErrorPago").classList.add("hidden");
    dmEl("dmPagoCuotaId").value = cuota.id;
    dmEl("dmPagoPagoId").value = pago?.id || "";
    dmEl("dmModalPagoTitulo").textContent = pago ? "Editar pago" : "Pagar cuota";
    dmEl("dmModalPagoSub").textContent = pago ? "Modificar el pago registrado" : "Registrar salida de dinero";
    dmEl("dmPagoInfo").innerHTML = `<i class="fa-solid fa-circle-info text-slate-500 mr-1"></i>
        ${dmEsc(dmState.detalle.descripcion || "Deuda mensual")} · Cuota ${cuota.numero} (${dmPeriodo(cuota)})
        · Vence ${dmFechaLegible(cuota.fecha_limite)} · ${dmImporte(cuota.monto, dmState.detalle.moneda_id)}`;
    dmEl("dmPagoMonto").value = pago?.monto ?? cuota.monto;
    dmEl("dmPagoFecha").value = dmFechaInput(pago?.fecha) || dmHoyISO();
    dmEl("dmPagoDescripcion").value = pago?.descripcion || "";
    dmEl("dmBtnPagar").textContent = pago ? "Guardar cambios" : "Confirmar pago";

    const predeterminada = pago?.cuenta_id
        || dmState.detalle.cuenta_pago_default_id
        || dmState.cuentas[0]?.id
        || null;
    await cargarSelectorCuentas("dmPagoCuenta", predeterminada, dmState.cuentas);

    dmAbrirModal("dmModalPago");
}

async function dmGuardarPago(event) {
    event.preventDefault();

    const cuota = dmState.cuotaObjetivo;
    if (!cuota) return;

    const pagoId = dmEl("dmPagoPagoId").value ? Number(dmEl("dmPagoPagoId").value) : null;
    const monto = Number(dmEl("dmPagoMonto").value);
    const cuentaId = Number(dmEl("dmPagoCuenta").value);
    const fecha = dmEl("dmPagoFecha").value;
    const descripcion = dmEl("dmPagoDescripcion").value.trim();

    const error = mensaje => {
        const el = dmEl("dmErrorPago");
        el.textContent = mensaje;
        el.classList.remove("hidden");
        mostrarNotificacion(mensaje, "warning");
    };

    if (!(monto > 0)) return error("El monto debe ser mayor que cero.");
    if (Math.abs(monto - dmNum(cuota.monto)) > 1e-6) {
        return error(`El pago debe coincidir con el monto de la cuota (${dmImporte(cuota.monto, dmState.detalle.moneda_id)}).`);
    }
    if (!cuentaId) return error("Seleccioná una cuenta.");

    const payload = {
        monto,
        cuenta_id: cuentaId,
        fecha: fechaParaAPI(fecha),
        descripcion: descripcion || null,
    };

    const boton = dmEl("dmBtnPagar");
    dmBloquearBoton(boton, true, "Guardando...");

    try {
        if (pagoId) {
            await putRequest(`deudas-mensuales/cuotas/${cuota.id}/pagos/${pagoId}`, payload);
            mostrarNotificacion("Pago actualizado.");
        } else {
            await post(`deudas-mensuales/cuotas/${cuota.id}/pagar`, payload);
            mostrarNotificacion("Cuota pagada.");
        }
        dmCerrarModal("dmModalPago");
        dmNotificarCambio();
        await dmCargarTodo();
    } catch (err) {
        mostrarNotificacion(err.message || "No se pudo registrar el pago", "error");
    } finally {
        dmRestaurarBoton(boton);
        dmEl("dmBtnPagar").textContent = pagoId ? "Guardar cambios" : "Confirmar pago";
    }
}

// ==================== PAGO EN BLOQUE ====================

function dmActualizarTotalLote() {
    const checks = [...dmEl("dmListaLote").querySelectorAll("input[type=checkbox]:checked")];
    const items = dmState.loteItems.filter(item => checks.some(check => Number(check.dataset.cuotaId) === Number(item.cuota_id)));
    const total = items.reduce((suma, item) => suma + dmNum(item.monto), 0);
    const monedas = new Set(items.map(item => Number(item.moneda_id)));
    const monedaId = monedas.size === 1 ? [...monedas][0] : null;
    dmEl("dmLoteTotal").textContent = monedaId
        ? dmImporte(total, monedaId)
        : `Σ ${dmFormatearNumero(total)}`;
    dmEl("dmBtnPagarLote").disabled = items.length === 0;
    dmEl("dmBtnPagarLote").classList.toggle("opacity-50", items.length === 0);
}

async function dmAbrirModalLote(deudaId = null) {
    dmState.loteDeudaId = deudaId ? Number(deudaId) : null;
    dmEl("dmModalLoteTitulo").textContent = dmState.loteDeudaId ? "Pagar atrasadas de esta deuda" : "Pagar cuotas atrasadas";
    dmEl("dmListaLote").innerHTML = '<p class="text-xs text-slate-500 py-3">Cargando cuotas vencidas...</p>';
    dmEl("dmLoteVacio").classList.add("hidden");
    dmEl("dmLoteFecha").value = dmHoyISO();
    dmEl("dmLoteDescripcion").value = "";
    dmEl("dmLoteCuenta").value = dmState.cuentas[0]?.id ? String(dmState.cuentas[0].id) : "";
    dmState.loteItems = [];
    dmEl("dmLoteTotal").textContent = "—";
    dmAbrirModal("dmModalLote");

    try {
        const moneda = dmState.filtros.moneda !== "todas" ? `&moneda_id=${encodeURIComponent(dmState.filtros.moneda)}` : "";
        const items = await get(`deudas-mensuales/proximas?dias=0${moneda}`);
        dmState.loteItems = (Array.isArray(items) ? items : []).filter(item =>
            item.vencida
            && (!dmState.loteDeudaId || Number(item.deuda_mensual_id) === dmState.loteDeudaId)
        );

        if (dmState.loteItems.length === 0) {
            dmEl("dmListaLote").innerHTML = "";
            dmEl("dmLoteVacio").classList.remove("hidden");
            dmEl("dmBtnPagarLote").disabled = true;
            return;
        }

        dmEl("dmLoteVacio").classList.add("hidden");
        dmEl("dmListaLote").innerHTML = dmState.loteItems.map(item => `
            <label class="flex items-center justify-between gap-3 p-3 rounded-xl bg-slate-950 border border-slate-800 hover:border-slate-700 cursor-pointer">
                <div class="flex items-center gap-3 min-w-0">
                    <input type="checkbox" checked data-cuota-id="${item.cuota_id}"
                        class="w-4 h-4 rounded text-emerald-500 bg-slate-900 border-slate-700 focus:ring-0 cursor-pointer" />
                    <div class="min-w-0">
                        <p class="text-sm font-semibold text-white truncate">${dmEsc(item.descripcion || "Deuda mensual")}</p>
                        <p class="text-[11px] text-rose-400">Cuota ${item.numero} · ${dmPeriodo(item)} · ${dmDiasTexto(item.fecha_limite)}</p>
                    </div>
                </div>
                <span class="text-sm font-bold text-white flex-shrink-0">${dmImporte(item.monto, item.moneda_id)}</span>
            </label>`).join("");

        dmActualizarTotalLote();
    } catch (error) {
        dmEl("dmListaLote").innerHTML = "";
        dmEl("dmLoteVacio").classList.remove("hidden");
        mostrarNotificacion(error.message || "No se pudieron cargar las cuotas vencidas", "error");
    }
}

async function dmPagarLote() {
    const checks = [...dmEl("dmListaLote").querySelectorAll("input[type=checkbox]:checked")];
    const cuotaIds = checks.map(check => Number(check.dataset.cuotaId));
    const cuentaId = Number(dmEl("dmLoteCuenta").value);
    const fecha = dmEl("dmLoteFecha").value;
    const descripcion = dmEl("dmLoteDescripcion").value.trim();

    if (cuotaIds.length === 0) {
        mostrarNotificacion("Seleccioná al menos una cuota vencida.", "warning");
        return;
    }
    if (!cuentaId) {
        mostrarNotificacion("Seleccioná la cuenta de pago.", "warning");
        return;
    }

    const boton = dmEl("dmBtnPagarLote");
    dmBloquearBoton(boton, true, "Pagando...");

    try {
        await post("deudas-mensuales/pagar-lote", {
            cuota_ids: cuotaIds,
            cuenta_id: cuentaId,
            fecha: fechaParaAPI(fecha),
            descripcion: descripcion || null,
        });
        mostrarNotificacion(`${cuotaIds.length} ${cuotaIds.length === 1 ? "cuota pagada" : "cuotas pagadas"}.`);
        dmCerrarModal("dmModalLote");
        dmNotificarCambio();
        await dmCargarTodo();
    } catch (error) {
        mostrarNotificacion(error.message || "No se pudieron pagar las cuotas", "error");
    } finally {
        dmRestaurarBoton(boton);
    }
}

// ==================== CONFIRMACIONES ====================

function dmAbrirConfirmarCancelar() {
    const deuda = dmState.detalle;
    if (!deuda) return;
    dmState.deudaParaCancelar = deuda.id;
    dmEl("dmCancelarInfo").textContent = `${deuda.descripcion || "Deuda mensual"} · ${dmImporte(deuda.pendiente, deuda.moneda_id)} pendiente`;
    dmAbrirModal("dmModalCancelar");
}

async function dmConfirmarCancelar() {
    const id = dmState.deudaParaCancelar;
    if (!id) return;
    const boton = dmEl("dmBtnConfirmarCancelar");
    dmBloquearBoton(boton, true, "Cancelando...");
    try {
        await post(`deudas-mensuales/${id}/cancelar`);
        mostrarNotificacion("Deuda mensual cancelada.");
        dmCerrarModal("dmModalCancelar");
        dmState.deudaParaCancelar = null;
        dmNotificarCambio();
        await dmCargarTodo();
    } catch (error) {
        mostrarNotificacion(error.message || "No se pudo cancelar la deuda", "error");
    } finally {
        dmRestaurarBoton(boton);
    }
}

function dmAbrirConfirmarEliminar() {
    const deuda = dmState.detalle;
    if (!deuda) return;
    dmState.deudaParaEliminar = deuda.id;
    dmEl("dmEliminarInfo").textContent = `${deuda.descripcion || "Deuda mensual"} · ${dmImporte(deuda.pendiente, deuda.moneda_id)} pendiente`;
    dmAbrirModal("dmModalEliminar");
}

async function dmConfirmarEliminar() {
    const id = dmState.deudaParaEliminar;
    if (!id) return;
    const boton = dmEl("dmBtnConfirmarEliminar");
    dmBloquearBoton(boton, true, "Eliminando...");

    try {
        await deleteRequest(`deudas-mensuales/${id}`);
        mostrarNotificacion("Deuda mensual eliminada.");
        dmCerrarModal("dmModalEliminar");
        dmState.deudaParaEliminar = null;
        dmState.seleccionadaId = null;
        dmState.detalle = null;
        const url = new URL(window.location.href);
        url.searchParams.delete("deuda");
        window.history.replaceState(null, "", url.toString());
        dmNotificarCambio();
        await dmCargarTodo();
    } catch (error) {
        mostrarNotificacion(error.message || "No se pudo eliminar la deuda", "error");
    } finally {
        dmRestaurarBoton(boton);
    }
}

function dmAbrirConfirmarEliminarPago(cuotaId, pagoId) {
    const cuota = (dmState.detalle?.cuotas || []).find(item => Number(item.id) === Number(cuotaId));
    const pago = cuota?.pagos?.find(item => Number(item.id) === Number(pagoId));
    if (!cuota || !pago) return;
    dmState.pagoParaEliminar = { cuotaId, pagoId };
    dmEl("dmEliminarPagoInfo").textContent = `${dmFechaLegible(pago.fecha)} · ${dmImporte(pago.monto, dmState.detalle.moneda_id)} · Cuota ${cuota.numero}`;
    dmAbrirModal("dmModalEliminarPago");
}

async function dmConfirmarEliminarPago() {
    const objetivo = dmState.pagoParaEliminar;
    if (!objetivo) return;
    const boton = dmEl("dmBtnConfirmarEliminarPago");
    dmBloquearBoton(boton, true, "Eliminando...");
    try {
        await deleteRequest(`deudas-mensuales/cuotas/${objetivo.cuotaId}/pagos/${objetivo.pagoId}`);
        mostrarNotificacion("Pago eliminado.");
        dmCerrarModal("dmModalEliminarPago");
        dmState.pagoParaEliminar = null;
        dmNotificarCambio();
        await dmCargarTodo();
    } catch (error) {
        mostrarNotificacion(error.message || "No se pudo eliminar el pago", "error");
    } finally {
        dmRestaurarBoton(boton);
    }
}

// ==================== EVENTOS ====================

function dmEnlazarEventos() {
    dmEl("dmBtnNuevaDeuda")?.addEventListener("click", () => dmAbrirModalDeuda());
    dmEl("dmBtnPagarAtrasadas")?.addEventListener("click", dmAbrirModalLote);
    dmEl("dmBtnPagarLote")?.addEventListener("click", dmPagarLote);

    dmEl("dmTabRecurrente")?.addEventListener("click", () => dmSetModoFormulario("recurrente"));
    dmEl("dmTabPlan")?.addEventListener("click", () => dmSetModoFormulario("cuotas"));
    dmEl("dmFormDeuda")?.addEventListener("submit", dmGuardarDeuda);
    dmEl("dmFormPago")?.addEventListener("submit", dmGuardarPago);

    dmEl("dmTipo")?.addEventListener("change", async event => {
        await cargarSubtipos("dmSubtipo", event.target.value, null);
    });

    dmEl("dmBtnConfirmarCancelar")?.addEventListener("click", dmConfirmarCancelar);
    dmEl("dmBtnConfirmarEliminar")?.addEventListener("click", dmConfirmarEliminar);
    dmEl("dmBtnConfirmarEliminarPago")?.addEventListener("click", dmConfirmarEliminarPago);

    dmEl("dmBtnCanceladas")?.addEventListener("click", () => {
        dmState.canceladasAbierto = !dmState.canceladasAbierto;
        dmRenderLista();
    });

    dmEl("dmFiltroMoneda")?.addEventListener("change", event => {
        dmState.filtros.moneda = event.target.value;
        dmCargarTodo();
    });
    dmEl("dmFiltroTipo")?.addEventListener("change", event => {
        dmState.filtros.tipo = event.target.value;
        dmCargarTodo();
    });
    dmEl("dmFiltroEstado")?.addEventListener("change", event => {
        dmState.filtros.estado = event.target.value;
        if (event.target.value === "canceladas") dmState.canceladasAbierto = true;
        dmRenderLista();
    });
    dmEl("dmFiltroModalidad")?.addEventListener("change", event => {
        dmState.filtros.modalidad = event.target.value;
        dmCargarTodo();
    });
    dmEl("dmBusqueda")?.addEventListener("input", event => {
        dmState.filtros.busqueda = event.target.value;
        clearTimeout(dmState.busquedaTimer);
        dmState.busquedaTimer = setTimeout(dmRenderLista, 150);
    });
    dmEl("dmBtnLimpiarFiltros")?.addEventListener("click", dmLimpiarFiltros);
    dmEl("dmBtnLimpiarVacio")?.addEventListener("click", dmLimpiarFiltros);

    dmEl("dmListaLote")?.addEventListener("change", dmActualizarTotalLote);

    document.querySelectorAll('[data-dm-cerrar]').forEach(boton => {
        boton.addEventListener("click", () => dmCerrarModal(boton.dataset.dmCerrar));
    });

    document.querySelectorAll('[role="dialog"]').forEach(modal => {
        modal.addEventListener("click", event => {
            if (event.target === modal) dmCerrarModal(modal.id);
        });
    });

    window.addEventListener("keydown", event => {
        if (event.key === "Escape") {
            document.querySelectorAll('[role="dialog"]').forEach(modal => modal.classList.add("hidden"));
        }
    });

    dmEl("dmListaVencidas")?.addEventListener("click", dmManejarClickLista);
    dmEl("dmListaActivas")?.addEventListener("click", dmManejarClickLista);
    dmEl("dmListaCanceladas")?.addEventListener("click", dmManejarClickLista);

    dmEl("dmDetalleContenido")?.addEventListener("click", event => {
        const accion = event.target.closest("[data-dm-accion]");
        if (!accion) return;

        const tipo = accion.dataset.dmAccion;
        const cuotaId = accion.dataset.cuotaId ? Number(accion.dataset.cuotaId) : null;
        const pagoId = accion.dataset.pagoId ? Number(accion.dataset.pagoId) : null;

        if (tipo === "pagar-proxima") {
            const proxima = dmState.detalle?.proxima;
            if (proxima) dmAbrirModalPago(proxima.id);
        }
        if (tipo === "pagar-cuota" && cuotaId) dmAbrirModalPago(cuotaId);
        if (tipo === "pagar-atrasadas") dmAbrirModalLote(dmState.detalle?.id);
        if (tipo === "editar") dmAbrirModalDeuda(dmState.detalle?.id);
        if (tipo === "cancelar") dmAbrirConfirmarCancelar();
        if (tipo === "eliminar") dmAbrirConfirmarEliminar();
        if (tipo === "editar-pago" && cuotaId && pagoId) dmAbrirModalPago(cuotaId, pagoId);
        if (tipo === "eliminar-pago" && cuotaId && pagoId) dmAbrirConfirmarEliminarPago(cuotaId, pagoId);
    });
}

function dmManejarClickLista(event) {
    const tarjeta = event.target.closest("[data-dm-id]");
    if (tarjeta) dmSeleccionarDeuda(Number(tarjeta.dataset.dmId));
}

// ==================== INICIALIZACIÓN ====================

async function dmInit() {
    dmEnlazarEventos();

    try {
        await dmCargarCatalogos();

        const params = new URLSearchParams(window.location.search);
        const deudaId = params.get("deuda");
        const entidadId = params.get("entidad");
        dmState.seleccionadaId = deudaId ? Number(deudaId) : null;
        dmState.entidadInicial = entidadId ? Number(entidadId) : null;
        dmState.nuevaAlIniciar = params.get("nueva") === "1";

        await dmCargarTodo();

        if (dmState.nuevaAlIniciar) {
            await dmAbrirModalDeuda();
            const url = new URL(window.location.href);
            url.searchParams.delete("nueva");
            url.searchParams.delete("entidad");
            window.history.replaceState(null, "", url.toString());
        }
    } catch (error) {
        console.error("Error inicializando deudas mensuales:", error);
        mostrarNotificacion(error.message || "No se pudieron cargar las deudas mensuales", "error");
        dmEl("dmListaVacia").classList.remove("hidden");
    }
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", dmInit);
} else {
    dmInit();
}
