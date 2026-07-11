const zipBtn = document.getElementById("zip-btn");
const githubBtn = document.getElementById("github-btn");

const zipSection = document.getElementById("zip-section");
const githubSection = document.getElementById("github-section");

zipBtn.addEventListener("click", () => {

    zipSection.style.display = "block";
    githubSection.style.display = "none";

    zipBtn.classList.add("active");
    githubBtn.classList.remove("active");

});

githubBtn.addEventListener("click", () => {

    zipSection.style.display = "none";
    githubSection.style.display = "block";

    githubBtn.classList.add("active");
    zipBtn.classList.remove("active");

});

/* Browse Files */

const browseBtn = document.getElementById("browse-btn");
const fileInput = document.getElementById("file-input");

browseBtn.addEventListener("click", () => {

    fileInput.click();

});

fileInput.addEventListener("change", () => {

    if(fileInput.files.length > 0){

        window.location.href = "/analysis/";

    }

});