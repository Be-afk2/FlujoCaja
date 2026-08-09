
// ==================== CATEGORÍAS ====================

let editandoCategoriaId = null;
let subtipoModal = { tipo_id: null, subtipoId: null };
let accionConfirmar = null;

const subtiposCache = {};

const PALETA_CATEGORIAS = [
    { icono: 'restaurant', color: 'orange' },
    { icono: 'directions_car', color: 'blue' },
    { icono: 'home', color: 'purple' },
    { icono: 'shopping_bag', color: 'emerald' },
    { icono: 'theater_comedy', color: 'pink' },
    { icono: 'fitness_center', color: 'red' },
    { icono: 'medical_services', color: 'cyan' },
    { icono: 'school', color: 'indigo' },
    { icono: 'bolt', color: 'amber' },
    { icono: 'local_mall', color: 'teal' },
];

function estiloCategoria(idx) {
    const e = PALETA_CATEGORIAS[idx % PALETA_CATEGORIAS.length];
    return {
        icono: e.icono,
        chip: `bg-${e.color}-500/20 text-${e.color}-400`,
        dot: `bg-${e.color}-400`,
    };
}

// ==================== CARGAR Y RENDERIZAR ====================

async function cargarCategorias() {
    const contenedor = document.getElementById('categorias-container');
    if (!contenedor) return;

    contenedor.innerHTML = '<div class="flex justify-center p-10 text-slate-500">Cargando categorías...</div>';

    try {
        const tipos = await get('tipos/?cantidad=50');

        if (!tipos || tipos.length === 0) {
            contenedor.innerHTML = '<div class="p-10 text-center text-slate-500 border-2 border-dashed border-slate-800 rounded-2xl">Aún no hay categorías. Crea la primera.</div>';
            return;
        }

        const subtiposPorTipo = await Promise.all(
            tipos.map(t => get(`subtipos/?tipo_id=${t.id}`).catch(() => ({ subtipos: [] })))
        );

        Object.keys(subtiposCache).forEach(k => delete subtiposCache[k]);
        subtiposPorTipo.forEach((detalle, idx) => {
            const tipoId = tipos[idx].id;
            ((detalle || {}).subtipos || []).forEach(s => {
                subtiposCache[s.id] = { id: s.id, nombre: s.nombre, tipo_id: tipoId };
            });
        });

        renderCategorias(tipos, subtiposPorTipo);
    } catch (error) {
        console.error('Error cargando categorías:', error);
        contenedor.innerHTML = '<div class="p-10 text-center text-slate-500 border-2 border-dashed border-slate-800 rounded-2xl">Error al cargar las categorías.</div>';
    }
}

function renderCategorias(tipos, subtiposPorTipo) {
    const contenedor = document.getElementById('categorias-container');
    if (!contenedor) return;

    contenedor.innerHTML = tipos.map((tipo, idx) => {
        const estilo = estiloCategoria(idx);
        const subtipos = (subtiposPorTipo[idx] || {}).subtipos || [];

        const subtiposHtml = subtipos.length === 0
            ? '<p class="p-3 text-sm text-slate-500">Sin subcategorías.</p>'
            : subtipos.map(s => `
                <div class="flex items-center justify-between p-3 hover:bg-slate-800 rounded-lg group transition-colors">
                    <div class="flex items-center gap-3">
                        <div class="w-1.5 h-1.5 rounded-full ${estilo.dot}"></div>
                        <span class="text-slate-300 font-medium">${s.nombre}</span>
                    </div>
                    <div class="flex gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button type="button" data-accion="editar-subtipo" data-tipo="${tipo.id}" data-id="${s.id}"
                            class="text-xs text-slate-500 hover:text-primary transition-colors">Editar</button>
                        <button type="button" data-accion="eliminar-subtipo" data-tipo="${tipo.id}" data-id="${s.id}"
                            class="text-xs text-slate-500 hover:text-rose-400 transition-colors">Eliminar</button>
                    </div>
                </div>`).join('');

        return `
        <div class="bg-card-dark rounded-2xl border border-border-dark shadow-sm overflow-hidden">
            <div class="p-5 border-b border-border-dark flex justify-between items-center bg-slate-800/50">
                <div class="flex items-center gap-4">
                    <div class="size-12 rounded-xl ${estilo.chip} flex items-center justify-center">
                        <span class="material-symbols-outlined text-2xl" style="font-variation-settings: 'FILL' 1;">${estilo.icono}</span>
                    </div>
                    <div>
                        <h3 class="font-bold text-lg text-white">${tipo.nombre}</h3>
                        <p class="text-xs text-slate-400">${tipo.descripcion || 'Sin descripción'}</p>
                    </div>
                </div>
                <div class="flex gap-2">
                    <button type="button" data-accion="editar-tipo" data-id="${tipo.id}"
                        class="p-2 text-slate-500 hover:text-primary transition-colors" title="Editar categoría">
                        <span class="material-symbols-outlined">edit</span>
                    </button>
                    <button type="button" data-accion="eliminar-tipo" data-id="${tipo.id}"
                        class="p-2 text-slate-500 hover:text-rose-400 transition-colors" title="Eliminar categoría">
                        <span class="material-symbols-outlined">delete</span>
                    </button>
                </div>
            </div>
            <div class="p-2">
                ${subtiposHtml}
                <button type="button" data-accion="agregar-subtipo" data-id="${tipo.id}"
                    class="w-full flex items-center justify-center gap-2 p-3 text-sm text-slate-500 hover:text-primary transition-colors rounded-lg mt-1">
                    <span class="material-symbols-outlined text-lg">add_box</span>
                    Agregar subcategoría
                </button>
            </div>
        </div>`;
    }).join('');
}

// ==================== CREAR / EDITAR CATEGORÍA (formulario lateral) ====================

async function guardarCategoria() {
    const nombre = document.getElementById('inputNombreCategoria').value.trim();
    const descripcion = document.getElementById('inputDescripcionCategoria').value.trim();

    if (!nombre) {
        mostrarNotificacion('Ingresa el nombre de la categoría', 'warning');
        return;
    }

    const btn = document.getElementById('btnCrearCategoria');
    const esEdicion = editandoCategoriaId !== null;
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Guardando...';
    }

    try {
        if (esEdicion) {
            await putRequest(`tipos/${editandoCategoriaId}`, { nombre, descripcion });
            mostrarNotificacion('Categoría actualizada');
        } else {
            await post('tipos/', { nombre, descripcion });
            mostrarNotificacion('Categoría creada');
        }
        resetFormCategoria();
        await cargarCategorias();
    } catch (error) {
        console.error('Error guardando categoría:', error);
        mostrarNotificacion(error.message || 'Error al guardar la categoría', 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = esEdicion ? 'Guardar Cambios' : 'Crear Categoría';
        }
    }
}

async function editarCategoria(tipoId) {
    try {
        const tipos = await get('tipos/?cantidad=50');
        const tipo = (tipos || []).find(t => Number(t.id) === Number(tipoId));
        if (!tipo) return;

        editandoCategoriaId = tipo.id;
        document.getElementById('inputNombreCategoria').value = tipo.nombre;
        document.getElementById('inputDescripcionCategoria').value = tipo.descripcion || '';
        document.getElementById('tituloFormCategoria').textContent = 'Editar Categoría';
        document.getElementById('btnCrearCategoria').textContent = 'Guardar Cambios';
        document.getElementById('formCategoria')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        document.getElementById('inputNombreCategoria')?.focus();
    } catch (error) {
        console.error('Error cargando categoría a editar:', error);
        mostrarNotificacion('No se pudo cargar la categoría', 'error');
    }
}

function resetFormCategoria() {
    editandoCategoriaId = null;
    const form = document.getElementById('formCategoria');
    if (form) form.reset();
    const titulo = document.getElementById('tituloFormCategoria');
    if (titulo) titulo.textContent = 'Nueva Categoría';
    const btn = document.getElementById('btnCrearCategoria');
    if (btn) btn.textContent = 'Crear Categoría';
}

// ==================== MODAL SUBTIPOS (crear / editar) ====================

function abrirModalSubtipo(tipoId, subtipo) {
    const esEdicion = !!subtipo;
    subtipoModal = { tipo_id: Number(tipoId), subtipoId: esEdicion ? Number(subtipo.id) : null };
    document.getElementById('tituloModalSubtipo').textContent = esEdicion ? 'Editar Subcategoría' : 'Nueva Subcategoría';
    document.getElementById('inputNombreSubtipo').value = esEdicion ? subtipo.nombre : '';
    document.getElementById('btnGuardarSubtipo').textContent = esEdicion ? 'Guardar Cambios' : 'Guardar';
    document.getElementById('modalSubtipo').classList.remove('hidden');
    document.getElementById('inputNombreSubtipo')?.focus();
}

function cerrarModalSubtipo() {
    document.getElementById('modalSubtipo').classList.add('hidden');
    subtipoModal = { tipo_id: null, subtipoId: null };
}

async function guardarSubtipo() {
    const nombre = document.getElementById('inputNombreSubtipo').value.trim();
    if (!nombre) {
        mostrarNotificacion('Ingresa el nombre de la subcategoría', 'warning');
        return;
    }
    if (!subtipoModal.tipo_id) return;

    const btn = document.getElementById('btnGuardarSubtipo');
    const esEdicion = subtipoModal.subtipoId !== null;
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Guardando...';
    }

    try {
        if (esEdicion) {
            await putRequest(`subtipos/${subtipoModal.subtipoId}`, { nombre });
            mostrarNotificacion('Subcategoría actualizada');
        } else {
            await post('subtipos/', { nombre, tipo: subtipoModal.tipo_id });
            mostrarNotificacion('Subcategoría creada');
        }
        cerrarModalSubtipo();
        await cargarCategorias();
    } catch (error) {
        console.error('Error guardando subcategoría:', error);
        mostrarNotificacion(error.message || 'Error al guardar la subcategoría', 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = esEdicion ? 'Guardar Cambios' : 'Guardar';
        }
    }
}

// ==================== ELIMINAR (confirmación) ====================

function abrirConfirmacion(mensaje, accion) {
    document.getElementById('textoConfirmar').textContent = mensaje;
    accionConfirmar = accion;
    document.getElementById('modalConfirmar').classList.remove('hidden');
}

function cerrarConfirmacion() {
    document.getElementById('modalConfirmar').classList.add('hidden');
    accionConfirmar = null;
}

function confirmarEliminarTipo(tipoId) {
    abrirConfirmacion(
        '¿Seguro que deseas eliminar esta categoría? No se puede eliminar si tiene movimientos asociados.',
        () => deleteRequest(`tipos/${tipoId}`)
    );
}

function confirmarEliminarSubtipo(subtipoId) {
    abrirConfirmacion(
        '¿Seguro que deseas eliminar esta subcategoría? No se puede eliminar si tiene movimientos asociados.',
        () => deleteRequest(`subtipos/${subtipoId}`)
    );
}

async function ejecutarAccionConfirmada() {
    if (!accionConfirmar) return;
    const accion = accionConfirmar;
    accionConfirmar = null;

    const btn = document.getElementById('btnConfirmarAccion');
    if (btn) {
        btn.disabled = true;
        btn.textContent = 'Eliminando...';
    }

    try {
        await accion();
        cerrarConfirmacion();
        mostrarNotificacion('Eliminado correctamente');
        await cargarCategorias();
    } catch (error) {
        console.error('Error al eliminar:', error);
        cerrarConfirmacion();
        mostrarNotificacion(error.message || 'Error al eliminar', 'error');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = 'Eliminar';
        }
    }
}

// ==================== ACCIONES DE LAS TARJETAS (delegación) ====================

function configurarAcciones() {
    const contenedor = document.getElementById('categorias-container');
    if (!contenedor) return;

    contenedor.addEventListener('click', (e) => {
        const btn = e.target.closest('[data-accion]');
        if (!btn) return;

        const accion = btn.getAttribute('data-accion');
        const id = Number(btn.getAttribute('data-id'));
        const tipoId = btn.getAttribute('data-tipo');

        if (accion === 'editar-tipo') editarCategoria(id);
        else if (accion === 'eliminar-tipo') confirmarEliminarTipo(id);
        else if (accion === 'agregar-subtipo') abrirModalSubtipo(id, null);
        else if (accion === 'editar-subtipo') {
            const sub = subtiposCache[id] || { id, nombre: '' };
            abrirModalSubtipo(tipoId, sub);
        }
        else if (accion === 'eliminar-subtipo') confirmarEliminarSubtipo(id);
    });
}

// ==================== INICIALIZACIÓN ====================

function initCategorias() {
    document.getElementById('btn-nueva-categoria')?.addEventListener('click', () => {
        resetFormCategoria();
        document.getElementById('formCategoria')?.scrollIntoView({ behavior: 'smooth', block: 'center' });
        document.getElementById('inputNombreCategoria')?.focus();
    });

    document.getElementById('formCategoria')?.addEventListener('submit', (e) => {
        e.preventDefault();
        guardarCategoria();
    });
    document.getElementById('btnCancelarCategoria')?.addEventListener('click', resetFormCategoria);

    document.getElementById('btnGuardarSubtipo')?.addEventListener('click', guardarSubtipo);
    document.querySelectorAll('[data-cerrar-subtipo]').forEach(btn => btn.addEventListener('click', cerrarModalSubtipo));

    document.getElementById('btnCancelarConfirmar')?.addEventListener('click', cerrarConfirmacion);
    document.getElementById('btnConfirmarAccion')?.addEventListener('click', ejecutarAccionConfirmada);

    configurarAcciones();
    cargarCategorias();
}

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initCategorias);
} else {
    initCategorias();
}
