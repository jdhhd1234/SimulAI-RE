// 지도(OpenLayers) 로직. main.js와는 아래 함수와 document 이벤트로만 주고받는다.
//   geoSetCompanies(companies), geoSetLocations(locations), geoSetTerritories(territories),
//   geoSetSelected(id), geoPanTo(latitude, longitude)
//   이벤트: "geo-company-click" {id}, "geo-map-click" {latitude, longitude}
import * as maplibregl from 'https://unpkg.com/maplibre-gl@6.13.0/dist/maplibre-gl.mjs';

const getlatitude = document.querySelector('input[name="latitude"]');
const getlongitude = document.querySelector('input[name="longitude"]');

const map = new maplibregl.Map({
    container: 'map', // container id
    style: 'https://demotiles.maplibre.org/style.json', // style URL
    center: [0, 0], // starting position [lng, lat]
    zoom: 1, // starting zoom
    maplibreLogo: true
});


let geoTerritories = {};
let geoSelectedId = null;
let geoCompanyMarkers = [];
let geoLocationMarkers = [];
const hoverPopup = new maplibregl.Popup({ closeButton: false, closeOnClick: false, offset: 12 });

map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

// 영토 색상: 자산이 점유한 국가는 밝게, 선택된 자산의 영토는 더 밝게
function geoCountryColor() {
    const pairs = [];
    Object.entries(geoTerritories).forEach(([country, owner]) => {
        pairs.push(country, owner.company_id === geoSelectedId ? "#8c8c8c" : "#3d3d3d");
    });
    return pairs.length ? ["match", ["get", "name"], ...pairs, "#141414"] : "#141414";
}

function geoRefreshCountries() {
    if (map.getLayer("countries-fill")) {
        map.setPaintProperty("countries-fill", "fill-color", geoCountryColor());
    }
}

map.on("load", () => {
    map.addSource("countries", { type: "geojson", data: "/geomap/countries.geojson" });
    map.addLayer({ id: "countries-fill", type: "fill", source: "countries", paint: { "fill-color": geoCountryColor() } });
    map.addLayer({ id: "countries-line", type: "line", source: "countries", paint: { "line-color": "#333333", "line-width": 0.6 } });

    // 마우스를 올린 국가 이름 표시 (점유 중이면 자산 이름 포함)
    map.on("mousemove", "countries-fill", (event) => {
        const name = event.features[0].properties.name;
        const owner = geoTerritories[name];
        hoverPopup.setLngLat(event.lngLat).setText(owner ? `${name} · ${owner.company_name}` : name).addTo(map);
    });
    map.on("mouseleave", "countries-fill", () => hoverPopup.remove());
    geoRefreshCountries();
});

map.on("error", (event) => {
    if (event.sourceId === "countries") {
        setStatus("지도 로드 실패", true);
    }
});

// 마커를 누르면 자산 선택(geo-company-click), 그 외 지점을 누르면 좌표 전달(geo-map-click)
map.on("click", (event) => {
    if (event.originalEvent.target.closest(".geo-marker")) {
        return;
    }
    const { lat, lng } = event.lngLat.wrap();
    document.dispatchEvent(new CustomEvent("geo-map-click", { detail: { latitude: lat, longitude: lng } }));
});

function geoSetCompanies(companies) {
    geoCompanyMarkers.forEach((marker) => marker.remove());
    geoCompanyMarkers = companies.map((company) => {
        const el = document.createElement("div");
        el.className = "geo-marker company-marker";
        el.dataset.id = company.id;
        el.title = company.name;
        el.classList.toggle("active", company.id === geoSelectedId);
        el.addEventListener("click", () => {
            document.dispatchEvent(new CustomEvent("geo-company-click", { detail: { id: company.id } }));
        });
        return new maplibregl.Marker({ element: el }).setLngLat([company.longitude, company.latitude]).addTo(map);
    });
}

function geoSetLocations(locations) {
    geoLocationMarkers.forEach((marker) => marker.remove());
    geoLocationMarkers = locations.map((location) => {
        const el = document.createElement("div");
        el.className = "geo-marker location-marker";
        el.title = location.name;
        return new maplibregl.Marker({ element: el }).setLngLat([location.longitude, location.latitude]).addTo(map);
    });
}

function geoSetTerritories(territories) {
    geoTerritories = territories;
    geoRefreshCountries();
}

function geoSetSelected(id) {
    geoSelectedId = id;
    geoCompanyMarkers.forEach((marker) => {
        const el = marker.getElement();
        el.classList.toggle("active", el.dataset.id === geoSelectedId);
    });
    geoRefreshCountries();
}

function geoPanTo(latitude, longitude) {
    map.easeTo({ center: [longitude, latitude], duration: 300 });
}

// main.js(일반 모듈)에서 호출할 수 있도록 전역에 노출
Object.assign(window, { geoSetCompanies, geoSetLocations, geoSetTerritories, geoSetSelected, geoPanTo });

/** 
 * 
 * let marker = new Marker()
  .setLngLat([30.5, 50.5])
  .addTo(map);
*/