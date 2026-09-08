import random
import threading
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import calc.base.country_mdl as country_mdl

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


# country_mdl -> API -> FrontEnd 자동 등록 피드
# country_mdl은 수정하지 않고, 여기서만 주기적으로 mainRun을 호출한다.
AUTO_SCENARIOS = [
    ("East Bloc Command", "Russia", 55.7558, 37.6173),
    ("Pacific Front", "Japan", 35.6762, 139.6503),
    ("Ironworks Alliance", "Germany", 52.5200, 13.4050),
    ("Atlantic Sentinel", "United States", 40.7128, -74.0060),
    ("Sahara Vanguard", "Egypt", 30.0444, 31.2357),
    ("Amazon Front", "Brazil", -15.8267, -47.9218),
    ("Himalaya Corps", "India", 28.6139, 77.2090),
    ("Cape Defense", "South Africa", -33.9249, 18.4241),
    ("Down Under Outpost", "Australia", -33.8688, 151.2093),
    ("Bering Watch", "Canada", 45.4215, -75.6972),
]
AUTO_COMPANIES_TO_ADD = 10
AUTO_CADENCE_SECONDS = 5.0

companies_lock = threading.Lock()
_auto_stop = threading.Event()
_auto_added = 0


def _next_company_id():
    numbers = []
    for company in companies:
        suffix = company["id"].rsplit("-", 1)[-1]
        if suffix.isdigit():
            numbers.append(int(suffix))
    return f"company-{(max(numbers) + 1) if numbers else len(companies) + 1}"


def _append_company(company):
    with companies_lock:
        company["id"] = _next_company_id()
        companies.append(company)
    return company


def _auto_generate_companies():
    global _auto_added
    while _auto_added < AUTO_COMPANIES_TO_ADD and not _auto_stop.is_set():
        scenario = AUTO_SCENARIOS[_auto_added % len(AUTO_SCENARIOS)]
        name, country, latitude, longitude = scenario
        gdp = random.randint(50000, 900000)
        population = random.randint(400000, 3500000)
        tax_rate = round(random.uniform(5.0, 18.0), 2)
        resource_power = random.randint(1, 10)

        try:
            simulation = country_mdl.CountryEconomic(
                gdp=gdp,
                population=population,
                tax_rate=tax_rate,
                resource_power=resource_power,
            )
            company_data = country_mdl.mainRun(False, company=simulation)
        except Exception as error:
            print(f"[AUTO] 시뮬레이션 실패: {error}")
            _auto_stop.wait(AUTO_CADENCE_SECONDS)
            continue

        company = _append_company({
            "name": name,
            "country": country,
            "latitude": latitude,
            "longitude": longitude,
            "data": company_data,
        })
        _auto_added += 1
        print(f"[AUTO] 자산 자동 등록: {company['name']} ({company['id']})")
        _auto_stop.wait(AUTO_CADENCE_SECONDS)


@asynccontextmanager
async def lifespan(_app):
    auto_thread = threading.Thread(target=_auto_generate_companies, daemon=True)
    auto_thread.start()
    yield
    _auto_stop.set()


app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500"],
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    company_record = _append_company({
        "name": company_input.name,
        "country": company_input.country,
        "latitude": company_input.latitude,
        "longitude": company_input.longitude,
        "data": company_data,
    })
    return company_summary(company_record)


frontend_dir = Path(__file__).resolve().parents[1] / "main"
geomap_dir = Path(__file__).resolve().parents[1] / "geomap"
app.mount("/geomap", StaticFiles(directory=geomap_dir), name="geomap")
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
