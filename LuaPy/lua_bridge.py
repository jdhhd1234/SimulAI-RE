import os
import sys

import lupa

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import calc.dynamics_system.dynamic_lowlevel as dm
import calc.dynamics_system.dynamic_sector as ds
import calc.dynamics_system.dynamic_index as di
import calc.abm.abm_consumer_market as abm


class LuaBridge:
    """
    2026/09/30: dynamic_lowlevel.py + dynamic_sector.py 기준으로 재작성.
    2026/10/14: dynamic_index.py(지역) + abm_market.py(소비자 ABM)도 Lua에 연결.
    - SD: ModelSystemDynamics / SystemDynamics(stock, flow, converter)
    - Sector: SystemDynamicSector의 sector API를 그대로 감싼다.
    - Region: SystemDynamicChara의 지역 API를 그대로 감싼다.
    - ABM: 10% 소득계층 소비자 그룹(ConsumerAgent)
    Lua 사용법:
        local sec = api.make_sector("bio")
        api.set_resource("resource", 1000, 100, 1.0, 1.0)
        local rule = api.set_production_rule("bio_rule", {resource = 1}, 0.8)
        local fac_id = api.sector_create_factory("bio_factory", sec, 37.5, 127.0)
        api.sector_factory_setting(fac_id, {capacity = 100})
        api.set_sector_production_rule(sec, rule)
        api.connect_supply_chain(sec)

        local seoul = api.make_region("Seoul")
        api.set_region_resource(seoul, "resource", 500)
        api.set_population(seoul, 10000, 0.01, 0.6)
        api.set_infrastructure(seoul, 0.9, 0.8, 0.9, 0.95)
        api.make_consumer_groups(api.get_region(seoul).population.total)
    """

    def __init__(self, start_time, stop_time, dt, name: str):
        self.model = dm.ModelSystemDynamics(start_time, stop_time, dt, name).system_dynamics_makeModel_func()
        self.model.lua_fn = {}  # BPTK equation 문자열이 model.lua_fn[key](t)로 Lua 함수를 부른다.
        self.factory = ds.SystemDynamicSector()
        self.chara = di.SystemDynamicChara()
        self.sd = dm.SystemDynamics()
        self.consumers = []
        self.consumer_rows = None  # ABM은 상태가 있어서 한번만 진행시키고 결과를 재사용한다.
        # 지도 API용 공장 위치 목록. 실제 저장소는 factory.factories다.
        self.establishments = []
        self.info = {}
        self.locations = []
        self.console = []

        self.lua = lupa.LuaRuntime(unpack_returned_tuples=False)
        self.lua.globals()["api"] = self
        self.lua.globals()["get"] = lambda name, t: self.model.memoize(name, t)
        self.lua.globals()["print"] = self._print
        self.set_locations([])

    # 저장소는 SystemDynamicSector 하나만 두고, 기존 호출부를 위해 이름만 노출한다.
    @property
    def factories(self):
        return self.factory.factories

    @property
    def production_rules(self):
        return self.factory.production_rules

    @property
    def resources(self):
        return self.factory.resources

    def _print(self, *values):
        self.console.append("\t".join(str(value) for value in values))

    def _key(self, fn):
        key = f"lua_{len(self.model.lua_fn)}"
        self.model.lua_fn[key] = lambda t: float(fn(t))
        return key

    def _converter_eq(self, eq):
        """Lua 함수면 BPTK가 받는 문자열 equation으로 바꾼다. 숫자/문자열/None은 그대로."""
        if lupa.lua_type(eq) == "function":
            return f"model.lua_fn['{self._key(eq)}'](t)"
        return 0 if eq is None else eq

    def _stock_eq(self, eq):
        """stock은 숫자/Element만 받는다. Lua 함수면 변화율 converter를 만들어 그 Element를 넘긴다."""
        if lupa.lua_type(eq) == "function":
            key = self._key(eq)
            return self.sd.system_dynamics_converter_func(
                self.model, f"{key}_rate", f"model.lua_fn['{key}'](t)"
            )
        return 0 if eq is None else eq

    @staticmethod
    def _to_python(value):
        if lupa.lua_type(value) == "table":
            return {
                LuaBridge._to_python(key): LuaBridge._to_python(item)
                for key, item in value.items()
            }
        return value

    def _resolve_sector(self, sector_ref):
        """sector 인자(이름 문자열 또는 name 키가 있는 dict/Lua 테이블) -> (name, sector dict)."""
        name = sector_ref if isinstance(sector_ref, str) else sector_ref["name"]
        sector = self.factory.sectors.get(name)
        if sector is None:
            raise ValueError(f"unknown sector: {sector_ref!r} (먼저 api.make_sector(name)을 호출하세요)")
        return name, sector

    def _resolve_factory(self, factory_id):
        factory = self.factories.get(factory_id)
        if factory is None:
            raise ValueError(f"unknown factory: {factory_id!r} (먼저 api.sector_create_factory를 호출하세요)")
        return factory

    # ---------- Sector ----------

    def make_sector(self, name):
        """분류 껍데기를 만들고 factory.sectors에 보관한다. Lua 연쇄 호출용으로 이름(핸들)을 돌려준다."""
        self.factory.make_sector(name)
        return name

    def set_production_rule(self, name, need_resource, yield_rate):
        self.factory.set_production_rule(name, self._to_python(need_resource), float(yield_rate))
        return name

    def set_sector_production_rule(self, sector, rule):
        sector_name, _ = self._resolve_sector(sector)
        self.factory.set_sector_production_rule(sector_name, rule)
        return sector_name

    def set_resource(self, name, reserve, extraction_capacity, extraction_cost, processing_yield):
        self.factory.set_resource(
            name,
            int(reserve),
            int(extraction_capacity),
            float(extraction_cost),
            float(processing_yield),
        )
        return name

    def sector_create_factory(self, name, sector, latitude=0, longitude=0):
        """특정 좌표에 공장을 건설하고, 이후 설정에 사용할 핸들을 돌려준다."""
        sector_name, _ = self._resolve_sector(sector)
        factory_id = str(name)
        if factory_id in self.factories:
            raise ValueError(f"factory already exists: {factory_id}")
        self.factory.sector_create_factory(factory_id, sector_name)
        self.establishments.append({
            "id": factory_id,
            "sector": sector_name,
            "latitude": float(latitude),
            "longitude": float(longitude),
        })
        return factory_id

    def sector_make_factory(self, name, sector, latitude=0, longitude=0):
        """기존 Lua 시나리오가 사용할 수 있는 공장 생성 이름이다."""
        return self.sector_create_factory(name, sector, latitude, longitude)

    def sector_factory_setting(self, factory_id, settings=None, **kwargs):
        self._resolve_factory(factory_id)
        if settings is not None:
            kwargs.update(self._to_python(settings))
        self.factory.sector_factory_setting(factory_id, **kwargs)
        return factory_id

    def connect_supply_chain(self, sector):
        name, _ = self._resolve_sector(sector)
        return self.factory.connect_supply_chain(name, self.model)

    def delete_factory(self, factory_id):
        factory = self._resolve_factory(factory_id)
        sector = self.factory.sectors.get(factory["sector"])
        if sector is None or self.factory.sector_delete_factory(sector, factory_id) is None:
            raise ValueError(f"factory is not attached to a sector: {factory_id!r}")
        self.info.pop(factory_id, None)
        self.establishments = [item for item in self.establishments if item["id"] != factory_id]
        return factory_id

    def delete_sector(self, name):
        sector = self.factory.sectors.get(name)
        if sector is None:
            return None
        for factory_id in list(sector["factories"]):
            self.delete_factory(factory_id)
        self.factory.delete_sector(name)
        return name

    def delete_production_rule(self, name):
        return self.factory.delete_recipe(name) is not None

    def delete_resource(self, name):
        return self.factory.delete_resource(name) is not None

    # ---------- Region ----------

    def make_region(self, name):
        self.chara.make_region(name)
        return name

    def delete_region(self, name):
        return self.chara.delete_region(name) is not None

    def get_region(self, name):
        """지역 정보를 Lua 테이블로 돌려준다. Lua: api.get_region("Seoul").population.total"""
        region = self.chara.get_region(name)
        if region is None:
            return None
        return self.lua.table_from(region, recursive=True)

    def set_region_resource(self, region, resource, amount):
        self.chara.set_region_resource(region, resource, amount, self.factory)
        return region

    def delete_region_resource(self, region, resource):
        return self.chara.delete_region_resource(region, resource) is not None

    def set_population(self, region, total, growth_rate=0.0, labor_ratio=0.0):
        self.chara.set_population(region, int(total), float(growth_rate), float(labor_ratio))
        return region

    def set_infrastructure(self, region, power=0.0, transport=0.0, water=0.0, telecom=0.0):
        self.chara.set_infrastructure(region, power, transport, water, telecom)
        return region

    # ---------- ABM ----------

    def make_consumer_groups(self, population=10000, mean=300.0, std=100.0, groups=10):
        """정규분포 소득 인구를 10% 계층 소비자 그룹으로 만든다. 만든 그룹 수를 돌려준다."""
        # make_consumer_groups는 ConsumerAgent 메서드지만 self를 쓰지 않아서 클래스로 바로 부른다.
        # 이 부분은 나중에 abm_company_market.py에서 make_consumer_groups라는 함수를 추가해서 할것이다 (Claude Code쓸꺼임.)
        self.consumers = abm.Consumer.make_consumer_groups(
            None, self.model, int(population), float(mean), float(std), int(groups)
        )
        self.consumer_rows = None
        return len(self.consumers)

    def consumer_series(self, times):
        """소비자 그룹을 times 순서대로 진행시키고 시간별 상태를 돌려준다."""
        rows = []
        for step, t in enumerate(times):
            groups = []
            for agent in self.consumers:
                agent.act(t, step, 0)
                groups.append({
                    "decile": agent.get_property_value("decile"),
                    "population": agent.get_property_value("population"),
                    "state": agent.state,
                    "income": agent.get_property_value("income"),
                    "cash": agent.get_property_value("cash"),
                    "consume": agent.get_property_value("consume"),
                })
            rows.append({
                "time": t,
                "groups": groups,
                "total_consume": sum(group["consume"] for group in groups),
            })
        return rows

    # ---------- SD ----------

    def make_stock(self, name, eq=None, init_value=0.0):
        self.sd.system_dynamics_stock_func(self.model, name, self._stock_eq(eq), float(init_value))
        return name

    def make_flow(self, name, eq=None):
        self.sd.system_dynamics_flow_func(self.model, name, self._converter_eq(eq))
        return name

    def make_converter(self, name, eq=None):
        self.sd.system_dynamics_converter_func(self.model, name, self._converter_eq(eq))
        return name

    # ---------- UI ----------

    def set_locations(self, locations):
        """
        UI에서 추가한 위치를 Lua 전역 locations 테이블(1부터 시작)로 넘긴다.
        Lua: locations[1].name, locations[1].lat, locations[1].lon
        """
        self.locations = [dict(location) for location in locations]
        items = [
            {
                "id": location["id"],
                "name": location["name"],
                "lat": location["latitude"],
                "lon": location["longitude"],
            }
            for location in locations
        ]
        self.lua.globals()["locations"] = self.lua.table_from(items, recursive=True)

    def get_info_marker(self, name):
        """WebUI에서 추가한 위치 마커를 이름으로 조회한다."""
        for location in self.locations:
            if location["name"] == name:
                return location
        raise ValueError(f"unknown location marker: {name!r}")

    def describe(self, factory_id, name, country=""):
        """지도에 보일 이름/국가. factory_id는 sector_create_factory가 돌려준 값."""
        self.info[factory_id] = {"name": name, "country": country}

    def sector_link(self, sector):
        """해당 sector의 공장과 연결된 레시피를 조회한다."""
        name, sector_dict = self._resolve_sector(sector)
        return {
            "sector": name,
            "factories": list(sector_dict["factories"]),
            "production_rule": self.production_rules.get(sector_dict.get("production_rule")),
        }

    def sector_summary(self, sector):
        """해당 sector의 공장 수와 capacity 요약을 돌려준다."""
        name, sector_dict = self._resolve_sector(sector)
        factories = sector_dict["factories"]
        return {
            "sector": name,
            "factory_count": len(factories),
            "capacity": sum(float(self.factories[factory].get("capacity", 0)) for factory in factories),
            "locations": [
                [item["latitude"], item["longitude"]]
                for item in self.establishments if item["sector"] == name
            ],
        }

    # ---------- Run / Result ----------

    def run_file(self, path):
        with open(path, encoding="utf-8") as f:
            return self.lua.execute(f.read())

    def value(self, name, t):
        return self.model.memoize(name, t)

    def times(self):
        steps = int((self.model.stoptime - self.model.starttime) / self.model.dt) + 1
        return [self.model.starttime + i * self.model.dt for i in range(steps)]

    def series(self):
        """
        WebUI용. 모든 stock/flow/converter의 시간별 값을 {name: [값...]}으로 돌려준다.
        소비자 그룹이 있으면 "consumers"에 시간별 ABM 결과도 넣는다.
        """
        times = self.times()
        result = {}
        for name in list(self.model.stocks) + list(self.model.flows) + list(self.model.converters):
            if name.startswith("lua_"):  # _key/_stock_eq가 만든 내부 이름
                continue
            result[name] = [self.model.memoize(name, t) for t in times]

        output = {"time": times, "series": result}
        if self.consumers:
            if self.consumer_rows is None:
                self.consumer_rows = self.consumer_series(times)
            output["consumers"] = self.consumer_rows
        return output

    def results(self):
        """sector/지역/SD/ABM 전체 상태를 JSON으로 바꿀 수 있는 dict로 돌려준다."""
        return {
            "sectors": self.factory.sectors,
            "factories": self.factories,
            "resources": self.resources,
            "production_rules": self.production_rules,
            "regions": self.chara.regions,
            **self.series(),
        }

    def map_records(self):
        """
        지도(WAR ECONOMY UI)용. sector의 공장마다
        {sector, latitude, longitude, name, country, data:[{time, ...}]}를 돌려준다.
        현 엔진의 stock/converter는 전역 이름이므로 모든 공장이 같은 시계열을 공유한다.
        """
        result = self.series()
        data = []
        for i, t in enumerate(result["time"]):
            row = {"time": int(t) if float(t).is_integer() else t}
            for name, values in result["series"].items():
                row[name] = values[i]
            data.append(row)

        records = []
        for establishment in self.establishments:
            info = self.info.get(establishment["id"], {})
            records.append({
                "sector": establishment["sector"],
                "latitude": establishment["latitude"],
                "longitude": establishment["longitude"],
                "name": info.get("name", establishment["id"]),
                "country": info.get("country", ""),
                "data": [dict(row) for row in data],
            })

        return records
