document.addEventListener("keydown", function(e){
    if(e.ctrlKey && e.key === "k"){
        e.preventDefault();
        togglePalette(true);
    }

    if(e.key === "Escape"){
        togglePalette(false);
    }
});

function togglePalette(show){
    document.getElementById("cmdbar").style.display = show ? "block": "none";
}

const COMMANDS = {
    "go home": () => window.location.href = "/",
    "go simulation": () => window.location.href = "/index",
    "go pomodoro": () => window.location.href = "/pomodoro",
    "go history": () => window.location.href = "/history",
    "go dashboard": () => window.location.href = "/dashboard",
    "go planner": () => window.location.href = "/planner",
    "go settings": () => window.location.href = "/settings",
};

document.getElementById("commandInput").addEventListener("keydown", function(e){
    if(e.key === "Enter"){
        const value = this.value.toLowerCase().trim();

        if(COMMANDS[value]){
            COMMANDS[value]();
        }

        this.value = "";
        togglePalette(false);
    }
});