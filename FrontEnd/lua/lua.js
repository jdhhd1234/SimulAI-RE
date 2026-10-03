const fileSelect = document.querySelector("#lua-file");
const sourceEl = document.querySelector("#source");
const statusEl = document.querySelector("#status");
const consoleEl = document.querySelector("#console");
const runButton = document.querySelector("#run");
const sectorBody = document.querySelector("#sector-table tbody");
const chartCanvas = document.querySelector("#chart");

const chartColors = ["#ffffff", "#4fc3f7", "#ffb74d", "#81c784", "#e57373", "#ba68c8", "#fff176", "#4db6ac"];
let chart;

function setStatus(message, isError = false) {
    statusEl.textContent = message;
    statusEl.classList.toggle("error", isError);
}

function renderConsole(lines, error) {
    consoleEl.textContent = [...lines, ...(error ? [`ERROR: ${error}`] : [])].join("\n") || "출력이 없습니다.";
}

async function loadSource() {
    const response = await fetch(`/lua/files/${encodeURIComponent(fileSelect.value)}`);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    const file = await response.json();
    sourceEl.textContent = file.source;
}

async function loadFiles() {
    const response = await fetch("/lua/files");
    const names = await response.json();

    names.forEach((name) => {
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        fileSelect.appendChild(option);
    });

    if (names.length) {
        await loadSource();
    } else {
        setStatus("LuaPy 폴더에 .lua 파일이 없습니다.", true);
    }
}

function renderChart(result) {
    chart?.destroy();
    chart = new Chart(chartCanvas, {
        type: "line",
        data: {
            labels: result.time,
            datasets: Object.keys(result.series).map((key, i) => ({
                label: key,
                data: result.series[key],
                tension: 0.1,
                borderColor: chartColors[i % chartColors.length],
                backgroundColor: "transparent",
            })),
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { color: "#333" }, ticks: { color: "#888" } },
                y: { grid: { color: "#333" }, ticks: { color: "#888" } },
            },
            plugins: { legend: { labels: { color: "#888" } } },
        },
    });
}

function renderSectors(sectors) {
    sectorBody.replaceChildren();
    sectors.forEach((sector) => {
        const row = document.createElement("tr");
        const cells = [
            sector.summary.sector,
            sector.link.production_rule
                ? `${Object.entries(sector.link.production_rule.need_resource).map(([name, amount]) => `${name} x${amount}`).join(", ")} -> output (${sector.link.production_rule.yield_rate})`
                : "-",
            sector.summary.factory_count,
            sector.summary.capacity,
            sector.summary.locations.map((pos) => `(${pos[0]}, ${pos[1]})`).join(" ") || "-",
        ];
        cells.forEach((value) => {
            const cell = document.createElement("td");
            cell.textContent = value;
            row.appendChild(cell);
        });
        sectorBody.appendChild(row);
    });
}

async function runLua() {
    const params = new URLSearchParams({
        start: document.querySelector("#start").value,
        stop: document.querySelector("#stop").value,
        dt: document.querySelector("#dt").value,
    });

    setStatus("실행 중...");
    runButton.disabled = true;
    try {
        const response = await fetch(`/lua/run/${encodeURIComponent(fileSelect.value)}?${params}`, { method: "POST" });
        const result = await response.json();
        if (!response.ok) {
            const detail = result.detail || {};
            const message = typeof detail === "string" ? detail : detail.message || JSON.stringify(detail);
            renderConsole(detail.console || [], message);
            throw new Error(message);
        }
        renderConsole(result.console || []);
        renderChart(result);
        renderSectors(result.sectors);
        setStatus("완료");
    } catch (error) {
        setStatus(error.message, true);
    } finally {
        runButton.disabled = false;
    }
}

fileSelect.addEventListener("change", () => loadSource().catch((error) => setStatus(error.message, true)));
runButton.addEventListener("click", runLua);
loadFiles().catch((error) => setStatus(error.message, true));
