const COMMANDS = [
    { id: 'home', name: 'Go Home', icon: '🏠', url: '/', tags: ['home'] },
    { id: 'simulation', name: 'Go Simulation', icon: '🎮', url: '/index', tags: ['simulation'] },
    { id: 'pomodoro', name: 'Go Pomodoro', icon: '⏱️', url: '/pomodoro', tags: ['pomodoro'] },
    { id: 'history', name: 'Go History', icon: '📜', url: '/history', tags: ['history'] },
    { id: 'dashboard', name: 'Go Dashboard', icon: '📊', url: '/dashboard', tags: ['dashboard'] },
    { id: 'planner', name: 'Go Planner', icon: '📅', url: '/planner', tags: ['planner'] },
    { id: 'settings', name: 'Go Settings', icon: '⚙️', url: '/settings', tags: ['settings'] }
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

function renderList(){
    cmdList.innerHTML = "";

    if(filteredCommands.length === 0){

        cmdList.innerHTML =
            '<li class="cmd-empty">No command found</li>';

        return;
    }

    filteredCommands.forEach((cmd, index) => {

        const li = document.createElement("li");

        li.className =
            "cmd-item" +
            (index === selectedIndex ? " active" : "");

        li.innerHTML =
            `<span class="cmd-item-icon">${cmd.icon}</span>
             <span>${cmd.name}</span>`;

        li.onclick = () => {

            if(cmd.url){
                window.location.href = cmd.url;
            }
        };

        li.onmouseover = () => {
            selectedIndex = index;
            renderList();
        };

        cmdList.appendChild(li);
    });
}

function scoreCommand(cmd, query){
    query = query.toLowerCase()

    let score = 0;

    if(cmd.name.toLowerCase().includes(query)) score += 3;
    if(cmd.id.toLowerCase().includes(query)) score += 2;
    
    for(const tag of (cmd.tags || [])){
        if(tag.toLowerCase().includes(query)) score += 2;
    }

    return score;
}

function filterCommands(query) {
    if (!query) {
        filteredCommands = [...COMMANDS];
    } else {
        filteredCommands = COMMANDS
        .map(cmd => ({
            ...cmd,
            score: scoreCommand(cmd, query)
        }))
        .filter(cmd => cmd.score > 0)
        .sort((a, b) => b.score - a.score);
    }
    selectedIndex = 0;
    renderList();
}

function getSelected(){
    if(!filteredCommands.length) return null;
    return filteredCommands[selectedIndex];
}

cmdInput.addEventListener("input", function(e) {
    filterCommands(e.target.value.trim());
    cmdbar.classList.remove("shake-error")
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

        const cmd = getSelected();

        if (cmd && cmd.url) {
            window.location.href = cmd.url;
        } else {
            cmdbar.classList.remove("shake-error");
            void cmdbar.offsetWidth; 
            cmdbar.classList.add("shake-error");
        }
    }
});
