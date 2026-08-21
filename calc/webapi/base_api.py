from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import calc.basic_model.base_mode as bm

#uvicorn calc.webapi.base_api:app --reload
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SimulationInput(BaseModel):
    population_initial_value: float
    capital_initial_value: float
    birth_rate_equation: float
    death_rate_equation: float
    labor_participation_equation: float
    labor_productivity_equation: float
    capital_productivity_equation: float
    saving_rate_equation: float
    depreciation_rate_equation: float


@app.post("/check")
def check():
    return {"message": "Python API 응답 성공!"}


@app.post("/main")
def main(data: SimulationInput):
    pass