const status = document.querySelector("#status");
const chartCanvas = document.querySelector("#cash-chart");
const workersChartCanvas = document.querySelector("#workers-chart");
const demandChartCanvas = document.querySelector("#demand-chart");
const simulationTable = document.querySelector("#simulation-table");

async function loadData() {
    try {
        const response = await fetch("http://127.0.0.1:8000/data");

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        new Chart(chartCanvas, {
            type: "line",
            data: {
                labels: data.map((point) => point.time),
                datasets: Object.keys(data[0])
                    .filter((key) => !["time", "workers", "demand", "previous_demand"].includes(key))
                    .map((key) => ({
                        label: key,
                        data: data.map((point) => point[key]),
                        tension: 0.1,
                    })),
            },
        });

        new Chart(workersChartCanvas, {
            type: "line",
            data: {
                labels: data.map((point) => point.time),
                datasets: [
                    {
                        label: "workers",
                        data: data.map((point) => point.workers),
                        tension: 0.1,
                    },
                ],
            },
            options: {
                scales: {
                    y: {
                        title: {
                            display: true,
                            text: "Workers",
                        },
                    },
                },
            },
        });

        new Chart(demandChartCanvas, {
            type: "line",
            data: {
                labels: data.map((point) => point.time),
                datasets: ["demand", "previous_demand"].map((key) => ({
                    label: key,
                    data: data.map((point) => point[key]),
                    tension: 0.1,
                })),
            },
        });

        const columns = Object.keys(data[0]);
        const tableHead = simulationTable.querySelector("thead");
        const tableBody = simulationTable.querySelector("tbody");
        const headerRow = document.createElement("tr");

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
        status.textContent = "Connected";
    } catch (error) {
        status.textContent = `Failed to load data: ${error.message}`;
    }
}

loadData();
