const statusEl = document.querySelector("#status");
const chartCanvas = document.querySelector("#cash-chart");
const simulationTable = document.querySelector("#simulation-table");
const simulationDetails = document.querySelector(".simulation-details");
const mapChartCanvas = document.querySelector("#map-chart");
const debugMode = document.querySelector("#debug-mode");
const mapViewToggle = document.querySelector(".map-view-toggle");
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

function scaleValue(value) {
    if (!Number.isFinite(value)) {
        return null;
    }

    return Math.sign(value) * Math.log10(1 + Math.abs(value));
}

function scaleSeries(series) {
    return series.map(scaleValue);
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
    const allNumbers = data.flatMap((point) => numericKeys.map((key) => point[key]).filter(Number.isFinite));
    const maxAbs = allNumbers.length ? Math.max(...allNumbers.map((value) => Math.abs(value))) : 0;
    const useLogScale = maxAbs > 10000;

    if (mapChartCanvas) {
        mapChart = new Chart(mapChartCanvas, {
            type: "line",
            data: {
                labels: data.map((point) => point.time),
                datasets: numericKeys.map((key, i) => ({
                    label: key,
                    data: useLogScale ? scaleSeries(data.map((point) => point[key])) : data.map((point) => point[key]),
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
                        ticks: { color: tickColor, maxTicksLimit: 2, font: { size: 10 } },
                    },
                    y: {
                        grid: { color: "#222222" },
                        ticks: { color: tickColor, maxTicksLimit: 2, font: { size: 10 } },
                        title: useLogScale ? { display: false, text: "log10(1+|x|)", color: tickColor, font: { size: 5 } } : undefined,
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
                    data: useLogScale ? scaleSeries(data.map((point) => point[key])) : data.map((point) => point[key]),
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
                y: {
                    grid: { color: gridColor },
                    ticks: { color: tickColor },
                    title: useLogScale ? { display: false, text: "log10(1+|x|)", color: tickColor, font: { size: 10 } } : undefined,
                },
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

function setMapView(view) {
    const mapPanel = document.querySelector(".map-panel");
    if (!mapPanel) {
        return;
    }

    const chartView = view === "chart";
    mapPanel.classList.toggle("chart-view", chartView);

    mapViewToggle?.querySelectorAll("button").forEach((button) => {
        const active = button.dataset.view === view;
        button.classList.toggle("active", active);
        button.setAttribute("aria-pressed", String(active));
    });

    if (chartView) {
        requestAnimationFrame(() => mapChart?.resize());
    }

    document.dispatchEvent(new CustomEvent("map-view-change", { detail: { view } }));
}

if (mapViewToggle) {
    mapViewToggle.addEventListener("click", (event) => {
        const button = event.target.closest("button[data-view]");
        if (!button) {
            return;
        }
        setMapView(button.dataset.view);
    });
}

const debugFromUrl = new URLSearchParams(window.location.search).get("debug") === "true";
if (debugMode) {
    debugMode.checked = debugFromUrl;
    debugMode.addEventListener("change", () => setDebugMode(debugMode.checked));
}
setDebugMode(debugFromUrl);