from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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

@app.post("/main")
def main(data: dict):
    simulation = bm.BaseModel(
        population=data["population"],
        factories=data["factories"],
        resources=data["resource"]
    )

    return {
        "population": simulation.population,
        "factories": simulation.factories,
        "resources": simulation.resources,
        "total_score": simulation.total_score
    }