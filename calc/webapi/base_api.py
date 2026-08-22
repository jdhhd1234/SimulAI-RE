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

    resource: float = Field(..., ge=0)
    product_price: float = Field(..., ge=0)
    population: float = Field(..., ge=0)
    buy_expense: float = Field(..., gt=0)


def _configure_model(model, data: SimulationRequest) -> None:
    """Apply API input and defaults without changing the base model."""
    # Stock initial values
    model.stocks["cash"].initial_value = 1000.0
    model.stocks["raw_material"].initial_value = data.resource
    model.stocks["products"].initial_value = 0.0
    model.stocks["profit"].initial_value = 0.0

    # Constant values
    model.constants["population"].equation = data.population
    model.constants["consumption_per_person"].equation = 0.2
    model.constants["buy_price"].equation = data.buy_expense
    model.constants["sell_price"].equation = data.product_price
    model.constants["raw_per_product"].equation = 1.0
    model.constants["production_capacity"].equation = 20.0


def _simulation_results(model) -> list[dict[str, float]]:
    """Evaluate the model at every configured simulation step."""
    results = []
    steps = int(round((model.stoptime - model.starttime) / model.dt))

    for step in range(steps + 1):
        time = round(model.starttime + step * model.dt, 10)
        results.append(
            {
                "time": time,
                "cash": float(model.evaluate_equation("cash", time)),
                "raw_material": float(
                    model.evaluate_equation("raw_material", time)
                ),
                "products": float(model.evaluate_equation("products", time)),
                "profit": float(model.evaluate_equation("profit", time)),
                "demand": float(model.evaluate_equation("demand", time)),
                "production": float(
                    model.evaluate_equation("production", time)
                ),
                "sales": float(model.evaluate_equation("sales", time)),
            }
        )

    return results


@app.post("/main")
def main(data: SimulationRequest):
    init = bm.InitValue(
        resource=data.resource,
        product_price=data.product_price,
        population=data.population,
        buy_expense=data.buy_expense,
    )
    model = bm.TestBPTK(init)
    _configure_model(model, data)

    return {
        "model": model.name,
        "starttime": model.starttime,
        "stoptime": model.stoptime,
        "dt": model.dt,
        "results": _simulation_results(model),
    }
