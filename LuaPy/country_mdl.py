import json
import os

from LuaPy.lua_bridge import LuaBridge

# 2026/09/24: 삭제된 calc/base/country_mdl을 대체한다. FrontEnd/webapi/main.py가 쓰던
# CountryEconomic / mainRun 호출 형태를 그대로 두고, 계산은 country.lua(새 엔진)가 한다.
COUNTRY_LUA = os.path.join(os.path.dirname(__file__), "country.lua")

# 응답 키 -> 모델 element 이름
COLUMNS = {
    "gdp": "gdp",
    "tax_revenue": "tax_revenue",
    "hire": "hire",
    "labor": "country_0_0_labor",
    "production": "production",
    "sell": "sell",
}


class CountryEconomic:
    def __init__(self, gdp, population, tax_rate, resource_power) -> None:
        self.gdp = gdp
        self.population = population
        self.tax_rate = tax_rate
        self.resource_power = resource_power


def mainRun(Pretty: bool, Integer: bool = True, company=None):
    company = company or CountryEconomic(
        gdp=1000.0,
        population=1200.0,
        tax_rate=0.12,
        resource_power=7.0
    )

    bridge = LuaBridge(0.0, 5.0, 1.0, "CountryModel")
    bridge.lua.globals()["params"] = bridge.lua.table_from({
        "gdp": company.gdp,
        "population": company.population,
        "tax_rate": company.tax_rate,
        "resource_power": company.resource_power,
    })
    bridge.run_file(COUNTRY_LUA)
    result = bridge.series()

    maindata = []
    for i, time in enumerate(result["time"]):
        row = {"time": int(round(time)) if Integer else float(time)}
        for key, name in COLUMNS.items():
            value = result["series"][name][i]
            row[key] = int(round(value)) if Integer else float(value)
        maindata.append(row)

    if Pretty is True:
        return json.dumps(maindata, indent=2, ensure_ascii=False)

    return maindata
