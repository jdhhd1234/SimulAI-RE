const status = document.querySelector("#status");
const chartCanvas = document.querySelector("#cash-chart");
const workersChartCanvas = document.querySelector("#workers-chart");
const demandChartCanvas = document.querySelector("#demand-chart");
const simulationTable = document.querySelector("#simulation-table");
const simulationDetails = document.querySelector(".simulation-details");
const debugMode = document.querySelector("#debug-mode");
const turnResults = document.querySelector("#turn-results");
const turnResultsList = document.querySelector("#turn-results-list");
const closeTurnResults = document.querySelector("#close-turn-results");

let cashChart;
let workersChart;
let demandChart;
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
        item.innerHTML = `
            <div class="turn-result-title">턴 ${point.time}</div>
            <div class="turn-result-values">
                <span>자금 <strong>${point.cash.toLocaleString("ko-KR")}</strong></span>
                <span>수익 <strong>${point.profit.toLocaleString("ko-KR")}</strong></span>
                <span>부채 <strong>${point.debt.toLocaleString("ko-KR")}</strong></span>
                <span>병력 <strong>${point.workers.toLocaleString("ko-KR")}</strong></span>
                <span>매출 <strong>${point.revenue.toLocaleString("ko-KR")}</strong></span>
                <span>수요 <strong>${point.demand.toLocaleString("ko-KR")}</strong></span>
            </div>
            <div class="turn-result-action">AI 전략: <strong>${point.ai_action || "--"}</strong></div>
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
    workersChart?.destroy();
    demandChart?.destroy();

    const chartColors = ["#ffffff", "#aaaaaa", "#666666", "#444444"];
    const gridColor = "#333333";
    const tickColor = "#888888";

    cashChart = new Chart(chartCanvas, {
        type: "line",
        data: {
            labels: data.map((point) => point.time),
            datasets: Object.keys(data[0])
                .filter((key) => !["time", "workers", "demand", "previous_demand", "ai_action"].includes(key))
                .map((key, i) => ({
                    label: key,
                    data: data.map((point) => point[key]),
                    tension: 0.1,
                    borderColor: chartColors[i % chartColors.length],
                    backgroundColor: "transparent",
                })),
        },
        options: {
            scales: {
                x: { grid: { color: gridColor }, ticks: { color: tickColor } },
                y: { grid: { color: gridColor }, ticks: { color: tickColor } },
            },
            plugins: { legend: { labels: { color: tickColor } } },
        },
    });

    workersChart = new Chart(workersChartCanvas, {
        type: "line",
        data: {
            labels: data.map((point) => point.time),
            datasets: [
                {
                    label: "workers",
                    data: data.map((point) => point.workers),
                    tension: 0.1,
                    borderColor: "#ffffff",
                    backgroundColor: "transparent",
                },
            ],
        },
        options: {
            scales: {
                x: { grid: { color: gridColor }, ticks: { color: tickColor } },
                y: {
                    title: { display: true, text: "Workers", color: tickColor },
                    grid: { color: gridColor },
                    ticks: { color: tickColor },
                },
            },
            plugins: { legend: { labels: { color: tickColor } } },
        },
    });

    demandChart = new Chart(demandChartCanvas, {
        type: "line",
        data: {
            labels: data.map((point) => point.time),
            datasets: ["demand", "previous_demand"].map((key, i) => ({
                label: key,
                data: data.map((point) => point[key]),
                tension: 0.1,
                borderColor: i === 0 ? "#ffffff" : "#666666",
                backgroundColor: "transparent",
            })),
        },
        options: {
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
    if (event.detail.showResults || debugMode?.checked) {
        setResultsOpen(true);
        if (turnResults) {
            turnResults.hidden = false;
        }
        if (status) {
            status.textContent = "연결됨";
        }
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
