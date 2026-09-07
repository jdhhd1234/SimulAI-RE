const statusEl = document.querySelector("#status");
const chartCanvas = document.querySelector("#cash-chart");
const simulationTable = document.querySelector("#simulation-table");
const simulationDetails = document.querySelector(".simulation-details");
const mapChartCanvas = document.querySelector("#map-chart");
const debugMode = document.querySelector("#debug-mode");
const turnResults = document.querySelector("#turn-results");
const turnResultsList = document.querySelector("#turn-results-list");
const closeTurnResults = document.querySelector("#close-turn-results");

let cashChart;
let mapChart;
let latestSimulationData = [];
let debugDataLoaded = false;

function setResultsOpen(enabled) {
    if (!simulationDetails) {
        return;
    }

    simulationDetails.hidden = !enabled;
    document.body.classList.toggle("results-open", enabled);
    document.querySelector("main")?.classList.toggle("results-open", enabled);
}

function renderTurnResults(data) {
    if (!turnResultsList) {
        return;
    }

    turnResultsList.replaceChildren();
    data.forEach((point) => {
        const item = document.createElement("article");
        item.className = "turn-result-card";
        const keys = Object.keys(point).filter((key) => key !== "time" && key !== "ai_action");
        item.innerHTML = `
            <div class="turn-result-title">턴 ${point.time}</div>
            <div class="turn-result-values">
                ${keys.map((key) => `<span>${key} <strong>${typeof point[key] === "number" ? point[key].toLocaleString("ko-KR") : point[key]}</strong></span>`).join("")}
            </div>
            ${point.ai_action ? `<div class="turn-result-action">AI 전략: <strong>${point.ai_action}</strong></div>` : ""}
        `;
        turnResultsList.appendChild(item);
    });
}

function renderTable(data) {
    const tableHead = simulationTable.querySelector("thead");
    const tableBody = simulationTable.querySelector("tbody");
    const columns = Object.keys(data[0]);
    const headerRow = document.createElement("tr");

    tableHead.replaceChildren();
    tableBody.replaceChildren();

    columns.forEach((column) => {
        const cell = document.createElement("th");
        cell.textContent = column;
        headerRow.appendChild(cell);
    });
    tableHead.appendChild(headerRow);

    data.forEach((point) => {
        const row = document.createElement("tr");

        columns.forEach((column) => {
            const cell = document.createElement("td");
            const value = point[column];
            cell.textContent = typeof value === "number"
                ? value.toLocaleString("ko-KR", { maximumFractionDigits: 2 })
                : value;
            row.appendChild(cell);
        });

        tableBody.appendChild(row);
    });
}

function renderSimulation(data) {
    if (!data?.length || !chartCanvas) {
        return;
    }

    latestSimulationData = data;
    renderTurnResults(data);
    cashChart?.destroy();
    mapChart?.destroy();

    const chartColors = ["#ffffff", "#4fc3f7", "#ffb74d", "#81c784", "#e57373", "#ba68c8", "#fff176", "#4db6ac"];
    const gridColor = "#333333";
    const tickColor = "#888888";

    const numericKeys = Object.keys(data[0]).filter((key) => key !== "time" && key !== "ai_action" && typeof data[0][key] === "number");

    if (mapChartCanvas) {
        mapChart = new Chart(mapChartCanvas, {
            type: "line",
            data: {
                labels: data.map((point) => point.time),
                datasets: numericKeys.map((key, i) => ({
                    label: key,
                    data: data.map((point) => point[key]),
                    tension: 0.1,
                    borderColor: chartColors[i % chartColors.length],
                    backgroundColor: "transparent",
                })),
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: tickColor, maxTicksLimit: 5, font: { size: 10 } },
                    },
                    y: {
                        grid: { color: "#222222" },
                        ticks: { color: tickColor, maxTicksLimit: 4, font: { size: 10 } },
                    },
                },
                plugins: { legend: { labels: { color: tickColor, boxWidth: 8, font: { size: 10 } } } },
            },
        });
    }

    cashChart = new Chart(chartCanvas, {
        type: "line",
        data: {
            labels: data.map((point) => point.time),
            datasets: numericKeys.map((key, i) => ({
                    label: key,
                    data: data.map((point) => point[key]),
                    tension: 0.1,
                    borderColor: chartColors[i % chartColors.length],
                    backgroundColor: "transparent",
                })),
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            scales: {
                x: { grid: { color: gridColor }, ticks: { color: tickColor } },
                y: { grid: { color: gridColor }, ticks: { color: tickColor } },
            },
            plugins: { legend: { labels: { color: tickColor } } },
        },
    });

    renderTable(data);
    debugDataLoaded = true;
}

function setDebugMode(enabled) {
    setResultsOpen(enabled);
    if (enabled && latestSimulationData.length) {
        renderSimulation(latestSimulationData);
    }
}

document.addEventListener("company-data", (event) => {
    const data = event.detail?.data;
    if (!data?.length) {
        return;
    }

    renderSimulation(data);
    setResultsOpen(true);
    if (turnResults) {
        turnResults.hidden = false;
    }
    if (statusEl) {
        statusEl.textContent = "연결됨";
    }
});

if (closeTurnResults) {
    closeTurnResults.addEventListener("click", () => {
        if (turnResults) {
            turnResults.hidden = true;
        }
    });
}

const debugFromUrl = new URLSearchParams(window.location.search).get("debug") === "true";
if (debugMode) {
    debugMode.checked = debugFromUrl;
    debugMode.addEventListener("change", () => setDebugMode(debugMode.checked));
}
setDebugMode(debugFromUrl);
