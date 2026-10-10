// 지도/Lua 화면 공용 함수 (흑백 테마)
const GRAYS = ["#ffffff", "#b3b3b3", "#808080", "#5c5c5c"];
const DASHES = [[], [6, 4], [2, 3], [10, 3, 2, 3]];

function setStatus(message, isError = false) {
    const el = document.querySelector("#status");
    el.textContent = message;
    el.classList.toggle("error", isError);
}

function fmt(value) {
    return typeof value === "number"
        ? value.toLocaleString("ko-KR", { maximumFractionDigits: 2 })
        : value ?? "-";
}

async function api(path, options) {
    const response = await fetch(path, options);
    const body = await response.json().catch(() => null);
    if (!response.ok) {
        const detail = body?.detail;
        const message = typeof detail === "string" ? detail : detail?.message || `HTTP ${response.status}`;
        const error = new Error(message);
        error.detail = detail;
        throw error;
    }
    return body;
}

// 값 차이가 너무 크면 부호 유지 log 스케일로 그린다.
function renderLineChart(canvas, chart, labels, series) {
    chart?.destroy();
    const keys = Object.keys(series).filter((key) => series[key].some(Number.isFinite));
    const maxAbs = Math.max(0, ...keys.flatMap((key) => series[key].filter(Number.isFinite).map(Math.abs)));
    const useLog = maxAbs > 10000;
    const scale = (v) => (Number.isFinite(v) ? (useLog ? Math.sign(v) * Math.log10(1 + Math.abs(v)) : v) : null);

    return new Chart(canvas, {
        type: "line",
        data: {
            labels,
            datasets: keys.map((key, i) => ({
                label: key,
                data: series[key].map(scale),
                borderColor: GRAYS[i % GRAYS.length],
                borderDash: DASHES[Math.floor(i / GRAYS.length) % DASHES.length],
                borderWidth: 1.5,
                pointRadius: 0,
                tension: 0.1,
            })),
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            interaction: { mode: "index", intersect: false },
            scales: {
                x: { grid: { color: "#1a1a1a" }, ticks: { color: "#7a7a7a" } },
                y: {
                    grid: { color: "#1a1a1a" },
                    ticks: { color: "#7a7a7a" },
                    title: { display: useLog, text: "log10(1+|x|)", color: "#7a7a7a" },
                },
            },
            plugins: {
                legend: { labels: { color: "#b3b3b3", boxWidth: 12, boxHeight: 1 } },
                tooltip: { backgroundColor: "#0d0d0d", borderColor: "#262626", borderWidth: 1 },
            },
        },
    });
}

function renderTable(table, rows) {
    const head = table.querySelector("thead");
    const body = table.querySelector("tbody");
    head.replaceChildren();
    body.replaceChildren();
    if (!rows?.length) {
        return;
    }

    const columns = Object.keys(rows[0]);
    const headRow = document.createElement("tr");
    columns.forEach((column) => {
        const th = document.createElement("th");
        th.textContent = column;
        headRow.appendChild(th);
    });
    head.appendChild(headRow);

    rows.forEach((row) => {
        const tr = document.createElement("tr");
        columns.forEach((column) => {
            const td = document.createElement("td");
            td.textContent = fmt(row[column]);
            tr.appendChild(td);
        });
        body.appendChild(tr);
    });
}
