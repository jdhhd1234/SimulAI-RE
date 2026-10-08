const storageKey = 'simulai-world-editor-v1';
const ui = Object.fromEntries([...document.querySelectorAll('[id]')].map(element => [element.id, element]));
let scenario;
let selectedId = null;
let countryLayer;
let borderLayer = null;
let drawing = false;
let dirty = false;
const map = L.map('editor-map').setView([25, 15], 2);
L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '&copy; OpenStreetMap contributors', maxZoom: 18,
}).addTo(map);
const drawControl = new L.Control.Draw({
    draw: { polygon: { allowIntersection: false, shapeOptions: { color: '#c4d78b' } },
        polyline: false, rectangle: false, circle: false, marker: false, circlemarker: false },
    edit: false,
});

function status(message) {
    ui['editor-status'].textContent = message;
}

function validateScenario(value) {
    if (!value || value.version !== 1 || !Array.isArray(value.nations) ||
        value.map?.type !== 'FeatureCollection' || !Array.isArray(value.map.features)) {
        throw new Error('올바른 에디터 설정 JSON 또는 GeoJSON이 아닙니다.');
    }
    const nationIds = new Set();
    for (const nation of value.nations) {
        if (!nation || typeof nation.id !== 'string' || !nation.id || nationIds.has(nation.id) ||
            typeof nation.name !== 'string' || !nation.name.trim() || !/^#[0-9a-f]{6}$/i.test(nation.color)) {
            throw new Error('국가 이름, ID 또는 색상 형식이 올바르지 않습니다.');
        }
        nationIds.add(nation.id);
    }
    const ids = new Set();
    for (const feature of value.map.features) {
        const properties = feature?.properties;
        const geometry = feature?.geometry;
        if (feature?.type !== 'Feature' || !properties || typeof properties.editorId !== 'string' ||
            !properties.editorId || ids.has(properties.editorId) || typeof properties.name !== 'string' ||
            !properties.name.trim() || !['Polygon', 'MultiPolygon'].includes(geometry?.type) ||
            (properties.nationId !== null && !nationIds.has(properties.nationId))) {
            throw new Error('영토 이름, ID, 국가 배정 또는 도형 형식이 올바르지 않습니다.');
        }
        const polygons = geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.coordinates;
        if (!Array.isArray(polygons) || !polygons.length) throw new Error('빈 도형은 사용할 수 없습니다.');
        for (const polygon of polygons) {
            if (!Array.isArray(polygon) || !polygon.length) throw new Error('잘못된 Polygon입니다.');
            for (const ring of polygon) {
                if (!Array.isArray(ring) || ring.length < 4 || ring.some(point =>
                    !Array.isArray(point) || point.length < 2 || !Number.isFinite(point[0]) ||
                    !Number.isFinite(point[1]) || Math.abs(point[0]) > 180 || Math.abs(point[1]) > 90) ||
                    ring[0][0] !== ring[ring.length - 1][0] || ring[0][1] !== ring[ring.length - 1][1]) {
                    throw new Error('경계는 닫힌 좌표 배열이어야 하며 경도/위도 범위가 유효해야 합니다.');
                }
            }
        }
        ids.add(properties.editorId);
    }
    return value;
}

function fromGeoJSON(geojson) {
    if (geojson?.type !== 'FeatureCollection' || !Array.isArray(geojson.features)) {
        throw new Error('Polygon 또는 MultiPolygon으로 구성된 FeatureCollection이 필요합니다.');
    }
    const value = { version: 1, nations: [], map: structuredClone(geojson) };
    value.map.features.forEach((feature, index) => {
        feature.properties = { ...feature.properties, editorId: `territory-${index}`,
            name: feature.properties?.name || `영토 ${index + 1}`, nationId: null };
    });
    return validateScenario(value);
}

function selectedFeature() {
    return scenario.map.features.find(feature => feature.properties.editorId === selectedId);
}

function finishBorder() {
    if (!borderLayer) return;
    const feature = selectedFeature();
    const geometry = borderLayer.toGeoJSON().geometry;
    try {
        validateScenario({ ...scenario, map: { type: 'FeatureCollection', features: [{ ...feature, geometry }] } });
    } catch (error) {
        status(error.message);
        return false;
    }
    feature.geometry = geometry;
    borderLayer.editing.disable();
    borderLayer = null;
    dirty = true;
    return true;
}

function render() {
    const nationId = ui.nation.value;
    ui.nation.replaceChildren(new Option('국가 선택', ''));
    scenario.nations.forEach(nation => ui.nation.add(new Option(nation.name, nation.id)));
    ui.nation.value = scenario.nations.some(nation => nation.id === nationId) ? nationId : '';
    const nation = scenario.nations.find(item => item.id === ui.nation.value);
    ui['nation-name'].value = nation?.name || '';
    ui['nation-color'].value = nation?.color || '#77ae78';
    ui['nation-update'].disabled = !nation;
    ui['nation-delete'].disabled = !nation;
    if (countryLayer) map.removeLayer(countryLayer);
    countryLayer = L.geoJSON(scenario.map, {
        style: feature => {
            const owner = scenario.nations.find(item => item.id === feature.properties.nationId);
            const selected = feature.properties.editorId === selectedId;
            return { color: selected ? '#f5e8a3' : '#8c9b87', weight: selected ? 3 : 1,
                fillColor: owner?.color || '#53615a', fillOpacity: owner ? .65 : .25 };
        },
        onEachFeature: (feature, layer) => {
            const owner = scenario.nations.find(item => item.id === feature.properties.nationId);
            const tooltip = document.createElement('span');
            tooltip.textContent = `${feature.properties.name} / ${owner?.name || '미배정'}`;
            layer.bindTooltip(tooltip);
            layer.on('click', () => {
                if (drawing || borderLayer) return;
                selectedId = feature.properties.editorId;
                render();
            });
        },
    }).addTo(map);
    const feature = selectedFeature();
    const owner = scenario.nations.find(item => item.id === feature?.properties.nationId);
    ui.selection.textContent = feature ? `${feature.properties.name} / ${owner?.name || '미배정'}` : '지도에서 영토를 선택하세요.';
    ui['territory-name'].value = feature?.properties.name || '';
    for (const id of ['territory-name', 'territory-update', 'unassign', 'territory-delete']) ui[id].disabled = !feature;
    ui.assign.disabled = !feature || !nation;
    ui['border-edit'].disabled = !feature || feature.geometry.type !== 'Polygon' || feature.geometry.coordinates.length !== 1;
    ui['border-edit'].textContent = '경계 편집';
    ui.counts.textContent = `국가 ${scenario.nations.length} / 영토 ${scenario.map.features.length} / 배정 ${scenario.map.features.filter(item => item.properties.nationId).length}`;
}

function changed(message) {
    dirty = true;
    render();
    status(`${message} 저장 버튼으로 변경사항을 보관하세요.`);
}

ui.nation.addEventListener('change', () => { if (finishBorder() !== false) render(); });
ui['nation-add'].addEventListener('click', () => {
    if (!ui['nation-name'].reportValidity() || !ui['nation-name'].value.trim() || finishBorder() === false) return;
    const nation = { id: crypto.randomUUID(), name: ui['nation-name'].value.trim(), color: ui['nation-color'].value };
    scenario.nations.push(nation);
    ui.nation.add(new Option(nation.name, nation.id));
    ui.nation.value = nation.id;
    changed('국가를 생성했습니다.');
});
ui['nation-form'].addEventListener('submit', event => {
    event.preventDefault();
    if (finishBorder() === false) return;
    const nation = scenario.nations.find(item => item.id === ui.nation.value);
    if (!nation || !ui['nation-name'].value.trim()) return;
    nation.name = ui['nation-name'].value.trim();
    nation.color = ui['nation-color'].value;
    changed('국가 설정을 변경했습니다.');
});
ui['nation-delete'].addEventListener('click', () => {
    if (!confirm('이 국가를 삭제하고 소속 영토를 미배정 상태로 바꿀까요?') || finishBorder() === false) return;
    const id = ui.nation.value;
    scenario.nations = scenario.nations.filter(nation => nation.id !== id);
    scenario.map.features.forEach(feature => { if (feature.properties.nationId === id) feature.properties.nationId = null; });
    changed('국가를 삭제했습니다.');
});
ui['territory-form'].addEventListener('submit', event => {
    event.preventDefault();
    if (!ui['territory-name'].value.trim() || finishBorder() === false) return;
    selectedFeature().properties.name = ui['territory-name'].value.trim();
    changed('영토 이름을 변경했습니다.');
});
for (const id of ['assign', 'unassign']) ui[id].addEventListener('click', () => {
    if (finishBorder() === false) return;
    selectedFeature().properties.nationId = id === 'assign' ? ui.nation.value : null;
    changed(id === 'assign' ? '영토를 배정했습니다.' : '배정을 해제했습니다.');
});
ui['territory-delete'].addEventListener('click', () => {
    if (!confirm('선택한 영토를 지도에서 삭제할까요?') || finishBorder() === false) return;
    scenario.map.features = scenario.map.features.filter(feature => feature.properties.editorId !== selectedId);
    selectedId = null;
    changed('영토를 삭제했습니다.');
});
ui['border-edit'].addEventListener('click', () => {
    if (borderLayer) {
        if (finishBorder() !== false) changed('경계를 변경했습니다.');
        return;
    }
    countryLayer.eachLayer(layer => { if (layer.feature.properties.editorId === selectedId) borderLayer = layer; });
    borderLayer.editing.enable();
    ui['border-edit'].textContent = '경계 적용';
    status('경계의 꼭짓점을 드래그한 뒤 경계 적용을 누르세요.');
});
map.on('draw:drawstart', () => {
    drawing = true;
    if (borderLayer) {
        borderLayer.editing.disable();
        borderLayer = null;
        render();
        status('진행 중이던 경계 편집을 취소하고 새 영토를 그립니다.');
    }
});
map.on('draw:drawstop', () => { drawing = false; });
map.on('draw:created', event => {
    const feature = event.layer.toGeoJSON();
    feature.properties = { editorId: crypto.randomUUID(), name: '새 영토', nationId: ui.nation.value || null };
    try {
        validateScenario({ ...scenario, map: { type: 'FeatureCollection', features: [feature] } });
        scenario.map.features.push(feature);
        selectedId = feature.properties.editorId;
        changed('새 영토를 추가했습니다.');
    } catch (error) { status(error.message); }
});
ui.save.addEventListener('click', () => {
    if (finishBorder() === false) return;
    try {
        localStorage.setItem(storageKey, JSON.stringify(scenario));
        dirty = false;
        render();
        status('현재 브라우저에 저장했습니다. 다음 방문 시 자동으로 불러옵니다.');
    } catch (error) { status(`저장 실패: ${error.message}. JSON 내보내기를 사용하세요.`); }
});
ui.export.addEventListener('click', () => {
    if (finishBorder() === false) return;
    render();
    const url = URL.createObjectURL(new Blob([JSON.stringify(scenario, null, 2)], { type: 'application/json' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'simulai-world.json';
    link.click();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    status('국가 설정과 지도 경계를 JSON으로 내보냈습니다.');
});
for (const id of ['import', 'map-import']) ui[id].addEventListener('change', async event => {
    const file = event.target.files[0];
    if (!file) return;
    try {
        const value = JSON.parse(await file.text());
        const next = id === 'import' ? validateScenario(value) : fromGeoJSON(value);
        if (!confirm('현재 국가 설정과 지도를 불러온 파일로 교체할까요?')) return;
        if (borderLayer) borderLayer.editing.disable();
        borderLayer = null;
        scenario = next;
        selectedId = null;
        changed('파일을 불러왔습니다.');
        if (countryLayer.getBounds().isValid()) map.fitBounds(countryLayer.getBounds());
    } catch (error) { status(`불러오기 실패: ${error.message}`); }
    finally { event.target.value = ''; }
});
ui.reset.addEventListener('click', async () => {
    if (!confirm('모든 국가 설정과 편집 내용을 지우고 기본 지도로 돌아갈까요?')) return;
    try {
        const response = await fetch('/geomap/countries.geojson');
        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        const next = fromGeoJSON(await response.json());
        if (borderLayer) borderLayer.editing.disable();
        borderLayer = null;
        scenario = next;
        selectedId = null;
        changed('기본 지도로 초기화했습니다.');
        map.setView([25, 15], 2);
    } catch (error) { status(`초기화 실패: ${error.message}`); }
});
window.addEventListener('beforeunload', event => {
    if (dirty || borderLayer) { event.preventDefault(); event.returnValue = ''; }
});

async function initialize() {
    try {
        let saved = null;
        let warning = '';
        try {
            const raw = localStorage.getItem(storageKey);
            if (raw) saved = validateScenario(JSON.parse(raw));
        } catch (error) { warning = '저장된 설정을 읽지 못해 기본 지도를 표시합니다. '; }
        if (saved) scenario = saved;
        else {
            const response = await fetch('/geomap/countries.geojson');
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            scenario = fromGeoJSON(await response.json());
        }
        for (const id of ['save', 'export', 'nation', 'nation-name', 'nation-color', 'nation-add', 'import', 'map-import', 'reset']) ui[id].disabled = false;
        map.addControl(drawControl);
        render();
        status(warning + (saved ? '저장된 지도 설정을 불러왔습니다.' : '국가를 생성하거나 지도에서 영토를 선택하세요.'));
    } catch (error) { status(`지도를 불러오지 못했습니다: ${error.message}. 서버 연결을 확인하고 새로고침하세요.`); }
}
initialize();
