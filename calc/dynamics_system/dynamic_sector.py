from BPTK_Py import Model
from BPTK_Py import sd_functions as sd

import calc.dynamics_system.dynamic_model as dynamic_model

class SystemDynamicSector:

    def __init__(self):
        # 2026/09/30: make_sector가 만든 sector 정보를 단발성으로 흘려보내지 않고
        # factory가 살아있는 동안 계속 보관한다. (LuaBridge.recipes/info와 같은 방식)

        # 어떤 sector이 있는지
        self.sectors = {}

        # 어떤 공장이 있는지
        self.factories = {}

        # 어떤 조합법이 있는지
        self.production_rules = {}

        # 어떤 자원이 있는지
        self.resources = {}

        # 공급망 연결 상태는 어떤지
        self.supply_chain = {}

    def make_sector(self, name: str):
        """
        2026/09/24: APIPlan.md 반영. sector은 분류 정보만 가진다.
        수치/모델 데이터(capital, labor 등)는 make_establishment가 가진다.

        2026/09/30: 지금 보니까 이 정보를 단발성 휘발성으로 가지고 있는게 아니라.
        계속 지속을 해야할거 같음.
        """
        if name not in self.sectors:
            self.sectors[name] = {
                "name": name,
                "factories": []
            }

        return self.sectors[name]

    def delete_sector(self, name: str):
        return self.sectors.pop(name, None)

    def set_resource(
        self,
        name: str,
        reserve: int,
        extraction_capacity: int,
        extraction_cost: float,
        processing_yield: float
    ):
        """
        2026/10/03: 자원을 설정하는 함수
        """
        set_res_data = {
            "name": name,
            "reserve": reserve,
            "extraction_capa": extraction_capacity,
            "extraction_cost": extraction_cost,
            "processing_yield": processing_yield
        }

        self.resources[name] = set_res_data

        return set_res_data

    def delete_resource(self, name: str):
        return self.resources.pop(name, None)

    def set_production_rule(
        self,
        name: str,
        need_resource: dict,
        yield_rate: float
    ):
        """
        2026/10/03: 특정 생산품을 만들기위해 들어가는 함수
        """

        """
        2026/10/03
        need_resource 예시:
        {
            "steel": 100.0,
            "carbon": 20.0,
            "oil": 10.0
        }
        """

        checked_resource = {}

        for resource, amount in need_resource.items():

            if resource not in self.resources:
                raise ValueError(f"Dont Exist Resource: {resource}")

            amount = float(amount)

            if amount <= 0:
                raise ValueError(
                    f"{resource} The required amount must be greater than zero"
                )

            checked_resource[resource] = amount

        recipe = {
            "name": name,
            "need_resource": checked_resource,
            "yield_rate": float(yield_rate)
        }

        self.production_rules[name] = recipe

        return recipe

    def delete_recipe(self, name: str):
        return self.production_rules.pop(name, None)

    def set_sector_production_rule(self, sector_name: str, rule_name: str):
        if sector_name not in self.sectors:
            raise ValueError(f"Dont Exist Sector: {sector_name}")
        if rule_name not in self.production_rules:
            raise ValueError(f"Dont Exist Production Rule: {rule_name}")

        self.sectors[sector_name]["production_rule"] = rule_name
        return self.sectors[sector_name]

    def sector_create_factory(
        self,
        factory_name: str,
        sector: str
    ):
        """
        2026/09/27: 공장을 특정 좌표에 건설한다.
        ## Parameters
        - xpos
        - ypos
        - sector_type
        
        ## Engine Dynamic calculate
        - month_product
        """
        
        # 2026/09/30: make_sector가 돌려준 지속 sector를 그대로 받아서
        # 그 sector에 공장을 붙인다.
        """ Lua
        make_sec_bio = make_sector("bio")
        make_fac_1 = sector_make_factory(1200, 720, make_sec_bio)
        """
        factory = {
            "capacity": 1.0,
            "sector": sector,
            "inventory": {},
            "settings": {}
        }

        self.factories[factory_name] = factory

        self.sectors[sector]["factories"].append(factory_name)

        return factory

    def sector_delete_factory(
        self,
        sector: dict,
        factory_name: str
    ):
        if factory_name in sector["factories"]:
            sector["factories"].remove(factory_name)
            return self.factories.pop(factory_name, None)

        return None

    def sector_factory_setting(
        self,
        factory_name: str,
        **settings
    ):
        factory = self.factories.get(factory_name)

        if factory is None:
            return None

        factory.update(settings)

        return factory

    def connect_supply_chain(self, sector_name: str, model: Model):

        """
        2026/10/03

        이 함수는 기존에 있는 그냥 속과 알맹이만 있는 특징에 자동으로 flow를 붙치는 역할을 한다.
        """

        """
        # Plan
        
        1. 여기있는 정보를 다 읽기
        make_sector -> dict
        set_production_rule -> dict
        sector_create_factory -> dict

        2. 읽은 다음에 그걸 BPTK-Py로 변환시킨다
        """

        sector = self.sectors[sector_name]

        rule = self.production_rules[
            sector["production_rule"]
        ]

        factories = [
            self.factories[name]
            for name in sector["factories"]
        ]

        capacity = 0.0

        for factory in factories:
            capacity += factory["capacity"]

        if capacity <= 0:
            raise ValueError(f"{sector_name} has no production capacity")

        functions = getattr(model, "sector_fn", None)
        if functions is None:
            functions = {}
            model.sector_fn = functions

        production_name = f"{sector_name}_production"
        output_name = f"{sector_name}_output"
        stock_names = {}

        for resource, amount in rule["need_resource"].items():
            resource_data = self.resources[resource]
            stock_name = f"{sector_name}_{resource}_reserve"
            stock_names[resource] = stock_name
            model.stock(stock_name).initial_value = float(resource_data["reserve"])

        def production_rate(t):
            available_capacity = capacity
            for resource, amount in rule["need_resource"].items():
                resource_data = self.resources[resource]
                reserve = max(0.0, model.memoize(stock_names[resource], t))
                available_capacity = min(
                    available_capacity,
                    resource_data["extraction_capa"] / amount,
                    reserve / amount,
                )
            return available_capacity * rule["yield_rate"]

        functions[production_name] = production_rate
        production_flow = model.flow(production_name)
        production_flow.equation = f"model.sector_fn['{production_name}'](t)"
        model.stock(output_name).equation = production_flow

        for resource, amount in rule["need_resource"].items():
            consumption_name = f"{sector_name}_{resource}_consumption"
            functions[consumption_name] = lambda t, amount=amount: -production_rate(t) * amount
            consumption_flow = model.flow(consumption_name)
            consumption_flow.equation = f"model.sector_fn['{consumption_name}'](t)"
            model.stock(stock_names[resource]).equation = consumption_flow

        return {
            "sector": sector_name,
            "production": production_name,
            "output": output_name,
            "resources": stock_names,
        }
