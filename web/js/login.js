console.log("Login.js cargado");



function Login() {
    const email = document.getElementById("emailInput").value;
    const password = document.getElementById("passwordInput").value;

    if (!email || !password) {
        alert("Por favor, completa ambos campos.");
        return;
    }
}
