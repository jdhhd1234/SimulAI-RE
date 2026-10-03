import os
import sys

import lupa

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import calc.dynamics_system.dynamic_lowlevel as dm
import calc.dynamics_system.dynamic_sector as ds


class LuaBridge:
    """
    2026/09/30: dynamic_main.py + dynamic_sector.py 기준으로 재작성.
    - SD: ModelSystemDynamics / SystemDynamics(stock, flow, converter)만 쓴다.
    - Sector: SystemDynamicSector의 sector API를 그대로 감싼다.
    Lua 사용법:
        local sec = api.make_sector("bio")
        api.set_resource("resource", 1000, 100, 1.0, 1.0)
        local rule = api.set_production_rule("bio_rule", {resource = 1}, 0.8)
        local fac_id = api.sector_create_factory("bio_factory", sec, 37.5, 127.0)
        api.sector_factory_setting(fac_id, {capacity = 100})
        api.set_sector_production_rule(sec, rule)
        api.connect_supply_chain(sec)
    """

    def __init__(self, start_time, stop_time, dt, name: str):
        self.model = dm.ModelSystemDynamics(start_time, stop_time, dt, name).system_dynamics_makeModel_func()
        self.model.lua_fn = {}  # BPTK equation 문자열이 model.lua_fn[key](t)로 Lua 함수를 부른다.
        self.factory = ds.SystemDynamicSector()
        self.sd = dm.SystemDynamics()
        # 지도 API와 기존 호출부가 사용할 수 있도록 평탄 목록도 유지한다.
        # 실제 저장소는 factory.sectors[name]["factories"]다.
        self.establishments = []
        self.info = {}
        self.factories = {}
        self.factory_sectors = {}
        self.factory_ids = {}
        self.production_rules = {}
        self.resources = {}
        self.locations = []
        self.console = []

        self.lua = lupa.LuaRuntime(unpack_returned_tuples=False)
        self.lua.globals()["api"] = self
        self.lua.globals()["get"] = lambda name, t: self.model.memoize(name, t)
        self.lua.globals()["print"] = self._print
        self.set_locations([])

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

    def _resolve_sector(self, sector_ref):
        """sector 인자(이름 문자열, sector dict, Lua 테이블) -> (name, sector dict)."""
        name = None
        if isinstance(sector_ref, str):
            name = sector_ref
        elif isinstance(sector_ref, dict):
            name = sector_ref.get("name")
        else:
            # lupa Lua 테이블(또는 Python 객체): ["name"] / .name / .get("name") 순서로 시도
            for accessor in (
                lambda r: r["name"],
                lambda r: r.name,
                lambda r: r.get("name"),
            ):
                try:
                    name = accessor(sector_ref)
                    break
                except Exception:
                    continue
            if name is None:
                # make_sector가 이름 문자열을 돌려주므로, 테이블이 곧 이름인 경우
                try:
                    name = str(sector_ref)
                except Exception:
                    name = None
        sector = self.factory.sectors.get(name) if name is not None else None
        if sector is None:
            raise ValueError(f"unknown sector: {sector_ref!r} (먼저 api.make_sector(name)을 호출하세요)")
        return name, sector

    @staticmethod
    def _to_python(value):
        if lupa.lua_type(value) == "table":
            return {
                LuaBridge._to_python(key): LuaBridge._to_python(item)
                for key, item in value.items()
            }
        if isinstance(value, dict):
            return {key: LuaBridge._to_python(item) for key, item in value.items()}
        if isinstance(value, list):
            return [LuaBridge._to_python(item) for item in value]
        return value

    def _resolve_factory(self, factory_ref):
        if isinstance(factory_ref, str):
            factory = self.factories.get(factory_ref)
        elif isinstance(factory_ref, dict):
            factory = factory_ref
        else:
            factory = None

        if factory is None:
            raise ValueError(f"unknown factory: {factory_ref!r} (먼저 api.sector_create_factory를 호출하세요)")
        return factory

    def _resolve_resource(self, resource_ref):
        if isinstance(resource_ref, str):
            resource = self.resources.get(resource_ref)
        elif isinstance(resource_ref, dict):
            resource = resource_ref
        else:
            resource = self._to_python(resource_ref)

        if resource is None:
            raise ValueError(f"unknown resource: {resource_ref!r} (먼저 api.set_resource(name, ...)를 호출하세요)")
        return resource

    def make_sector(self, name):
        """분류 껍데기를 만들고 factory.sectors에 보관한다. Lua 연쇄 호출용으로 이름(핸들)을 돌려준다."""
        self.factory.make_sector(name)
        return name

    def set_production_rule(self, name, need_resource, yield_rate):
        recipe = self.factory.set_production_rule(
            name, self._to_python(need_resource), float(yield_rate)
        )
        self.production_rules[name] = recipe
        return name

    def set_sector_production_rule(self, sector, rule):
        sector_name, _ = self._resolve_sector(sector)
        if rule not in self.production_rules:
            raise ValueError(f"unknown production rule: {rule!r}")
        self.factory.set_sector_production_rule(sector_name, rule)
        return sector_name

    def set_resource(self, name, reserve, extraction_capacity, extraction_cost, processing_yield):
        resource = self.factory.set_resource(
            name,
            int(reserve),
            int(extraction_capacity),
            float(extraction_cost),
            float(processing_yield),
        )
        self.resources[name] = resource
        return name

    def sector_create_factory(self, name, sector, latitude=0, longitude=0):
        """특정 좌표에 공장을 건설하고, 이후 설정에 사용할 핸들을 돌려준다."""
        sector_name, _ = self._resolve_sector(sector)
        factory_id = str(name)
        if factory_id in self.factories:
            raise ValueError(f"factory already exists: {factory_id}")
        factory = self.factory.sector_create_factory(factory_id, sector_name)
        self.factories[factory_id] = factory
        self.factory_sectors[factory_id] = sector_name
        self.factory_ids[id(factory)] = factory_id
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

    def sector_factory_setting(self, factory_ref, settings=None, **kwargs):
        factory = self._resolve_factory(factory_ref)
        if settings is not None:
            kwargs.update(self._to_python(settings))
        self.factory.sector_factory_setting(factory_ref, **kwargs)
        return factory_ref

    def connect_supply_chain(self, sector):
        name, _ = self._resolve_sector(sector)
        return self.factory.connect_supply_chain(name, self.model)

    def delete_factory(self, factory_ref):
        factory = self._resolve_factory(factory_ref)
        factory_id = factory_ref if isinstance(factory_ref, str) else self.factory_ids.get(id(factory))
        sector_name = self.factory_sectors.get(factory_id)
        sector = self.factory.sectors.get(sector_name) if sector_name else None
        if sector is None:
            raise ValueError(f"factory is not attached to a sector: {factory_ref!r}")

        deleted = self.factory.sector_delete_factory(sector, factory_id)
        if deleted is None:
            raise ValueError(f"factory is not attached to a sector: {factory_ref!r}")
        self.factories.pop(factory_id, None)
        self.factory_sectors.pop(factory_id, None)
        self.factory_ids.pop(id(factory), None)
        self.info.pop(factory_id, None)
        self.establishments = [item for item in self.establishments if item["id"] != factory_id]
        return factory_id

    def delete_sector(self, name):
        sector = self.factory.sectors.get(name)
        if sector is None:
            return None
        for factory in list(sector.get("factories", [])):
            factory_id = self.factory_ids.get(id(factory))
            if factory_id is not None:
                self.delete_factory(factory_id)
        self.factory.delete_sector(name)
        return name

    def delete_production_rule(self, name):
        self.production_rules.pop(name, None)
        return self.factory.delete_recipe(name) is not None

    def delete_resource(self, name):
        self.resources.pop(name, None)
        return self.factory.delete_resource(name) is not None

    def make_stock(self, name, eq=None, init_value=0.0):
        self.sd.system_dynamics_stock_func(
            self.model, name, self._stock_eq(eq), float(init_value)
        )
        return name

    def make_flow(self, name, eq=None):
        self.sd.system_dynamics_flow_func(self.model, name, self._converter_eq(eq))
        return name

    def make_converter(self, name, eq=None):
        self.sd.system_dynamics_converter_func(self.model, name, self._converter_eq(eq))
        return name

    def set_locations(self, locations):
        """
        UI에서 추가한 위치를 Lua 전역 locations 테이블(1부터 시작)로 넘긴다.
        Lua: locations[1].name, locations[1].lat, locations[1].lon
        """
        self.locations = [dict(location) for location in locations]
        items = []
        for location in locations:
            items.append({
                "id": location["id"],
                "name": location["name"],
                "lat": location["latitude"],
                "lon": location["longitude"],
            })
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
        factories = list(sector_dict.get("factories", []))
        rule_name = sector_dict.get("production_rule")
        return {
            "sector": name,
            "factories": factories,
            "production_rule": self.production_rules.get(rule_name),
        }

    def sector_summary(self, sector):
        """해당 sector의 공장 수와 capacity 요약을 돌려준다."""
        name, sector_dict = self._resolve_sector(sector)
        factories = list(sector_dict.get("factories", []))
        return {
            "sector": name,
            "factory_count": len(factories),
            "capacity": sum(float(self.factories[factory].get("capacity", 0)) for factory in factories),
            "locations": [
                [item["latitude"], item["longitude"]]
                for item in self.establishments if item["sector"] == name
            ],
        }

    def run_file(self, path):
        with open(path, encoding="utf-8") as f:
            return self.lua.execute(f.read())

    def value(self, name, t):
        return self.model.memoize(name, t)

    def series(self):
        """WebUI용. 모든 stock/converter의 시간별 값을 {name: [값...]}으로 돌려준다."""
        steps = int((self.model.stoptime - self.model.starttime) / self.model.dt) + 1
        times = []
        for i in range(steps):
            times.append(self.model.starttime + i * self.model.dt)

        result = {}
        for name in list(self.model.stocks) + list(self.model.flows) + list(self.model.converters):
            if name.startswith("lua_"):  # _key/_stock_eq가 만든 내부 이름
                continue
            values = []
            for t in times:
                values.append(self.model.memoize(name, t))
            result[name] = values

        return {"time": times, "series": result}

    def map_records(self):
        """
        지도(WAR ECONOMY UI)용. sector의 공장마다
        {sector, latitude, longitude, name, country, data:[{time, ...}]}를 돌려준다.
        현 엔진의 stock/converter는 전역 이름이므로 모든 공장이 같은 시계열을 공유한다.
        """
        result = self.series()

        records = []
        for establishment in self.establishments:
            factory_id = establishment["id"]
            data = []
            for i, t in enumerate(result["time"]):
                row = {"time": int(t) if float(t).is_integer() else t}
                for name, values in result["series"].items():
                    row[name] = values[i]
                data.append(row)

            info = self.info.get(factory_id, {})
            records.append({
                "sector": establishment["sector"],
                "latitude": establishment["latitude"],
                "longitude": establishment["longitude"],
                "name": info.get("name", factory_id),
                "country": info.get("country", ""),
                "data": data,
            })

        return records
