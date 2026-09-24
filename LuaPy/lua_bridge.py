import os
import sys

import lupa

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "calc"))

import dynamics_system.dynamic_main as dm
import dynamics_system.dynamic_sector as ds


class LuaBridge:
    """
    2026/09/24: Python(BPTK-Py) <-> Lua(lupa) 연동.
    Lua는 api.* 로 sector/establishment를 정의하고, equation은 Lua 함수(function(t) ... end)로 넘긴다.
    Lua 함수 안에서는 get(name, t)로 다른 stock/converter의 값을 읽는다.
    """

    def __init__(self, start_time, stop_time, dt, name: str):
        self.model = dm.ModelSystemDynamics(start_time, stop_time, dt, name).system_dynamics_makeModel_func()
        self.model.lua_fn = {}  # BPTK equation 문자열이 model.lua_fn[key](t)로 Lua 함수를 부른다.
        self.factory = ds.SystemDynamicMakeSector()
        self.sd = dm.SystemDynamics()
        self.establishments = []
        self.recipes = {}
        self.info = {}

        self.lua = lupa.LuaRuntime(unpack_returned_tuples=False)
        self.lua.globals()["api"] = self
        self.lua.globals()["get"] = lambda name, t: self.model.memoize(name, t)
        self.set_locations([])

    def _key(self, fn):
        key = f"lua_{len(self.model.lua_fn)}"
        self.model.lua_fn[key] = lambda t: float(fn(t))
        return key

    def _converter_eq(self, eq):
        """Lua 함수면 BPTK converter가 받는 문자열 equation으로 바꾼다. 숫자/None은 그대로."""
        if lupa.lua_type(eq) == "function":
            return f"model.lua_fn['{self._key(eq)}'](t)"
        return eq

    def _stock_eq(self, eq):
        """stock은 숫자/Element만 받는다. Lua 함수면 변화율 converter를 만들어 그 Element를 넘긴다."""
        if lupa.lua_type(eq) == "function":
            key = self._key(eq)
            return self.sd.system_dynamics_converter_func(
                self.model, f"{key}_rate", f"model.lua_fn['{key}'](t)"
            )
        return 0 if eq is None else eq

    def make_sector(self, id, name):
        return self.factory.make_sector(id, name)["id"]

    def make_good(self, id, unit):
        return self.factory.make_good(id, unit)["id"]

    def set_recipe(self, output_good, inputs, labor, capacity):
        # Lua table -> dict
        inputs = dict(inputs.items()) if inputs else {}
        self.recipes[output_good] = self.factory.set_recipe(output_good, inputs, labor, capacity)
        return output_good

    def make_establishment(self, sector, x, y, recipe, capital=0.0,
                           capital_eq=None, labor_eq=None, capacity_eq=None):
        establishment = self.factory.make_establishment(
            self.model, sector, (x, y), self.recipes[recipe], capital,
            self._stock_eq(capital_eq),
            self._stock_eq(labor_eq),
            self._converter_eq(capacity_eq),
        )
        self.establishments.append(establishment)
        return f"{sector}_{x}_{y}"

    def set_locations(self, locations):
        """
        2026/09/24: UI에서 추가한 위치를 Lua 전역 locations 테이블(1부터 시작)로 넘긴다.
        Lua: locations[1].name, locations[1].lat, locations[1].lon
        """
        items = []
        for location in locations:
            items.append({
                "id": location["id"],
                "name": location["name"],
                "lat": location["latitude"],
                "lon": location["longitude"],
            })
        self.lua.globals()["locations"] = self.lua.table_from(items, recursive=True)

    def describe(self, establishment_id, name, country=""):
        """2026/09/24: 지도에 보일 이름/국가. location(x, y)는 지도의 (위도, 경도)로 쓴다."""
        self.info[establishment_id] = {"name": name, "country": country}

    def make_converter(self, name, eq):
        self.sd.system_dynamics_converter_func(self.model, name, self._converter_eq(eq))
        return name

    def sector_link(self, sector_id):
        return self.lua.table_from(self.factory.sector_link(sector_id, self.establishments), recursive=True)

    def sector_summary(self, sector_id):
        return self.lua.table_from(self.factory.sector_summary(sector_id, self.establishments), recursive=True)

    def run_file(self, path):
        with open(path, encoding="utf-8") as f:
            return self.lua.execute(f.read())

    def value(self, name, t):
        return self.model.memoize(name, t)

    def series(self):
        """2026/09/24: WebUI용. 모든 stock/converter의 시간별 값을 {name: [값...]}으로 돌려준다."""
        steps = int((self.model.stoptime - self.model.starttime) / self.model.dt) + 1
        times = []
        for i in range(steps):
            times.append(self.model.starttime + i * self.model.dt)

        result = {}
        for name in list(self.model.stocks) + list(self.model.converters):
            if name.startswith("lua_"):  # _key/_stock_eq가 만든 내부 이름
                continue
            values = []
            for t in times:
                values.append(self.model.memoize(name, t))
            result[name] = values

        return {"time": times, "series": result}

    def map_records(self):
        """
        2026/09/24: 지도(WAR ECONOMY UI)용. establishment마다
        {sector, latitude, longitude, name, country, data:[{time, ...}]}를 돌려준다.
        data에는 그 사업장의 값(접두사 제거: capital, labor, capacity)과
        어느 사업장에도 속하지 않는 공용 converter(steel_output 등)가 들어간다.
        """
        result = self.series()
        ids = []
        for e in self.establishments:
            ids.append(f"{e['sector']}_{e['posx']}_{e['posy']}")

        records = []
        for e, est_id in zip(self.establishments, ids):
            keys = {}  # series 이름 -> 화면에 보일 이름
            for name in result["series"]:
                if name.startswith(est_id + "_"):
                    keys[name] = name[len(est_id) + 1:]
                    continue
                shared = True
                for other in ids:
                    if name.startswith(other + "_"):
                        shared = False
                if shared:
                    keys[name] = name

            data = []
            for i, t in enumerate(result["time"]):
                row = {"time": int(t) if float(t).is_integer() else t}
                for name, key in keys.items():
                    row[key] = result["series"][name][i]
                data.append(row)

            info = self.info.get(est_id, {})
            records.append({
                "sector": e["sector"],
                "latitude": e["posx"],
                "longitude": e["posy"],
                "name": info.get("name", est_id),
                "country": info.get("country", ""),
                "data": data,
            })

        return records
