const API_BASE = "http://127.0.0.1:8000";

const elements = {
    form: document.querySelector("#simulation-form"),
    modelSelect: document.querySelector("#model-select"),
    modelMeta: document.querySelector("#model-meta"),
    schemaFields: document.querySelector("#schema-fields"),
    chartGrid: document.querySelector("#chart-grid"),
    status: document.querySelector("#status"),
    statusPill: document.querySelector("#status-pill"),
    resultMeta: document.querySelector("#result-meta"),
    runButton: document.querySelector("#run-button"),
    refreshButton: document.querySelector("#refresh-models")
};

const state = {
    models: [],
    schema: null,
    charts: [],
    loadingModels: false,
    loadingSchema: false,
    loadingSimulation: false
};

function setStatus(message, tone = "idle") {
    elements.status.textContent = message;
    elements.statusPill.textContent =
        tone === "loading" ? "불러오는 중" : tone === "error" ? "오류" : tone === "success" ? "완료" : "대기 중";
    elements.statusPill.className = `status-pill status-pill--${tone}`;
}

function setBusy(isBusy) {
    elements.runButton.disabled = isBusy || !state.schema;
    elements.modelSelect.disabled = isBusy || state.loadingModels || state.models.length === 0;
    elements.refreshButton.disabled = isBusy || state.loadingModels;
    elements.form.classList.toggle("is-busy", isBusy);
}

function escapeText(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#39;");
}

function normalizeNumber(value) {
    const num = Number(value);
    return Number.isFinite(num) ? num : null;
}

function formatErrorDetail(detail) {
    if (detail === null || detail === undefined || detail === "") {
        return "알 수 없는 오류가 발생했습니다.";
    }

    if (typeof detail === "string") {
        return detail;
    }

    if (Array.isArray(detail)) {
        const items = detail.map((item) => formatErrorDetail(item)).filter(Boolean);
        return items.length ? items.join(" · ") : "알 수 없는 오류가 발생했습니다.";
    }

    if (typeof detail === "object") {
        const path = Array.isArray(detail.loc)
            ? detail.loc.filter((part) => part !== null && part !== undefined && part !== "").join(".")
            : "";
        const message = typeof detail.message === "string"
            ? detail.message
            : typeof detail.msg === "string"
                ? detail.msg
                : typeof detail.detail === "string"
                    ? detail.detail
                    : typeof detail.error === "string"
                        ? detail.error
                        : "";

        if (path || message) {
            return path ? `${path}: ${message || "오류가 발생했습니다."}` : message;
        }

        const entries = Object.entries(detail)
            .map(([key, value]) => {
                const formatted = formatErrorDetail(value);
                return formatted ? `${key} ${formatted}` : key;
            })
            .filter(Boolean);

        return entries.length ? entries.join(" · ") : "알 수 없는 오류가 발생했습니다.";
    }

    return String(detail);
}

function destroyCharts() {
    state.charts.forEach((chart) => chart.destroy());
    state.charts = [];
}

function clearResults(message = "아직 실행된 시뮬레이션이 없습니다.") {
    destroyCharts();
    elements.chartGrid.innerHTML = `<div class="empty-state empty-state--large">${message}</div>`;
    elements.resultMeta.innerHTML = "";
}

function setModelMeta(schema) {
    if (!schema) {
        elements.modelMeta.textContent = "";
        return;
    }

    const description = schema.description?.trim() || "설명 없음";
    const counts = `${schema.inputs?.length ?? 0}개 입력 · ${schema.charts?.length ?? 0}개 차트`;
    elements.modelMeta.innerHTML = `<strong>${escapeText(schema.name || schema.id)}</strong><span>·</span><span>${escapeText(description)}</span><span>·</span><span>${escapeText(counts)}</span>`;
}

function createField(input) {
    const field = document.createElement("div");
    field.className = "input-card";

    const label = document.createElement("label");
    label.setAttribute("for", `input-${input.name}`);
    label.textContent = input.label || input.name;

    const inputEl = document.createElement("input");
    inputEl.type = "number";
    inputEl.id = `input-${input.name}`;
    inputEl.name = input.name;
    inputEl.value = input.default ?? 0;
    inputEl.step = input.step ?? "any";
    if (input.min !== undefined && input.min !== null) inputEl.min = input.min;
    if (input.max !== undefined && input.max !== null) inputEl.max = input.max;
    inputEl.required = true;

    const helper = document.createElement("div");
    helper.className = "input-help";
    const parts = [];
    if (input.min !== undefined && input.min !== null) parts.push(`최소 ${input.min}`);
    if (input.max !== undefined && input.max !== null) parts.push(`최대 ${input.max}`);
    if (input.step !== undefined && input.step !== null) parts.push(`간격 ${input.step}`);
    helper.textContent = parts.join(" · ") || "수치 값을 입력하세요.";

    field.append(label, inputEl, helper);
    return field;
}

function renderSchema(schema) {
    state.schema = schema;
    destroyCharts();
    elements.resultMeta.innerHTML = "";
    setModelMeta(schema);

    if (!schema?.inputs?.length) {
        elements.schemaFields.innerHTML = '<div class="empty-state">이 모델에는 입력 항목이 없습니다.</div>';
    } else {
        elements.schemaFields.innerHTML = "";
        schema.inputs.forEach((input) => {
            elements.schemaFields.appendChild(createField(input));
        });
    }

    elements.runButton.disabled = state.loadingSimulation || !state.schema;
}

function renderModelOptions(models) {
    elements.modelSelect.innerHTML = "";

    if (!models.length) {
        const option = document.createElement("option");
        option.value = "";
        option.textContent = "사용 가능한 모델이 없습니다";
        elements.modelSelect.appendChild(option);
        elements.modelSelect.disabled = true;
        return;
    }

    const placeholder = document.createElement("option");
    placeholder.value = "";
    placeholder.textContent = "모델을 선택하세요";
    placeholder.disabled = true;
    placeholder.selected = true;
    elements.modelSelect.appendChild(placeholder);

    models.forEach((model) => {
        const option = document.createElement("option");
        option.value = model.id;
        option.textContent = model.name;
        elements.modelSelect.appendChild(option);
    });

    elements.modelSelect.disabled = false;
}

async function fetchJson(url, options = {}) {
    const controller = new AbortController();
    const timeoutMs = options.timeoutMs ?? 15000;
    const timeout = window.setTimeout(() => controller.abort(), timeoutMs);

    try {
        const response = await fetch(url, {
            ...options,
            signal: controller.signal,
            headers: {
                Accept: "application/json",
                ...(options.headers || {})
            }
        });

        const contentType = response.headers.get("content-type") || "";
        const payload = contentType.includes("application/json") ? await response.json().catch(() => ({})) : await response.text();

        if (!response.ok) {
            const detail = typeof payload === "string" ? payload : payload?.detail ?? payload?.message ?? `HTTP ${response.status}`;
            throw new Error(formatErrorDetail(detail));
        }

        return payload;
    } catch (error) {
        if (error?.name === "AbortError") {
            throw new Error("요청 시간이 초과되었습니다.");
        }
        throw error;
    } finally {
        window.clearTimeout(timeout);
    }
}

async function loadModels() {
    state.loadingModels = true;
    setBusy(true);
    setStatus("모델 목록을 불러오는 중입니다...", "loading");
    elements.modelMeta.textContent = "";
    clearResults("모델을 선택하면 결과 차트가 표시됩니다.");

    try {
        const data = await fetchJson(`${API_BASE}/models`);
        state.models = Array.isArray(data.models) ? data.models : [];
        renderModelOptions(state.models);
        setBusy(false);

        if (!state.models.length) {
            setStatus("사용 가능한 모델이 없습니다.", "error");
            elements.schemaFields.innerHTML = '<div class="empty-state">모델 목록이 비어 있습니다.</div>';
            return;
        }

        setStatus("모델을 선택하세요.", "idle");
        const firstModel = state.models[0];
        elements.modelSelect.value = firstModel.id;
        await loadSchema(firstModel.id);
    } catch (error) {
        state.models = [];
        renderModelOptions([]);
        elements.schemaFields.innerHTML = '<div class="empty-state">모델을 불러오지 못했습니다.</div>';
        setStatus(`모델 목록 불러오기 실패: ${error instanceof Error ? error.message : String(error)}`, "error");
    } finally {
        state.loadingModels = false;
        setBusy(false);
    }
}

async function loadSchema(modelId) {
    if (!modelId) return;

    state.loadingSchema = true;
    setBusy(true);
    setStatus("모델 정보를 불러오는 중입니다...", "loading");
    clearResults("입력 정보를 불러오면 차트를 준비합니다.");
    elements.schemaFields.innerHTML = '<div class="empty-state">입력 정보를 불러오는 중...</div>';

    try {
        const schema = await fetchJson(`${API_BASE}/models/${encodeURIComponent(modelId)}/schema`);
        renderSchema(schema);
        setStatus(`"${schema.name || schema.id}" 모델이 준비되었습니다.`, "success");
    } catch (error) {
        state.schema = null;
        destroyCharts();
        elements.schemaFields.innerHTML = '<div class="empty-state">입력 정보를 불러오지 못했습니다.</div>';
        setModelMeta(null);
        setStatus(`입력 정보 불러오기 실패: ${error instanceof Error ? error.message : String(error)}`, "error");
    } finally {
        state.loadingSchema = false;
        setBusy(false);
        elements.runButton.disabled = !state.schema;
    }
}

function buildRequestData() {
    const data = {};
    state.schema?.inputs?.forEach((input) => {
        const field = elements.form.elements.namedItem(input.name);
        const rawValue = field?.value;
        data[input.name] = rawValue === "" || rawValue === undefined || rawValue === null ? null : normalizeNumber(rawValue);
    });
    return data;
}

function getSeriesValue(row, key) {
    const value = row?.[key];
    return normalizeNumber(value);
}

function createChartCard(chartSchema, results) {
    const card = document.createElement("article");
    card.className = "chart-card";

    const title = document.createElement("h3");
    title.textContent = chartSchema.title || chartSchema.id;

    const container = document.createElement("div");
    container.className = "chart-container";

    const canvas = document.createElement("canvas");
    canvas.height = 280;
    container.appendChild(canvas);
    card.append(title, container);

    const labels = results.map((row, index) => {
        const time = row?.time;
        return time !== undefined && time !== null ? time : index;
    });

    const datasets = (chartSchema.series || []).map((series) => ({
        label: series.label || series.key,
        data: results.map((row) => getSeriesValue(row, series.key)),
        borderColor: series.color || "#2563eb",
        backgroundColor: series.color || "#2563eb",
        borderWidth: 2,
        pointRadius: 0,
        pointHoverRadius: 4,
        tension: 0.28,
        fill: false,
        spanGaps: true
    }));

    const chart = new Chart(canvas, {
        type: "line",
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 700 },
            interaction: {
                mode: "index",
                intersect: false
            },
            plugins: {
                legend: {
                    position: "bottom",
                    labels: {
                        usePointStyle: true,
                        boxWidth: 10,
                        boxHeight: 10,
                        color: "#475569"
                    }
                },
                tooltip: {
                    backgroundColor: "rgba(15, 23, 42, 0.95)",
                    titleColor: "#f8fafc",
                    bodyColor: "#e2e8f0",
                    borderColor: "rgba(148, 163, 184, 0.2)",
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    title: { display: true, text: "시간" },
                    grid: { color: "rgba(148, 163, 184, 0.16)" },
                    ticks: { color: "#64748b" }
                },
                y: {
                    beginAtZero: false,
                    grid: { color: "rgba(148, 163, 184, 0.16)" },
                    ticks: { color: "#64748b" }
                }
            }
        }
    });

    state.charts.push(chart);
    return card;
}

function renderResults(response) {
    destroyCharts();

    const results = Array.isArray(response.results) ? response.results : [];
    if (!results.length) {
        clearResults("반환된 결과가 없습니다.");
        return;
    }

    const modelName = typeof response.model === "string"
        ? response.model
        : response.model?.name || state.schema?.name || state.schema?.id || "모델";
    const timeRange = `${response.starttime ?? "-"} → ${response.stoptime ?? "-"} (dt ${response.dt ?? "-"})`;
    elements.resultMeta.innerHTML = `
        <div class="meta-chip"><span>모델</span><strong>${escapeText(modelName)}</strong></div>
        <div class="meta-chip"><span>시뮬레이션 구간</span><strong>${escapeText(timeRange)}</strong></div>
        <div class="meta-chip"><span>샘플 수</span><strong>${results.length}개</strong></div>
    `;

    elements.chartGrid.innerHTML = "";
    (state.schema?.charts || []).forEach((chartSchema) => {
        elements.chartGrid.appendChild(createChartCard(chartSchema, results));
    });

    if (!state.schema?.charts?.length) {
        elements.chartGrid.innerHTML = '<div class="empty-state empty-state--large">이 모델에는 차트 정의가 없습니다.</div>';
    }
}

elements.modelSelect.addEventListener("change", (event) => {
    loadSchema(event.target.value);
});

elements.refreshButton.addEventListener("click", () => {
    loadModels();
});

elements.form.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!state.schema || !elements.modelSelect.value) {
        setStatus("먼저 모델을 선택하세요.", "error");
        return;
    }

    const requestData = buildRequestData();
    const invalidField = Object.values(requestData).some((value) => value === null);
    if (invalidField) {
        setStatus("모든 입력값을 숫자로 확인해 주세요.", "error");
        return;
    }

    state.loadingSimulation = true;
    setBusy(true);
    setStatus("시뮬레이션을 실행하는 중입니다...", "loading");

    try {
        const modelId = elements.modelSelect.value;
        const data = await fetchJson(`${API_BASE}/models/${encodeURIComponent(modelId)}/simulate`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(requestData)
        });

        renderResults(data);
        setStatus("시뮬레이션이 완료되었습니다.", "success");
    } catch (error) {
        clearResults("결과를 불러오지 못했습니다.");
        setStatus(`시뮬레이션 실패: ${error instanceof Error ? error.message : String(error)}`, "error");
    } finally {
        state.loadingSimulation = false;
        setBusy(false);
        elements.runButton.disabled = !state.schema;
    }
});

loadModels();
