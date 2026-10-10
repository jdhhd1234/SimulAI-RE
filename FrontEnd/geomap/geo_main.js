// 지도(OpenLayers) 로직. main.js와는 아래 함수와 document 이벤트로만 주고받는다.
//   geoSetCompanies(companies), geoSetLocations(locations), geoSetTerritories(territories),
//   geoSetSelected(id), geoPanTo(latitude, longitude)
//   이벤트: "geo-company-click" {id}, "geo-map-click" {latitude, longitude}
let geoTerritories = {};
let geoSelectedId = null;

const map = new ol.Map({
  target: 'map',
  layers: [
    new ol.layer.TileLayer({
      source: new ol.source.OSM(),
    }),
  ],
  view: new ol.View({
    center: [0, 0],
    zoom: 2,
  }),
});

function countryStyle(feature) {
    const owner = geoTerritories[feature.get("name")];
    const selected = owner && owner.company_id === geoSelectedId;
    return new ol.style.Style({
        stroke: new ol.style.Stroke({ color: "#333333", width: 0.6 }),
        fill: new ol.style.Fill({ color: selected ? "#8c8c8c" : owner ? "#3d3d3d" : "#141414" }),
    });
}

function companyStyle(feature) {
    const active = feature.get("company").id === geoSelectedId;
    return new ol.style.Style({
        image: new ol.style.Circle({
            radius: active ? 7 : 4,
            stroke: new ol.style.Stroke({ color: "#ffffff", width: 1 }),
            fill: new ol.style.Fill({ color: active ? "#ffffff" : "#000000" }),
        }),
    });
}

const locationStyle = new ol.style.Style({
    image: new ol.style.Circle({
        radius: 4,
        stroke: new ol.style.Stroke({ color: "#808080", width: 1, lineDash: [2, 2] }),
    }),
});

const countrySource = new ol.source.Vector({ url: "/geomap/countries.geojson", format: new ol.format.GeoJSON() });
const markerSource = new ol.source.Vector();
const locationSource = new ol.source.Vector();
const countryLayer = new ol.layer.Vector({ source: countrySource, style: countryStyle });
const markerLayer = new ol.layer.Vector({ source: markerSource, style: companyStyle });

countrySource.on("featuresloaderror", () => setStatus("지도 로드 실패", true));

// 마우스를 올린 대상 이름 표시
const tooltipEl = document.createElement("div");
tooltipEl.className = "map-tooltip";
tooltipEl.hidden = true;
const tooltip = new ol.Overlay({ element: tooltipEl, positioning: "center-left" });
map.addOverlay(tooltip);

map.on("pointermove", (event) => {
    if (event.dragging) {
        return;
    }
    const feature = map.forEachFeatureAtPixel(event.pixel, (item) => item);
    if (!feature) {
        tooltipEl.hidden = true;
        return;
    }

    let html;
    if (feature.get("company")) {
        html = feature.get("company").name;
    } else if (feature.get("location")) {
        html = feature.get("location").name;
    } else {
        const owner = geoTerritories[feature.get("name")];
        html = owner ? `${feature.get("name")}<br>${owner.company_name}` : feature.get("name");
    }
    tooltipEl.innerHTML = html;
    tooltipEl.hidden = false;
    tooltip.setPosition(event.coordinate);
});

// 자산 마커를 누르면 선택, 그 외 지점을 누르면 좌표 전달
map.on("singleclick", (event) => {
    const feature = map.forEachFeatureAtPixel(event.pixel, (item) => item, {
        layerFilter: (layer) => layer === markerLayer,
    });
    if (feature) {
        document.dispatchEvent(new CustomEvent("geo-company-click", { detail: { id: feature.get("company").id } }));
        return;
    }

    const [longitude, latitude] = ol.proj.toLonLat(event.coordinate);
    const wrapped = ((((longitude + 180) % 360) + 360) % 360) - 180;
    document.dispatchEvent(new CustomEvent("geo-map-click", { detail: { latitude, longitude: wrapped } }));
});

function pointFeature(latitude, longitude, properties) {
    return new ol.Feature({
        geometry: new ol.geom.Point(ol.proj.fromLonLat([longitude, latitude])),
        ...properties,
    });
}

function geoSetCompanies(companies) {
    markerSource.clear();
    companies.forEach((company) => markerSource.addFeature(pointFeature(company.latitude, company.longitude, { company })));
}

function geoSetLocations(locations) {
    locationSource.clear();
    locations.forEach((location) => locationSource.addFeature(pointFeature(location.latitude, location.longitude, { location })));
}

function geoSetTerritories(territories) {
    geoTerritories = territories;
    countryLayer.changed();
}

function geoSetSelected(id) {
    geoSelectedId = id;
    countryLayer.changed();
    markerLayer.changed();
}

function geoPanTo(latitude, longitude) {
    map.getView().animate({ center: ol.proj.fromLonLat([longitude, latitude]), duration: 300 });
}