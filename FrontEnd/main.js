const form = document.querySelector("#simulation-form");
const inputPopulation = document.querySelector("#input-value-population");
const inputResource = document.querySelector("#input-value-resource");
const inputProductPrice = document.querySelector("#input-value-product-price");
const inputBuyExpense = document.querySelector("#input-value-buy-expense");

const status = document.querySelector("#status");
const financeCanvas = document.querySelector("#finance-chart");
const operationsCanvas = document.querySelector("#operations-chart");

let financeChart;
let operationsChart;

function destroyCharts() {
    financeChart?.destroy();
    operationsChart?.destroy();
    financeChart = undefined;
    operationsChart = undefined;
}

function createLineDataset(label, values, color) {
    return {
        label,
        data: values,
        borderColor: color,
        backgroundColor: color,
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        tension: 0.2,
        fill: false
    };
}

function renderCharts(results) {
    destroyCharts();

    const labels = results.map((item) => item.time);
    const sharedOptions = {
        responsive: true,
        maintainAspectRatio: false,
        interaction: {
            mode: "index",
            intersect: false
        },
        plugins: {
            legend: {
                position: "bottom"
            }
        },
        scales: {
            x: {
                title: {
                    display: true,
                    text: "시간"
                }
            },
            y: {
                beginAtZero: true
            }
        }
    };

    financeChart = new Chart(financeCanvas, {
        type: "line",
        data: {
            labels,
            datasets: [
                createLineDataset(
                    "현금",
                    results.map((item) => item.cash),
                    "#2563eb"
                ),
                createLineDataset(
                    "누적 이익",
                    results.map((item) => item.profit),
                    "#16a34a"
                )
            ]
        },
        options: {
            ...sharedOptions,
            scales: {
                ...sharedOptions.scales,
                y: {
                    ...sharedOptions.scales.y,
                    title: {
                        display: true,
                        text: "금액"
                    }
                }
            }
        }
    });

    operationsChart = new Chart(operationsCanvas, {
        type: "line",
        data: {
            labels,
            datasets: [
                createLineDataset(
                    "원자재",
                    results.map((item) => item.raw_material),
                    "#a16207"
                ),
                createLineDataset(
                    "제품",
                    results.map((item) => item.products),
                    "#7c3aed"
                ),
                createLineDataset(
                    "수요",
                    results.map((item) => item.demand),
                    "#dc2626"
                ),
                createLineDataset(
                    "생산량",
                    results.map((item) => item.production),
                    "#0891b2"
                ),
                createLineDataset(
                    "판매량",
                    results.map((item) => item.sales),
                    "#ea580c"
                )
            ]
        },
        options: {
            ...sharedOptions,
            scales: {
                ...sharedOptions.scales,
                y: {
                    ...sharedOptions.scales.y,
                    title: {
                        display: true,
                        text: "수량"
                    }
                }
            }
        }
    });
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const requestData = {
        population: Number(inputPopulation.value),
        resource: Number(inputResource.value),
        product_price: Number(inputProductPrice.value),
        buy_expense: Number(inputBuyExpense.value)
    };

    status.textContent = "Python API에 요청 중입니다...";

    try {
        const response = await fetch("http://127.0.0.1:8000/main", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        const data = await response.json();

        renderCharts(data.results);
        status.textContent = "시뮬레이션이 완료되었습니다.";
    } catch (error) {
        destroyCharts();
        status.textContent = "시뮬레이션 요청에 실패했습니다.";
    }
});
