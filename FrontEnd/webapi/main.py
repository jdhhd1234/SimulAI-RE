import random
import threading
from contextlib import asynccontextmanager
from pathlib import Path

import lupa
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

import LuaPy.country_mdl as country_mdl
from LuaPy.lua_bridge import LuaBridge

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
    tax_rate: float = 0.12
    resource_power: float = 7.0


companies = [{
    "id": "company-1",
    "name": "Headquarters",
    "country": "South Korea",
    "latitude": 37.5665,
    "longitude": 126.9780,
    "data": data,
}]

AUTO_COMPANIES_TO_ADD = 10
AUTO_CADENCE_SECONDS = 0.1

companies_lock = threading.Lock()
_auto_stop = threading.Event()
_auto_added = 0

# 영토 소유 표시용 색상 팔레트 (company id 해시로 안정 배정)
TERRITORY_COLORS = [
    "#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231",
    "#911eb4", "#46f0f0", "#f032e6", "#bcf60c", "#fabebe",
]


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
        gdp = random.randint(50000, 900000)
        population = random.randint(400000, 3500000)
        tax_rate = round(random.uniform(0.05, 0.18), 4)
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


def _territory_color(company_id):
    index = sum(ord(char) for char in company_id)
    return TERRITORY_COLORS[index % len(TERRITORY_COLORS)]


def _company_power(company):
    latest = company["data"][-1]
    power = latest.get("production", 0)
    return float(power) if isinstance(power, (int, float)) else 0.0


@app.get("/data")
def get_data():
    return data


@app.get("/territories")
def get_territories():
    # 국가별로 가장 강한(production 기준) 자산이 해당 국가 영토를 점유한다.
    owners = {}
    for company in companies:
        country = company["country"]
        power = _company_power(company)
        current = owners.get(country)
        if current is None or power > current["power"]:
            owners[country] = {
                "country": country,
                "company_id": company["id"],
                "company_name": company["name"],
                "power": power,
                "color": _territory_color(company["id"]),
            }
    return list(owners.values())


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


# 2026/09/24: Lua 경제 시뮬레이션 WebUI API (구 lua_api.py 통합).
# Lua는 개인 컴퓨터의 LuaPy/*.lua 파일로 작성하고, 웹은 실행과 결과 표시만 한다.
# 브라우저에서 Lua 코드를 받아 실행하지 않는다(로컬 파일 이름만 받는다).
# 화면: /lua-ui/  (country.lua는 params를 Python이 넣어주는 파일이라 목록에서 뺀다)
LUA_DIR = Path(__file__).resolve().parents[2] / "LuaPy"
LUA_HIDDEN_FILES = ("country.lua",)


def _lua_path(name: str):
    path = (LUA_DIR / name).resolve()
    if path.parent != LUA_DIR or path.suffix != ".lua" or not path.is_file():
        raise HTTPException(status_code=404, detail="Lua file not found")
    return path


@app.get("/lua/files")
def list_lua_files():
    names = []
    for path in sorted(LUA_DIR.glob("*.lua")):
        if path.name not in LUA_HIDDEN_FILES:
            names.append(path.name)
    return names


@app.get("/lua/files/{name}")
def get_lua_source(name: str):
    return {"name": name, "source": _lua_path(name).read_text(encoding="utf-8")}


# 2026/09/24: UI에서 추가한 위치. Lua 실행 때 전역 locations 테이블로 전달된다. (메모리 저장)
class LocationInput(BaseModel):
    name: str = ""
    latitude: float
    longitude: float


locations = []
_location_seq = 0


@app.get("/locations")
def get_locations():
    return locations


@app.post("/locations")
def add_location(location_input: LocationInput):
    global _location_seq
    _location_seq += 1
    location = {
        "id": f"loc-{_location_seq}",
        "name": location_input.name.strip() or f"위치 {_location_seq}",
        "latitude": location_input.latitude,
        "longitude": location_input.longitude,
    }
    locations.append(location)
    return location


@app.delete("/locations/{location_id}")
def delete_location(location_id: str):
    for location in locations:
        if location["id"] == location_id:
            locations.remove(location)
            return location
    raise HTTPException(status_code=404, detail="Location not found")


@app.post("/lua/run/{name}")
def run_lua(
    name: str,
    start: float = 0,
    stop: float = Query(10, le=200),
    dt: float = Query(1, gt=0),
    to_map: bool = False,
):
    path = _lua_path(name)

    try:
        bridge = LuaBridge(start, stop, dt, "web_lua_economy")
        bridge.set_locations(locations)
        bridge.run_file(str(path))
        result = bridge.series()
        records = bridge.map_records() if to_map else []
    except (lupa.LuaError, Exception) as error:
        raise HTTPException(status_code=400, detail=f"{type(error).__name__}: {error}")

    # to_map: Lua 사업장을 지도의 자산(companies)으로 등록한다. 다시 실행하면 이전 Lua 자산을 교체한다.
    company_ids = []
    if to_map:
        with companies_lock:
            companies[:] = [company for company in companies if company.get("source") != "lua"]
        for record in records:
            record["source"] = "lua"
            company_ids.append(_append_company(record)["id"])
    result["company_ids"] = company_ids

    sectors = []
    seen = []
    for establishment in bridge.establishments:
        sector_id = establishment["sector"]
        if sector_id in seen:
            continue
        seen.append(sector_id)
        sectors.append({
            "link": bridge.factory.sector_link(sector_id, bridge.establishments),
            "summary": bridge.factory.sector_summary(sector_id, bridge.establishments),
        })

    result["sectors"] = sectors
    return result


frontend_dir = Path(__file__).resolve().parents[1] / "main"
geomap_dir = Path(__file__).resolve().parents[1] / "geomap"
lua_ui_dir = Path(__file__).resolve().parents[1] / "lua"
app.mount("/geomap", StaticFiles(directory=geomap_dir), name="geomap")
app.mount("/lua-ui", StaticFiles(directory=lua_ui_dir, html=True), name="lua_frontend")
app.mount("/", StaticFiles(directory=frontend_dir, html=True), name="frontend")
