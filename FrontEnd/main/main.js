const status = document.querySelector("#status");
const dataView = document.querySelector("#data");
const rawDataView = document.querySelector("#raw-data");

async function loadData() {
    try {
        const response = await fetch("http://127.0.0.1:8000/data");

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();
        dataView.replaceChildren(
            ...Object.entries(data).map(([key, value]) => {
                const card = document.createElement("article");
                const label = document.createElement("strong");
                const number = document.createElement("span");
                label.textContent = key;
                number.textContent = value;
                card.append(label, number);
                return card;
            }),
        );
        rawDataView.textContent = JSON.stringify(data, null, 2);
        status.textContent = "Connected";
    } catch (error) {
        status.textContent = `Failed to load data: ${error.message}`;
    }
}

loadData();