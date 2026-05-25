document.addEventListener('DOMContentLoaded', async function () {
    const data = verificarSesionLocal();

    if  (data) {
        console.log("Sesión activa, redirigiendo...");
        verificarTokenLife()
        //return window.location.href = 'pages/panelControl.html';
    } else {
        console.log("No hay sesión activa, permaneciendo en la página de inicio de sesión.");
        if(await verificarSesionApi()){
            console.log("Sesión activa en API, redirigiendo...");
            //return window.location.href = 'pages/panelControl.html';
        } else {
            console.log("No hay sesión activa en API, permaneciendo en la página de inicio de sesión.");
        }
    }
    
    //return window.location.href = 'pages/login.html';

});

function verificarTokenLife() {
    const token = sessionStorage.getItem("token")
    console.log("Verificando token:", token);
        if (token === null) {
            console.log("Token no encontrado.");
            cerrarSesion()
            return false;
        }
        const response = await get(`auth/life/token?token=${token}`)
        if (!response.ok) {
            cerrarSesion()
            return false;
        }
        return true;
}

async function verificarSesionApi() {
    const sesion =await get("auth/")
    console.log(sesion);
    if (sesion && sesion.token) {
        console.log("Sesión verificada.");
        guardarSesion(sesion.token);
        return true;
    }
    else{  
        return false;
    }
}
function verificarSesionLocal() {
    const data = localStorage.getItem("remember_session");
    if (data && data === "true" ) {
        console.log("Sesión verificada.");
            return true;
    } else {
        console.log("No hay sesión activa.");
        return false;
    }
}
function guardarSesion(token) {
    sessionStorage.setItem("token", token);
    localStorage.setItem("remember_session","true")
    console.log("Sesión guardada.");
}

function cerrarSesion() {
    sessionStorage.removeItem("token");
    localStorage.removeItem("remember_session");
    console.log("Sesión cerrada.");
}

function lista(lista = []) {
    var newLista = []
    for (let i = 0; i < lista.length; i++) {
        newLista.push(lista[i] * 2)
    }
    return newLista;
}

