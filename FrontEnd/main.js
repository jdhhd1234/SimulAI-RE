const form = document.querySelector("#simulation-form");
const inputCashInit = document.querySelector("#input-value-cash-init");
const inputDebtInit = document.querySelector("#input-value-debt-init");
const inputSellPrice = document.querySelector("#input-value-sell-price");
const inputDeltaTime = document.querySelector("#input-value-deltatime")
const inputStopTime = document.querySelector("#input-value-stoptime")

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
                    results.map((item) => item.final_profit),
                    "#16a34a"
                ),
                createLineDataset(
                    "부채",
                    results.map((item) => item.debt),
                    "#dc2626"
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
                    "제품 수량",
                    results.map((item) => item.product_count),
                    "#a16207"
                ),
                createLineDataset(
                    "제품 판매 가격",
                    results.map((item) => item.sell_price),
                    "#7c3aed"
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
                        text: "값"
                    }
                }
            }
        }
    });
}

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const requestData = {
        cash_init: Number(inputCashInit.value),
        debt_init: Number(inputDebtInit.value),
        sell_price: Number(inputSellPrice.value),
        deltatime: Number(inputDeltaTime.value),
        stoptime: Number(inputStopTime.value)
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
        const message = error instanceof Error ? error.message : String(error);
        console.error("시뮬레이션 요청 오류:", error);
        status.textContent = `시뮬레이션 요청에 실패했습니다. (${message})`;
    }
});
