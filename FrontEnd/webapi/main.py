from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import calc.base.country_mdl as country_mdl

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# uvicorn FrontEnd.webapi.main:app --reload
data = country_mdl.mainRun(False)


# 이거를 이렇게 고정으로 하는게 아니라 country_mdl에 나와있는 내용대로
class CompanyInput(BaseModel):
    name: str
    country: str
    latitude: float
    longitude: float
    gdp: float = 100000.0
    population: float = 1200000.0
    tax_rate: float = 12.0
    resource_power: float = 7.0


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


@app.get("/country")
def get_country():
    return country_mdl.mainRun(False)


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
    company = country_mdl.CountryEconomic(
        gdp=company_input.gdp,
        population=company_input.population,
        tax_rate=company_input.tax_rate,
        resource_power=company_input.resource_power,
    )
    company_data = country_mdl.mainRun(False, company=company)
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
