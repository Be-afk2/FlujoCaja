async function loadComponents() {

    const elements = document.querySelectorAll("[data-component]")

    for (const el of elements) {

        const file = el.getAttribute("data-component")

        const resp = await fetch(file)
        const html = await resp.text()

        el.innerHTML = html
    }
}
loadComponents()