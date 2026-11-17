async function loadComponents() {

    const elements = document.querySelectorAll("[data-component]")

    for (const el of elements) {

        const file = el.getAttribute("data-component")

        const resp = await fetch(file)
        const html = await resp.text()

        el.innerHTML = html
    }

    marcarMenuActivo()
    cargarNombreUsuario()
    cargarBadgeDeudasMensuales()
}

/**
 * Marca con un brillo de selección el ítem del menú lateral
 * que corresponde a la página actual.
 */
function marcarMenuActivo() {
    const paginaActual = (window.location.pathname.split('/').pop() || 'index.html').toLowerCase()

    document.querySelectorAll('.sidebar-link').forEach(link => {
        const href = (link.getAttribute('href') || '').split('/').pop().split('?')[0].toLowerCase()
        if (href === paginaActual) {
            link.classList.add('sidebar-active')
        }
    })
}

/**
 * Muestra en el menú lateral la cantidad de cuotas mensuales vencidas.
 */
async function cargarBadgeDeudasMensuales() {
    const badge = document.getElementById('badgeDeudasMensuales');
    if (!badge || typeof get !== 'function' || typeof obtenerToken !== 'function' || !obtenerToken()) return;

    try {
        const resumen = await get('deudas-mensuales/resumen');
        const cantidad = Number(resumen?.vencidas?.cantidad) || 0;
        badge.textContent = String(cantidad);
        badge.classList.toggle('hidden', cantidad === 0);
        badge.title = cantidad === 1 ? '1 cuota vencida' : `${cantidad} cuotas vencidas`;
    } catch (error) {
        badge.classList.add('hidden');
        console.warn('No se pudo cargar el badge de deudas mensuales:', error.message);
    }
}

window.addEventListener('deudas-mensuales-actualizadas', cargarBadgeDeudasMensuales);

async function cargarNombreUsuario() {
    const nombreEl = document.getElementById('userName');
    if (!nombreEl || typeof get !== 'function') return;

    try {
        const sesion = await get('auth');
        if (sesion?.user?.name) {
            nombreEl.textContent = sesion.user.name;
        }
    } catch (error) {
        console.warn('No se pudo cargar el nombre de usuario:', error.message);
    }
}

loadComponents()
