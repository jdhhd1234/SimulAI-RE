const fileSelect = document.querySelector("#lua-file");
const sourceEl = document.querySelector("#source");
const consoleEl = document.querySelector("#console");
const runButton = document.querySelector("#run");
const sectorBody = document.querySelector("#sector-table tbody");

let chart;

function renderConsole(lines, error) {
    consoleEl.textContent = [...lines, ...(error ? [`ERROR: ${error}`] : [])].join("\n") || "출력이 없습니다.";
}

async function loadSource() {
    const file = await api(`/lua/files/${encodeURIComponent(fileSelect.value)}`);
    sourceEl.textContent = file.source;
}

async function loadFiles() {
    const names = await api("/lua/files");
    names.forEach((name) => fileSelect.add(new Option(name, name)));
    if (names.length) {
        await loadSource();
        setStatus("준비");
    } else {
        setStatus("LuaPy 폴더에 .lua 파일이 없습니다.", true);
    }
}

function renderSectors(sectors) {
    sectorBody.replaceChildren();
    sectors.forEach((sector) => {
        const rule = sector.link.production_rule;
        const cells = [
            sector.summary.sector,
            rule
                ? `${Object.entries(rule.need_resource || {}).map(([name, amount]) => `${name} x${amount}`).join(", ")} → output (${rule.yield_rate})`
                : "-",
            sector.summary.factory_count,
            fmt(sector.summary.capacity),
            sector.summary.locations.map((pos) => `(${pos[0]}, ${pos[1]})`).join(" ") || "-",
        ];
        const row = document.createElement("tr");
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
        to_map: document.querySelector("#to-map").checked,
    });

    setStatus("실행 중...");
    runButton.disabled = true;
    try {
        const result = await api(`/lua/run/${encodeURIComponent(fileSelect.value)}?${params}`, { method: "POST" });
        renderConsole(result.console || []);
        chart = renderLineChart(document.querySelector("#chart"), chart, result.time, result.series);
        renderSectors(result.sectors || []);
        setStatus(result.company_ids?.length ? `완료 · 지도 자산 ${result.company_ids.length}개 등록` : "완료");
    } catch (error) {
        renderConsole(error.detail?.console || [], error.message);
        setStatus(error.message, true);
    } finally {
        runButton.disabled = false;
    }
}

fileSelect.addEventListener("change", () => loadSource().catch((error) => setStatus(error.message, true)));
runButton.addEventListener("click", runLua);
loadFiles().catch((error) => setStatus(error.message, true));
