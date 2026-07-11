let progress = 0;

const progressValue =
document.getElementById("progress-value");

const currentStep =
document.getElementById("current-step");

const steps = [

    "Extracting Files...",

    "Scanning Project Structure...",

    "Analyzing Code Quality...",

    "Detecting Technologies...",

    "Identifying Risks...",

    "Generating Recommendations..."

];

let stepIndex = 0;

const interval = setInterval(() => {

    progress += 2;

    progressValue.textContent =
    progress + "%";

    if(progress % 16 === 0 &&
       stepIndex < steps.length - 1){

        stepIndex++;

        currentStep.textContent =
        steps[stepIndex];

    }

    if(progress >= 100){

        clearInterval(interval);

        currentStep.textContent =
        "Analysis Complete ✅";

        setTimeout(() => {

            window.location.href =
            "/report/";

        }, 1500);

    }

}, 120);