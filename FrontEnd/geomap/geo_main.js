const mapElement = document.querySelector("#world-map");
const companyForm = document.querySelector("#company-form");
const companyList = document.querySelector("#company-list");
const formStatus = document.querySelector("#company-form-status");
const status = document.querySelector("#status");

let map;
let markerLayer;
let coordinateMarker;
let knownCompanyIds = new Set();

function escapeHtml(value) {
    return String(value ?? "")
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}

function formatValue(value) {
    if (typeof value !== "number") {
        return "--";
    }

    return value.toLocaleString("ko-KR", { maximumFractionDigits: 0 });
}

function updateOverview(point) {
    const metricGrid = document.querySelector(".metric-grid");
    if (metricGrid) {
        metricGrid.innerHTML = Object.entries(point)
            .filter(([key, value]) => key !== "time" && typeof value === "number")
            .map(([key, value]) => `
                <article class="metric-card">
                    <span>${escapeHtml(key)}</span>
                    <strong>${formatValue(value)}</strong>
                </article>
            `).join("");
    }

    const action = document.querySelector("#metric-action");
    if (action) {
        action.textContent = point.ai_action || "--";
    }
}

function createPopup(company) {
    const point = company.latest || {};

    return `
        <div class="map-popup">
            <h3>${escapeHtml(company.name)}</h3>
            <p>${escapeHtml(company.country)}</p>
            ${Object.entries(point)
                .filter(([key, value]) => key !== "time" && typeof value === "number")
                .slice(0, 3)
                .map(([key, value]) => `<p>${escapeHtml(key)}: ${formatValue(value)}</p>`)
                .join("")}
        </div>
    `;
}

function createMap() {
    if (!mapElement || typeof L === "undefined" || map) {
        return;
    }

    map = L.map(mapElement, { worldCopyJump: true }).setView([24, 10], 2);
    markerLayer = L.layerGroup().addTo(map);

    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        attribution: "&copy; OpenStreetMap contributors",
        maxZoom: 18,
    }).addTo(map);

    map.invalidateSize();

    map.on("click", (event) => {
        const latitudeInput = companyForm?.elements.latitude;
        const longitudeInput = companyForm?.elements.longitude;

        if (!latitudeInput || !longitudeInput) {
            return;
        }

        latitudeInput.value = event.latlng.lat.toFixed(4);
        longitudeInput.value = event.latlng.lng.toFixed(4);
        formStatus.textContent = "좌표 선택됨";

        if (coordinateMarker) {
            coordinateMarker.remove();
        }

        coordinateMarker = L.circleMarker(event.latlng, {
            radius: 7,
            color: "#ffffff",
            weight: 2,
            fillColor: "#888888",
            fillOpacity: 0.95,
        })
            .bindTooltip("선택된 위치")
            .addTo(map);
    });
}

function renderCompanies(companies) {
    createMap();

    if (!markerLayer) {
        return;
    }

    markerLayer.clearLayers();
    companies.forEach((company) => {
        L.circleMarker([company.latitude, company.longitude], {
            radius: 8,
            color: "#ffffff",
            weight: 2,
            fillColor: "#666666",
            fillOpacity: 0.9,
        })
            .bindTooltip(createPopup(company), {
                direction: "top",
                className: "company-tooltip",
            })
            .bindPopup(createPopup(company))
            .on("click", () => loadCompanies(company.id, true))
            .addTo(markerLayer);
    });
}

function renderCompanyList(companies, selectedId) {
    if (!companyList) {
        return;
    }

    companyList.innerHTML = companies.map((company) => `
        <div class="company-item${company.id === selectedId ? " selected" : ""}" data-id="${escapeHtml(company.id)}">
            <strong>${escapeHtml(company.name)}</strong>
            <span>${escapeHtml(company.country)}</span>
        </div>
    `).join("");

    companyList.querySelectorAll(".company-item").forEach((item) => {
        item.addEventListener("click", () => loadCompanies(item.dataset.id, true));
    });
}

async function loadCompanyData(companyId, showResults) {
    const response = await fetch(`/companies/${companyId}`);
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    const company = await response.json();
    document.dispatchEvent(new CustomEvent("company-data", {
        detail: {
            data: company.data,
            showResults,
        },
    }));
}

async function loadCompanies(selectedId, showResults = false) {
    try {
        const response = await fetch("/companies");
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const companies = await response.json();
        knownCompanyIds = new Set(companies.map((company) => company.id));
        const selectedCompany = companies.find((company) => company.id === selectedId) || companies[0];
        updateOverview(selectedCompany?.latest || {});
        renderCompanyList(companies, selectedCompany?.id);
        renderCompanies(companies);
        if (selectedCompany) {
            await loadCompanyData(selectedCompany.id, showResults);
        }
        if (status) {
            status.textContent = "연결됨";
        }
    } catch (error) {
        createMap();
        if (status) {
            status.textContent = `Failed to load companies: ${error.message}`;
        }
        console.error("Failed to load companies:", error);
    }
}

async function addCompany(event) {
    event.preventDefault();
    formStatus.textContent = "추가 중...";

    const formData = new FormData(companyForm);
    const company = {
        name: formData.get("name"),
        country: formData.get("country"),
        latitude: Number(formData.get("latitude")),
        longitude: Number(formData.get("longitude")),
    };

    [
        "gdp",
        "population",
        "tax_rate",
        "resource_power",
    ].forEach((field) => {
        company[field] = Number(formData.get(field));
    });

    try {
        const response = await fetch("/companies", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(company),
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || `HTTP ${response.status}`);
        }

        companyForm.reset();
        formStatus.textContent = "자산 추가됨";
        const createdCompany = await response.json();
        await loadCompanies(createdCompany.id, true);
    } catch (error) {
        formStatus.textContent = `Failed: ${error.message}`;
    }
}

if (companyForm) {
    companyForm.addEventListener("submit", addCompany);
}

const infoPanel = document.querySelector(".info-panel");
if (infoPanel) {
    infoPanel.addEventListener("resize", () => {
        if (map) {
            map.invalidateSize();
        }
    });
}

document.addEventListener("map-view-change", (event) => {
    if (event.detail?.view !== "map" || !map) {
        return;
    }

    requestAnimationFrame(() => map.invalidateSize());
});

const AUTO_REFRESH_MS = 3000;
let autoSyncRunning = false;

async function syncCompanies() {
    if (autoSyncRunning) {
        return;
    }
    autoSyncRunning = true;

    try {
        const response = await fetch("/companies");
        if (!response.ok) {
            return;
        }

        const companies = await response.json();
        const currentIds = new Set(companies.map((company) => company.id));
        const added = companies.filter((company) => !knownCompanyIds.has(company.id));
        knownCompanyIds = currentIds;

        if (!added.length) {
            return;
        }

        const newest = companies[companies.length - 1];
        updateOverview(newest.latest || {});
        renderCompanyList(companies, newest.id);
        renderCompanies(companies);
        await loadCompanyData(newest.id, false);
        if (status) {
            status.textContent = `새 자산 자동 등록: ${newest.name}`;
        }
    } catch {
        knownCompanyIds = new Set();
    } finally {
        autoSyncRunning = false;
    }
}

loadCompanies(undefined, true).then(() => {
    setInterval(syncCompanies, AUTO_REFRESH_MS);
});
