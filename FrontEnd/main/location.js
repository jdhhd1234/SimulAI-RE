// 위치 추가 (Lua locations 테이블)
const locationList = document.querySelector("#location-list");
export const locationForm = document.querySelector("#location-form");

export async function loadLocations() {
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
