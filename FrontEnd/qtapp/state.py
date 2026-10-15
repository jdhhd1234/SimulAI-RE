import json
import random
import threading
from pathlib import Path

import LuaPy.country_mdl as country_mdl
from LuaPy.lua_bridge import LuaBridge

# 2026/10/15: WebUI(FastAPI) 대신 Qt 앱이 직접 부르는 상태/로직. (구 FrontEnd/webapi/main.py)
# HTTP 없이 같은 프로세스 안에서 자산/위치/매장지/Lua 실행을 처리한다.

AUTO_COMPANIES_TO_ADD = 10
AUTO_CADENCE_SECONDS = 0.1

# 영토 소유 표시용 색상 팔레트 (company id 해시로 안정 배정)
TERRITORY_COLORS = [
    "#e6194b", "#3cb44b", "#ffe119", "#4363d8", "#f58231",
    "#911eb4", "#46f0f0", "#f032e6", "#bcf60c", "#fabebe",
]

# Lua는 개인 컴퓨터의 LuaPy/*.lua 파일로 작성하고, 앱은 실행과 결과 표시만 한다.
# (country.lua는 params를 Python이 넣어주는 파일이라 목록에서 뺀다)
LUA_DIR = Path(__file__).resolve().parents[2] / "LuaPy"
LUA_HIDDEN_FILES = ("country.lua",)

# 2026/10/12: 광물/에너지 매장지. UI에서 편집하고 deposits.json에 저장한다.
# Lua 실행 때 전역 deposits 테이블로 전달된다. (필드 이름은 api.set_resource 인자와 같다)
#   for _, d in ipairs(deposits) do
#       api.set_resource(d.resource, d.reserve, d.extraction_capacity, d.extraction_cost, d.processing_yield)
#   end
DEPOSITS_PATH = Path(__file__).resolve().parent / "deposits.json"
DEPOSIT_CATEGORIES = ("mineral", "energy")


class AppState:

    def __init__(self):
        self.companies = [{
            "id": "company-1",
            "name": "Headquarters",
            "country": "South Korea",
            "latitude": 37.5665,
            "longitude": 126.9780,
            "data": country_mdl.mainRun(False),
        }]
        self.companies_lock = threading.Lock()
        self._auto_stop = threading.Event()
        self._auto_added = 0

        # UI에서 추가한 위치. Lua 실행 때 전역 locations 테이블로 전달된다. (메모리 저장)
        self.locations = []
        self._location_seq = 0

        self.deposits = self._load_deposits()

    # ---------- 자산(companies) ----------

    def start_auto_companies(self):
        threading.Thread(target=self._auto_generate_companies, daemon=True).start()

    def stop(self):
        self._auto_stop.set()

    def _next_company_id(self):
        numbers = []
        for company in self.companies:
            suffix = company["id"].rsplit("-", 1)[-1]
            if suffix.isdigit():
                numbers.append(int(suffix))
        return f"company-{(max(numbers) + 1) if numbers else len(self.companies) + 1}"

    def _append_company(self, company):
        with self.companies_lock:
            company["id"] = self._next_company_id()
            self.companies.append(company)
        return company

    def _auto_generate_companies(self):
        while self._auto_added < AUTO_COMPANIES_TO_ADD and not self._auto_stop.is_set():
            simulation = country_mdl.CountryEconomic(
                gdp=random.randint(50000, 900000),
                population=random.randint(400000, 3500000),
                tax_rate=round(random.uniform(0.05, 0.18), 4),
                resource_power=random.randint(1, 10),
            )
            try:
                company_data = country_mdl.mainRun(False, company=simulation)
            except Exception as error:
                print(f"[AUTO] 시뮬레이션 실패: {error}")
                self._auto_stop.wait(AUTO_CADENCE_SECONDS)
                continue
            self._append_company({
                "name": f"Auto Company {self._auto_added + 1}",
                "country": "Unknown",
                "latitude": random.uniform(-60, 60),
                "longitude": random.uniform(-180, 180),
                "data": company_data,
                "source": "auto",
            })
            self._auto_added += 1

    def get_companies(self):
        with self.companies_lock:
            return list(self.companies)

    def get_company(self, company_id):
        with self.companies_lock:
            return next((item for item in self.companies if item["id"] == company_id), None)

    def delete_company(self, company_id):
        with self.companies_lock:
            for index, company in enumerate(self.companies):
                if company["id"] == company_id:
                    return self.companies.pop(index)
        return None

    def add_company(self, name, country, latitude, longitude,
                    gdp=100000.0, population=1200000.0, tax_rate=0.12, resource_power=7.0):
        company = country_mdl.CountryEconomic(gdp, population, tax_rate, resource_power)
        return self._append_company({
            "name": name,
            "country": country,
            "latitude": float(latitude),
            "longitude": float(longitude),
            "data": country_mdl.mainRun(False, company=company),
        })

    def get_territories(self):
        """국가별로 가장 강한(production 기준) 자산이 해당 국가 영토를 점유한다. {country: owner}"""
        owners = {}
        for company in self.get_companies():
            country = company["country"]
            power = company["data"][-1].get("production", 0)
            power = float(power) if isinstance(power, (int, float)) else 0.0
            current = owners.get(country)
            if current is None or power > current["power"]:
                owners[country] = {
                    "country": country,
                    "company_id": company["id"],
                    "company_name": company["name"],
                    "power": power,
                    "color": TERRITORY_COLORS[sum(ord(char) for char in company["id"]) % len(TERRITORY_COLORS)],
                }
        return owners

    # ---------- 위치(locations) ----------

    def add_location(self, name, latitude, longitude):
        self._location_seq += 1
        location = {
            "id": f"loc-{self._location_seq}",
            "name": name.strip() or f"위치 {self._location_seq}",
            "latitude": float(latitude),
            "longitude": float(longitude),
        }
        self.locations.append(location)
        return location

    def delete_location(self, location_id):
        self.locations = [location for location in self.locations if location["id"] != location_id]

    # ---------- 매장지(deposits) ----------

    def _load_deposits(self):
        if DEPOSITS_PATH.is_file():
            return json.loads(DEPOSITS_PATH.read_text(encoding="utf-8"))
        return []

    def _save_deposits(self):
        DEPOSITS_PATH.write_text(json.dumps(self.deposits, ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _deposit_record(deposit_id, values):
        record = {
            "name": str(values.get("name", "")).strip(),
            "category": values.get("category", "mineral"),
            "resource": str(values.get("resource", "")).strip(),
            "latitude": float(values["latitude"]),
            "longitude": float(values["longitude"]),
            "reserve": float(values.get("reserve", 0)),
            "extraction_capacity": float(values.get("extraction_capacity", 0)),
            "extraction_cost": float(values.get("extraction_cost", 0)),
            "processing_yield": float(values.get("processing_yield", 1.0)),
        }
        if not record["resource"]:
            raise ValueError("resource is required")
        if record["category"] not in DEPOSIT_CATEGORIES:
            raise ValueError(f"category must be one of {DEPOSIT_CATEGORIES}")
        if not -90 <= record["latitude"] <= 90 or not -180 <= record["longitude"] <= 180:
            raise ValueError("latitude/longitude out of range")
        for key in ("reserve", "extraction_capacity", "extraction_cost", "processing_yield"):
            if record[key] < 0:
                raise ValueError(f"{key} must not be negative")
        record["name"] = record["name"] or f"{record['resource']} {deposit_id}"
        return {"id": deposit_id, **record}

    def add_deposit(self, values):
        numbers = [int(d["id"].rsplit("-", 1)[-1]) for d in self.deposits if d["id"].rsplit("-", 1)[-1].isdigit()]
        deposit = self._deposit_record(f"dep-{max(numbers, default=0) + 1}", values)
        self.deposits.append(deposit)
        self._save_deposits()
        return deposit

    def update_deposit(self, deposit_id, values):
        for index, deposit in enumerate(self.deposits):
            if deposit["id"] == deposit_id:
                self.deposits[index] = self._deposit_record(deposit_id, values)
                self._save_deposits()
                return self.deposits[index]
        raise ValueError("Deposit not found")

    def delete_deposit(self, deposit_id):
        self.deposits = [deposit for deposit in self.deposits if deposit["id"] != deposit_id]
        self._save_deposits()

    # ---------- Lua ----------

    def lua_files(self):
        return [path.name for path in sorted(LUA_DIR.glob("*.lua")) if path.name not in LUA_HIDDEN_FILES]

    def lua_source(self, name):
        return (LUA_DIR / name).read_text(encoding="utf-8")

    def run_lua(self, name, start=0.0, stop=10.0, dt=1.0, to_map=False):
        """
        Lua 파일을 실행한다. 실패하면 (error, console)을 담은 LuaRunError를 던진다.
        to_map: Lua 사업장을 지도의 자산(companies)으로 등록한다. 다시 실행하면 이전 Lua 자산을 교체한다.
        """
        bridge = LuaBridge(start, stop, dt, "qt_lua_economy")
        try:
            bridge.set_locations(self.locations)
            bridge.lua.globals()["deposits"] = bridge.lua.table_from(
                [dict(deposit) for deposit in self.deposits], recursive=True
            )
            bridge.run_file(str(LUA_DIR / name))
            result = bridge.series()
            records = bridge.map_records() if to_map else []
        except Exception as error:
            raise LuaRunError(f"{type(error).__name__}: {error}", bridge.console) from error

        company_ids = []
        if to_map:
            with self.companies_lock:
                self.companies[:] = [company for company in self.companies if company.get("source") != "lua"]
            for record in records:
                record["source"] = "lua"
                company_ids.append(self._append_company(record)["id"])
        result["company_ids"] = company_ids

        result["sectors"] = [
            {"link": bridge.sector_link(sector_id), "summary": bridge.sector_summary(sector_id)}
            for sector_id in bridge.factory.sectors
        ]
        result["console"] = bridge.console
        return result


class LuaRunError(Exception):
    def __init__(self, message, console):
        super().__init__(message)
        self.console = list(console)
