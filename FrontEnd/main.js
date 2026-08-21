const form = document.querySelector("#simulation-form");
const inputFactories = document.querySelector("#input-value-factories");
const inputPopulation = document.querySelector("#input-value-population");
const inputResource = document.querySelector("#input-value-resource");

const status = document.querySelector("#status");
const result = document.querySelector("#result");

form.addEventListener("submit", async (event) => {
    event.preventDefault();

    const requestData = {
        factories: Number(inputFactories.value),
        population: Number(inputPopulation.value),
        resource: Number(inputResource.value)
    };

    status.textContent = "Python API에 요청 중입니다...";
    result.textContent = JSON.stringify(requestData, null, 2);

    try {
        const response = await fetch("http://127.0.0.1:8000/main", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(requestData)
        });

        if (!response.ok) {
            throw new Error("Response Error.");
            
        }

        if (response.ok) {
            const data = await response.json();

            console.log(data);
            result.textContent = JSON.stringify(data, null, 2);
        }

        status.textContent = "시뮬레이션이 완료되었습니다.";
        result.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
        status.textContent = "Python API에 연결하지 못했습니다. 요청 데이터만 표시합니다.";
        result.textContent = JSON.stringify({
            message: "Python API 연결 필요",
            request: requestData,
            error: error.message
        }, null, 2);
    }
});
