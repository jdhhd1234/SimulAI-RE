from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

import calc.basic_model.base_mode as bm

#uvicorn calc.webapi.base_api:app --reload
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/check")
def check():
    return {"message": "Python API 응답 성공!"}


class SimulationRequest(BaseModel):
    """Values supplied by the frontend for one simulation run."""
    cash_init: float = Field(..., ge=0)
    debt_init: float = Field(..., ge=0)
    sell_price: float = Field(..., gt=0)
    deltatime: float = Field(..., gt=0)
    stoptime: float = Field(..., gt=0)


def _simulation_results(model) -> list[dict[str, float]]:
    """Evaluate the model at every configured simulation step."""
    results = []
    steps = int(round((model.stoptime - model.starttime) / model.dt))

    for step in range(steps):
        time = round(model.starttime + step * model.dt, 10)
        results.append(
            {
                "time": time,
                "cash": float(model.evaluate_equation("cash", time)),
                "debt": float(model.evaluate_equation("debt", time)),
                "deltatime": model.dt,
                "sell_price": float(
                    model.evaluate_equation("sell_price", time)
                ),
                "product_count": float(
                    model.evaluate_equation("product_count", time)
                ),
                "final_profit": float(
                    model.evaluate_equation("final_profit", time)
                ),
            }
        )

    return results


@app.post("/main")
def main(data: SimulationRequest):
    init = bm.InitValue(
        cash_init=data.cash_init,
        debt_init=data.debt_init,
        sell_price=data.sell_price,
        deltatime=data.deltatime,
        stoptime=data.stoptime
    )
    model = init.CompanyModelTest()

    return {
        "model": model.name,
        "starttime": model.starttime,
        "stoptime": model.stoptime,
        "results": _simulation_results(model),
    }