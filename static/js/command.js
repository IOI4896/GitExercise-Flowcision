const COMMANDS = [
    { id: 'home', name: 'Go Home', icon: '🏠', url: '/' },
    { id: 'simulation', name: 'Go Simulation', icon: '🎮', url: '/index' },
    { id: 'pomodoro', name: 'Go Pomodoro', icon: '⏱️', url: '/pomodoro' },
    { id: 'history', name: 'Go History', icon: '📜', url: '/history' },
    { id: 'dashboard', name: 'Go Dashboard', icon: '📊', url: '/dashboard' },
    { id: 'planner', name: 'Go Planner', icon: '📅', url: '/planner' },
    { id: 'settings', name: 'Go Settings', icon: '⚙️', url: '/settings' }
];

let selectedIndex = 0;
let filteredCommands = [...COMMANDS];

const cmdbar = document.getElementById("cmdbar");
const cmdInput = document.getElementById("commandInput");
const cmdList = document.getElementById("cmd-list");

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
    cmdbar.style.display = show ? "block": "none";
    if (show) {
        cmdInput.value = "";
        filterCommands("");
        cmdInput.focus();
        cmdbar.classList.remove("shake-error");
    }
}

function renderList() {
    cmdList.innerHTML = "";
    filteredCommands.forEach((cmd, index) => {
        const li = document.createElement("li");
        li.className = "cmd-item" + (index === selectedIndex ? " active" : "");
        li.innerHTML = `<span class="cmd-item-icon">${cmd.icon}</span><span>${cmd.name}</span>`;
        li.onclick = () => window.location.href = cmd.url;
        li.onmouseover = () => {
            selectedIndex = index;
            renderList();
        };
        cmdList.appendChild(li);
    });
}

function filterCommands(query) {
    if (!query) {
        filteredCommands = [...COMMANDS];
    } else {
        const lowerQuery = query.toLowerCase();
        filteredCommands = COMMANDS.filter(cmd => 
            cmd.name.toLowerCase().includes(lowerQuery) || 
            cmd.id.toLowerCase().includes(lowerQuery)
        );
    }
    selectedIndex = 0;
    renderList();
}

cmdInput.addEventListener("input", function(e) {
    filterCommands(e.target.value);
    cmdbar.classList.remove("shake-error");
});

cmdInput.addEventListener("keydown", function(e){
    if (e.key === "ArrowDown") {
        e.preventDefault();
        if (filteredCommands.length > 0) {
            selectedIndex = (selectedIndex + 1) % filteredCommands.length;
            renderList();
        }
    } else if (e.key === "ArrowUp") {
        e.preventDefault();
        if (filteredCommands.length > 0) {
            selectedIndex = (selectedIndex - 1 + filteredCommands.length) % filteredCommands.length;
            renderList();
        }
    } else if (e.key === "Enter") {
        e.preventDefault();
        if (filteredCommands.length > 0) {
            window.location.href = filteredCommands[selectedIndex].url;
        } else {
            // 触发震动动画
            cmdbar.classList.remove("shake-error");
            void cmdbar.offsetWidth; 
            cmdbar.classList.add("shake-error");
        }
    }
});