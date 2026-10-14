// 지도 화면 진입점: 각 파일을 묶고 지도 이벤트를 연결한다.
//   company.js (자산), location.js (위치), deposit.js (광물/에너지 매장지)
import { refresh, selectCompany } from "./company.js";
import { loadLocations, locationForm } from "./location.js";
import { loadDeposits, editDeposit, depositForm } from "./deposit.js";

document.addEventListener("geo-deposit-click", (event) => editDeposit(event.detail.id));

document.addEventListener("geo-company-click", (event) => selectCompany(event.detail.id));

document.addEventListener("geo-map-click", (event) => {
    locationForm.latitude.value = event.detail.latitude.toFixed(4);
    locationForm.longitude.value = event.detail.longitude.toFixed(4);
    depositForm.latitude.value = event.detail.latitude.toFixed(4);
    depositForm.longitude.value = event.detail.longitude.toFixed(4);
});

loadLocations().catch((error) => setStatus(error.message, true));
loadDeposits().catch((error) => setStatus(error.message, true));
refresh();
setInterval(refresh, 3000);
