const status = document.querySelector("#status");
const chartCanvas = document.querySelector("#cash-chart");

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
                    .filter((key) => key !== "time")
                    .map((key) => ({
                        label: key,
                        data: data.map((point) => point[key]),
                        tension: 0.1,
                    })),
            },
        });
        status.textContent = "Connected";
    } catch (error) {
        status.textContent = `Failed to load data: ${error.message}`;
    }
}

loadData();
