(function () {
    const healthScore = document.querySelector("[data-health-score]");

    document.documentElement.classList.add("js-ready");

    if (!healthScore) {
        return;
    }

    const rawScore = Number.parseInt(healthScore.dataset.healthScore, 10);
    const score = Number.isFinite(rawScore) ? Math.max(0, Math.min(rawScore, 100)) : 0;

    window.requestAnimationFrame(function () {
        healthScore.style.setProperty("--health", score);
    });
})();
