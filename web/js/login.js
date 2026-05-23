document.addEventListener('DOMContentLoaded', async function () {
    const data = verificarSesionLocal();
    if  (data) {
        console.log("Sesión activa, redirigiendo...");
        return window.location.href = 'pages/panelControl.html';
    } else {
        console.log("No hay sesión activa, permaneciendo en la página de inicio de sesión.");
        if(verificarSesionApi()){
            console.log("Sesión activa en API, redirigiendo...");
            return window.location.href = 'pages/panelControl.html';
        } else {
            console.log("No hay sesión activa en API, permaneciendo en la página de inicio de sesión.");
        }
    }
    
    return window.location.href = 'pages/login.html';

});

function verificarTokenLife() {

}

function verificarSesionApi() {
    const sesion = get("auth/")
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