

const companyList = document.querySelector("#company-list");
const locationList = document.querySelector("#location-list");
const locationForm = document.querySelector("#location-form");
const metricsEl = document.querySelector("#metrics");

let territories = {};
let companies = [];
let selectedId = null;
let chart;

function renderCompanies() {
    companyList.replaceChildren();

    if (!companies.length) {
        companyList.innerHTML = '<li class="empty">자산이 없습니다.</li>';
    }

    companies.forEach((company) => {
        const active = company.id === selectedId;

        const item = document.createElement("li");
        item.classList.toggle("active", active);
        item.innerHTML = `<span>${company.name}<br><small>${company.country} · ${company.id}</small></span>`;
        const remove = document.createElement("button");
        remove.className = "small";
        remove.textContent = "삭제";
        remove.addEventListener("click", (event) => {
            event.stopPropagation();
            deleteCompany(company.id);
        });
        item.appendChild(remove);
        item.addEventListener("click", () => selectCompany(company.id));
        companyList.appendChild(item);
    });
    geoSetCompanies(companies);
}

async function refresh() {
    try {
        const [companyData, territoryData] = await Promise.all([api("/companies"), api("/territories")]);
        const changed = JSON.stringify(companyData.map((c) => c.id)) !== JSON.stringify(companies.map((c) => c.id));
        companies = companyData;
        territories = Object.fromEntries(territoryData.map((t) => [t.country, t]));
        if (changed) {
            renderCompanies();
        }
        geoSetTerritories(territories);
        setStatus(`연결됨 · 자산 ${companies.length}개`);
    } catch (error) {
        setStatus(`연결 실패: ${error.message}`, true);
    }
}

async function selectCompany(id) {
    selectedId = id;
    renderCompanies();
    geoSetSelected(id);

    try {
        const company = await api(`/companies/${encodeURIComponent(id)}`);
        const rows = company.data || [];
        const latest = rows[rows.length - 1] || {};

        document.querySelector("#detail-title").textContent = company.name;
        document.querySelector("#detail-sub").textContent =
            `${company.country} · ${fmt(company.latitude)}, ${fmt(company.longitude)}`;

        metricsEl.hidden = false;
        metricsEl.replaceChildren();
        Object.entries(latest).forEach(([key, value]) => {
            const cell = document.createElement("div");
            cell.innerHTML = `<span>${key}</span><strong>${fmt(value)}</strong>`;
            metricsEl.appendChild(cell);
        });

        const keys = rows.length ? Object.keys(rows[0]).filter((key) => key !== "time" && typeof rows[0][key] === "number") : [];
        const series = Object.fromEntries(keys.map((key) => [key, rows.map((row) => row[key])]));
        chart = renderLineChart(document.querySelector("#chart"), chart, rows.map((row) => row.time), series);
        renderTable(document.querySelector("#table"), rows);

        geoPanTo(company.latitude, company.longitude);
    } catch (error) {
        setStatus(error.message, true);
    }
}

async function deleteCompany(id) {
    try {
        await api(`/companies/${encodeURIComponent(id)}`, { method: "DELETE" });
        if (selectedId === id) {
            selectedId = null;
            geoSetSelected(null);
            chart?.destroy();
            chart = null;
            metricsEl.hidden = true;
            document.querySelector("#detail-title").textContent = "자산 정보";
            document.querySelector("#detail-sub").textContent = "자산을 선택하세요.";
            renderTable(document.querySelector("#table"), []);
        }
        await refresh();
    } catch (error) {
        setStatus(error.message, true);
    }
}

async function loadLocations() {
    const locations = await api("/locations");
    locationList.replaceChildren();

    locations.forEach((location) => {
        const item = document.createElement("li");
        item.innerHTML = `<span>${location.name}<br><small>${fmt(location.latitude)}, ${fmt(location.longitude)}</small></span>`;
        const remove = document.createElement("button");
        remove.className = "small";
        remove.textContent = "삭제";
        remove.addEventListener("click", async (event) => {
            event.stopPropagation();
            await api(`/locations/${encodeURIComponent(location.id)}`, { method: "DELETE" });
            loadLocations();
        });
        item.appendChild(remove);
        item.addEventListener("click", () => geoPanTo(location.latitude, location.longitude));
        locationList.appendChild(item);
    });
    geoSetLocations(locations);
}

document.addEventListener("geo-company-click", (event) => selectCompany(event.detail.id));

document.addEventListener("geo-map-click", (event) => {
    locationForm.latitude.value = event.detail.latitude.toFixed(4);
    locationForm.longitude.value = event.detail.longitude.toFixed(4);
});

locationForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
        await api("/locations", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: locationForm.name.value,
                latitude: Number(locationForm.latitude.value),
                longitude: Number(locationForm.longitude.value),
            }),
        });
        locationForm.reset();
        loadLocations();
    } catch (error) {
        setStatus(error.message, true);
    }
});

loadLocations().catch((error) => setStatus(error.message, true));
refresh();
setInterval(refresh, 3000);
