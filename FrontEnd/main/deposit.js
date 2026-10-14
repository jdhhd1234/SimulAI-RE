// 2026/10/12: 광물/에너지 매장지 편집
export const depositForm = document.querySelector("#deposit-form");
const depositList = document.querySelector("#deposit-list");
const depositTotals = document.querySelector("#deposit-totals");
const depositFilterCategory = document.querySelector("#deposit-filter-category");
const depositFilterResource = document.querySelector("#deposit-filter-resource");
const DEPOSIT_CATEGORY = { mineral: "광물", energy: "에너지" };
// 자원 입력 추천 목록. 여기 없는 이름도 자유롭게 입력할 수 있다.
const RESOURCE_PRESETS = {
    iron: "mineral", copper: "mineral", chrome: "mineral", nickel: "mineral", lithium: "mineral",
    cobalt: "mineral", rare_earth: "mineral", bauxite: "mineral", gold: "mineral",
    oil: "energy", gas: "energy", coal: "energy", uranium: "energy", carbon: "energy",
};

let deposits = [];
let selectedDepositId = null;

document.querySelector("#resource-names").replaceChildren(...Object.keys(RESOURCE_PRESETS).map((name) => new Option(name)));

function renderDeposits() {
    const resourceNames = [...new Set(deposits.map((deposit) => deposit.resource))].sort();
    const currentResource = depositFilterResource.value;
    depositFilterResource.replaceChildren(new Option("전체", ""), ...resourceNames.map((name) => new Option(name, name)));
    depositFilterResource.value = resourceNames.includes(currentResource) ? currentResource : "";

    const category = depositFilterCategory.value;
    const resource = depositFilterResource.value;
    const visible = deposits.filter((deposit) =>
        (!category || deposit.category === category) && (!resource || deposit.resource === resource));

    depositList.replaceChildren();
    if (!visible.length) {
        depositList.innerHTML = '<li class="empty">매장지가 없습니다.</li>';
    }
    visible.forEach((deposit) => {
        const item = document.createElement("li");
        item.classList.toggle("active", deposit.id === selectedDepositId);
        item.innerHTML = `<span>${deposit.name}<br><small>${DEPOSIT_CATEGORY[deposit.category]} · ${deposit.resource} · ${fmt(deposit.reserve)}</small></span>`;
        const remove = document.createElement("button");
        remove.className = "small";
        remove.textContent = "삭제";
        remove.addEventListener("click", async (event) => {
            event.stopPropagation();
            try {
                await api(`/deposits/${encodeURIComponent(deposit.id)}`, { method: "DELETE" });
                if (selectedDepositId === deposit.id) {
                    resetDepositForm();
                }
                loadDeposits();
            } catch (error) {
                setStatus(error.message, true);
            }
        });
        item.appendChild(remove);
        item.addEventListener("click", () => editDeposit(deposit.id));
        depositList.appendChild(item);
    });

    // 자원별 총 매장량 (현재 필터 기준)
    const totals = {};
    visible.forEach((deposit) => {
        totals[deposit.resource] = (totals[deposit.resource] || 0) + deposit.reserve;
    });
    depositTotals.hidden = !visible.length;
    depositTotals.replaceChildren();
    Object.entries(totals).forEach(([name, total]) => {
        const cell = document.createElement("div");
        cell.innerHTML = `<span>${name} 총 매장량</span><strong>${fmt(total)}</strong>`;
        depositTotals.appendChild(cell);
    });

    geoSetDeposits(visible, selectedDepositId);
}

export async function loadDeposits() {
    deposits = await api("/deposits");
    renderDeposits();
}

export function editDeposit(id) {
    const deposit = deposits.find((item) => item.id === id);
    if (!deposit) {
        return;
    }
    selectedDepositId = id;
    ["name", "category", "resource", "latitude", "longitude", "reserve", "extraction_capacity", "extraction_cost", "processing_yield"]
        .forEach((key) => { depositForm[key].value = deposit[key]; });
    document.querySelector("#deposit-submit").textContent = "수정";
    document.querySelector("#deposit-cancel").hidden = false;
    geoPanTo(deposit.latitude, deposit.longitude);
    renderDeposits();
}

function resetDepositForm() {
    selectedDepositId = null;
    depositForm.reset();
    document.querySelector("#deposit-submit").textContent = "추가";
    document.querySelector("#deposit-cancel").hidden = true;
    renderDeposits();
}

depositForm.addEventListener("submit", async (event) => {
    event.preventDefault();
    const id = selectedDepositId;
    try {
        await api(id ? `/deposits/${encodeURIComponent(id)}` : "/deposits", {
            method: id ? "PUT" : "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: depositForm.name.value,
                category: depositForm.category.value,
                resource: depositForm.resource.value,
                latitude: Number(depositForm.latitude.value),
                longitude: Number(depositForm.longitude.value),
                reserve: Number(depositForm.reserve.value || 0),
                extraction_capacity: Number(depositForm.extraction_capacity.value || 0),
                extraction_cost: Number(depositForm.extraction_cost.value || 0),
                processing_yield: Number(depositForm.processing_yield.value || 0),
            }),
        });
        resetDepositForm();
        await loadDeposits();
    } catch (error) {
        setStatus(error.message, true);
    }
});

// 추천 자원을 고르면 분류를 자동으로 맞춘다
depositForm.resource.addEventListener("change", () => {
    const category = RESOURCE_PRESETS[depositForm.resource.value.trim()];
    if (category) {
        depositForm.category.value = category;
    }
});

document.querySelector("#deposit-cancel").addEventListener("click", resetDepositForm);
depositFilterCategory.addEventListener("change", renderDeposits);
depositFilterResource.addEventListener("change", renderDeposits);
