from pathlib import Path
from typing import Any

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_methods=["*"],
    allow_headers=["*"],
)

#uvicorn FrontEnd.webapi.main:app --reload
data: dict[str, Any] = {
    "cash": 1000,
    "workers": 120,
    "sales": 350,
    "profit": 500,
}


@app.get("/data")
def get_data():
    return {"message": "Hello WOrld"}


@app.post("/data")
def set_data(new_data: dict[str, Any]) -> dict[str, Any]:
    data.clear()
    data.update(new_data)
    return data


frontend_dir = Path(__file__).resolve().parents[1] / "main"
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")