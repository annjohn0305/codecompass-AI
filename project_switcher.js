(function () {
    const select = document.querySelector("[data-route-base]");

    if (!select) {
        return;
    }

    select.addEventListener("change", function () {
        if (!this.value) {
            return;
        }

        this.disabled = true;
        window.location.href = `${this.dataset.routeBase}${this.value}/`;
    });
})();
