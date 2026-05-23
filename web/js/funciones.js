// ...existing code...

let baseUrl = 'http://127.0.0.1:8000/'; // Variable que almacena la base de la URL

/**
 * Función para hacer una petición GET a una ruta específica con datos opcionales.
 * @param {string} path - La ruta a la cual se realizará la petición.
 * @param {Object} data - Los datos que se enviarán en la petición (opcional).
 * @returns {Promise<Response>} - Una promesa que resuelve con la respuesta de la petición.
 */
async function get(path, data = {}) {
    const url = `${baseUrl}${path}`;
    const response = await fetch(url, {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json'
        },
    });
    return await response.json();
}

/**
 * Función para hacer una petición POST a una ruta específica con datos opcionales.
 * @param {string} path - La ruta a la cual se realizará la petición.
 * @param {Object} data - Los datos que se enviarán en la petición (opcional).
 * @returns {Promise<Response>} - Una promesa que resuelve con la respuesta de la petición.
 */
async function post(path, data = {}) {
    const url = `${baseUrl}${path}`;
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    return await response.json();
}

// Event listeners para botones (si existen en el HTML)
const btnGet = document.getElementById('btnGet');
if (btnGet) {
    btnGet.addEventListener('click', async () => {
        const response = await get('auth/life');
        console.log(response);
    });
}

const btnPost = document.getElementById('btnPost');
if (btnPost) {
    btnPost.addEventListener('click', async () => {
        const data = { clave: 'valor' };
        const response = await post('/ruta/especifica', data);
        console.log(response);
    });
}