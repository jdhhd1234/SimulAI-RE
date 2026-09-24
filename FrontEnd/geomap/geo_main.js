const mapElement = document.querySelector("#world-map");
const companyForm = document.querySelector("#company-form");
const companyList = document.querySelector("#company-list");
const formStatus = document.querySelector("#company-form-status");
const status = document.querySelector("#status");

let map;
let markerLayer;
let countryLayer;
let coordinateMarker;
let knownCompanyIds = new Set();
let countriesLoaded = false;
let territoryOwners = {};

const COUNTRY_ALIASES = {
    "United States": "United States of America",
    "USA": "United States of America",
    "UK": "United Kingdom",
    "Korea": "South Korea",
};

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

function normalizeCountry(name) {
    const key = String(name ?? "").trim();
    return COUNTRY_ALIASES[key] || key;
}

function countryStyle(feature) {
    const owner = territoryOwners[normalizeCountry(feature.properties.name)];
    if (!owner) {
        return {
            color: "#3a3a3a",
            weight: 1,
            fillColor: "#2a2a2a",
            fillOpacity: 0.25,
        };
    }

    return {
        color: "#ffffff",
        weight: 1,
        fillColor: owner.color,
        fillOpacity: 0.75,
    };
}

function bindCountryTooltip(feature, layer) {
    layer.bindTooltip(() => {
        const owner = territoryOwners[normalizeCountry(feature.properties.name)];
        return `
            <div class="map-popup">
                <h3>${escapeHtml(feature.properties.name)}</h3>
                <p>${escapeHtml(owner ? owner.company_name : "미점령")}</p>
            </div>
        `;
    }, {
        sticky: true,
        className: "company-tooltip",
    });
}

async function loadTerritories() {
    try {
        const response = await fetch("/territories");
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const territories = await response.json();
        territoryOwners = {};
        territories.forEach((territory) => {
            territoryOwners[normalizeCountry(territory.country)] = territory;
        });
        countryLayer?.setStyle(countryStyle);
    } catch (error) {
        console.error("Failed to load territories:", error);
    }
}

async function loadCountries() {
    if (!map || countriesLoaded) {
        return;
    }
    countriesLoaded = true;

    try {
        const response = await fetch("/geomap/countries.geojson");
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        countryLayer = L.geoJSON(data, {
            style: countryStyle,
            onEachFeature: bindCountryTooltip,
        }).addTo(map);
        countryLayer.bringToBack();
        await loadTerritories();
    } catch (error) {
        console.error("Failed to load country borders:", error);
    }
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

    loadCountries();

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
    loadTerritories();
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
