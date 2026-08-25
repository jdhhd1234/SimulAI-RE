from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

import calc.basic_model.base_mode as bm

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_methods=["*"],
    allow_headers=["*"],
)

#uvicorn FrontEnd.webapi.main:app --reload
data = bm.mainRun(False)


@app.get("/data")
def get_data():
    return data


frontend_dir = Path(__file__).resolve().parents[1] / "main"
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")