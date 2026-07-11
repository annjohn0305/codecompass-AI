document.addEventListener("DOMContentLoaded", () => {

    console.log("CodeCompass AI Loaded 🚀");

    // Feature Card Hover Animation
    const cards = document.querySelectorAll(".card");

    cards.forEach(card => {

        card.addEventListener("mouseenter", () => {
            card.style.transform = "translateY(-10px)";
            card.style.transition = "0.3s ease";
        });

        card.addEventListener("mouseleave", () => {
            card.style.transform = "translateY(0px)";
        });

    });

    // Navbar Shadow on Scroll
    const navbar = document.querySelector(".navbar");

    window.addEventListener("scroll", () => {

        if (window.scrollY > 50) {

            navbar.style.background = "#0b1026";
            navbar.style.boxShadow = "0 4px 20px rgba(0,0,0,0.3)";

        } else {

            navbar.style.background = "transparent";
            navbar.style.boxShadow = "none";

        }

    });

    // Smooth Fade-In Animation
    const hero = document.querySelector(".hero-content");

    if (hero) {

        hero.style.opacity = "0";
        hero.style.transform = "translateY(30px)";

        setTimeout(() => {

            hero.style.transition = "all 1s ease";
            hero.style.opacity = "1";
            hero.style.transform = "translateY(0)";

        }, 200);

    }

});