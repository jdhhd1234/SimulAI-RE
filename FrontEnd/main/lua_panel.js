// 2026/09/24: 위치 추가 + Lua 코드 실행 패널.
// - 지도에서 고른 좌표를 위치로 추가하면 서버가 기억하고, Lua 실행 때 locations 테이블로 넘어간다.
// - Lua를 실행하면 서버가 사업장을 지도 자산으로 등록하고, geo_main.js의 loadCompanies로 다시 그린다.
// (#company-form은 지도 클릭 시 좌표를 채워주는 geo_main.js의 폼 id를 그대로 쓴 "위치 추가" 폼이다.)
const luaForm = document.querySelector("#lua-form");
const luaFileSelect = document.querySelector("#lua-file");
const luaStatus = document.querySelector("#lua-status");
const locationList = document.querySelector("#location-list");

let locationLayer;

async function loadLuaFiles() {
    const response = await fetch("/lua/files");
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }

    const names = await response.json();
    names.forEach((name) => {
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        luaFileSelect.appendChild(option);
    });

    if (!names.length) {
        luaStatus.textContent = "LuaPy 폴더에 .lua 파일이 없습니다.";
    }
}

async function runLua(event) {
    event.preventDefault();
    if (!luaFileSelect.value) {
        return;
    }

    luaStatus.textContent = "실행 중...";
    try {
        const response = await fetch(`/lua/run/${encodeURIComponent(luaFileSelect.value)}?to_map=true`, { method: "POST" });
        const result = await response.json();
        if (!response.ok) {
            throw new Error(typeof result.detail === "string" ? result.detail : JSON.stringify(result.detail));
        }

        luaStatus.textContent = `사업장 ${result.company_ids.length}개를 지도에 표시했습니다.`;
        // 방금 등록된 Lua 자산 중 첫 번째를 선택해 보여준다.
        await loadCompanies(result.company_ids[0], true);
    } catch (error) {
        luaStatus.textContent = `Failed: ${error.message}`;
    }
}

function renderLocations(locations) {
    createMap();

    locationList.replaceChildren();
    locations.forEach((location, index) => {
        const item = document.createElement("div");
        item.className = "company-item";

        const title = document.createElement("strong");
        title.textContent = `${index + 1}. ${location.name}`;
        const coordinates = document.createElement("span");
        coordinates.textContent = `${location.latitude.toFixed(4)}, ${location.longitude.toFixed(4)}`;
        const remove = document.createElement("button");
        remove.type = "button";
        remove.className = "location-remove";
        remove.textContent = "삭제";
        remove.addEventListener("click", () => removeLocation(location.id));

        item.append(title, coordinates, remove);
        locationList.appendChild(item);
    });

    if (typeof map === "undefined" || !map) {
        return;
    }
    locationLayer?.clearLayers();
    locationLayer = locationLayer || L.layerGroup().addTo(map);
    locations.forEach((location, index) => {
        L.circleMarker([location.latitude, location.longitude], {
            radius: 6,
            color: "#4fc3f7",
            weight: 2,
            fillColor: "#4fc3f7",
            fillOpacity: 0.6,
        })
            .bindTooltip(`${index + 1}. ${location.name}`)
            .addTo(locationLayer);
    });
}

async function loadLocations() {
    const response = await fetch("/locations");
    if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
    }
    renderLocations(await response.json());
}

async function addLocation(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const status = document.querySelector("#company-form-status");
    status.textContent = "추가 중...";

    try {
        const response = await fetch("/locations", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: form.elements.name.value,
                latitude: Number(form.elements.latitude.value),
                longitude: Number(form.elements.longitude.value),
            }),
        });
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        form.reset();
        coordinateMarker?.remove();
        coordinateMarker = undefined;
        status.textContent = "위치 추가됨";
        await loadLocations();
    } catch (error) {
        status.textContent = `Failed: ${error.message}`;
    }
}

async function removeLocation(locationId) {
    const response = await fetch(`/locations/${encodeURIComponent(locationId)}`, { method: "DELETE" });
    if (response.ok) {
        await loadLocations();
    }
}

const locationForm = document.querySelector("#company-form");
if (locationForm && locationList) {
    locationForm.addEventListener("submit", addLocation);
    loadLocations().catch((error) => {
        document.querySelector("#company-form-status").textContent = `Failed: ${error.message}`;
    });
}

if (luaForm && luaFileSelect) {
    luaForm.addEventListener("submit", runLua);
    loadLuaFiles().catch((error) => {
        luaStatus.textContent = `Failed: ${error.message}`;
    });
}
