// ==================== NOTIFICACIONES TOAST ====================

const COLORES_NOTIFICACION = {
    success: { bg: 'bg-emerald-500', icono: '✓' },
    error: { bg: 'bg-rose-500', icono: '✗' },
    warning: { bg: 'bg-amber-500', icono: '⚠' },
};

/**
 * Muestra una notificación flotante que se desvanece a los 3 segundos.
 * @param {string} mensaje - Texto a mostrar.
 * @param {'success'|'error'|'warning'} tipo - Color de la notificación.
 */
function mostrarNotificacion(mensaje, tipo = 'success') {
    const config = COLORES_NOTIFICACION[tipo] || COLORES_NOTIFICACION.success;

    let contenedor = document.getElementById('contenedor-notificaciones');
    if (!contenedor) {
        contenedor = document.createElement('div');
        contenedor.id = 'contenedor-notificaciones';
        contenedor.className = 'fixed top-4 right-4 z-50 space-y-3';
        document.body.appendChild(contenedor);
    }

    const toast = document.createElement('div');
    toast.className = `flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg text-white ${config.bg} opacity-0 translate-x-2 transition-all duration-300`;

    const icono = document.createElement('span');
    icono.className = 'font-bold';
    icono.textContent = config.icono;

    const texto = document.createElement('span');
    texto.className = 'text-sm font-medium';
    texto.textContent = mensaje;

    toast.appendChild(icono);
    toast.appendChild(texto);
    contenedor.appendChild(toast);

    requestAnimationFrame(() => {
        toast.classList.remove('opacity-0', 'translate-x-2');
    });

    setTimeout(() => {
        toast.classList.add('opacity-0', 'translate-x-2');
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}
