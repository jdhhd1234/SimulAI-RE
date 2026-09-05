from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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


class CompanyInput(BaseModel):
    name: str
    country: str
    latitude: float
    longitude: float
    cash_init: float = 1000.0
    debt_init: float = 1.0
    previous_demand: float = 500.0
    workers: float = 120.0
    workers_wage: float = 2500.0
    production_per_worker: float = 10.0
    origin_price: float = 100.0
    sell_price: float = 1000.0
    deltatime: float = 1.0
    stoptime: float = 12.0


companies = [{
    "id": "company-1",
    "name": "Headquarters",
    "country": "South Korea",
    "latitude": 37.5665,
    "longitude": 126.9780,
    "data": data,
}]


def company_summary(company):
    latest = company["data"][-1]
    return {
        "id": company["id"],
        "name": company["name"],
        "country": company["country"],
        "latitude": company["latitude"],
        "longitude": company["longitude"],
        "latest": latest,
    }


@app.get("/data")
def get_data():
    return data


@app.get("/companies")
def get_companies():
    return [company_summary(company) for company in companies]


@app.get("/companies/{company_id}")
def get_company(company_id: str):
    company = next((item for item in companies if item["id"] == company_id), None)
    if company is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return company


@app.post("/companies")
def add_company(company_input: CompanyInput):
    company = bm.CompanyModel(
        cash_init=company_input.cash_init,
        previous_demand=company_input.previous_demand,
        origin_price=company_input.origin_price,
        sell_price=company_input.sell_price,
        workers=company_input.workers,
        workers_wage=company_input.workers_wage,
        production_per_worker=company_input.production_per_worker,
        deltatime=company_input.deltatime,
        stoptime=company_input.stoptime,
        debt_init=company_input.debt_init,
    )
    company_data = bm.mainRun(False, company=company)
    company_record = {
        "id": f"company-{len(companies) + 1}",
        "name": company_input.name,
        "country": company_input.country,
        "latitude": company_input.latitude,
        "longitude": company_input.longitude,
        "data": company_data,
    }
    companies.append(company_record)
    return company_summary(company_record)


frontend_dir = Path(__file__).resolve().parents[1] / "main"
geomap_dir = Path(__file__).resolve().parents[1] / "geomap"
app.mount("/geomap", StaticFiles(directory=geomap_dir), name="geomap")
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
