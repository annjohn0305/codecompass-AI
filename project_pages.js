(function () {
    const select = document.querySelector("[data-project-select]");

    if (!select) {
        return;
    }

    const routeBase = select.dataset.routeBase;

    if (!routeBase) {
        return;
    }

    select.addEventListener("change", function () {
        const projectId = this.value;

        if (!projectId) {
            return;
        }

        document.body.classList.add("is-navigating");
        this.disabled = true;
        window.location.href = `${routeBase}${projectId}/`;
    });
})();
