console.log("Login.js cargado");



async function  Login() {
    const email = document.getElementById("emailInput").value;
    const password = document.getElementById("passwordInput").value;

    if (!email || !password) {
        alert("Por favor, completa ambos campos.");
        return;
    }
    const CuentaNueva = await post("auth/login", { email, password });
    if (CuentaNueva) {
        localStorage.setItem("token", CuentaNueva.token);
        redirigir(ROUTES.PANEL_CONTROL);
    } else {
        alert("Error de autenticación: " + CuentaNueva.message);
    }
}
