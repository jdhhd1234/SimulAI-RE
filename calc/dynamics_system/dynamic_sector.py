from BPTK_Py import Model
from BPTK_Py import sd_functions as sd

import calc.dynamics_system.dynamic_model as dynamic_model

class SystemDynamicSector:

    def __init__(self):
        # 2026/09/30: make_sector가 만든 sector 정보를 단발성으로 흘려보내지 않고
        # factory가 살아있는 동안 계속 보관한다. (LuaBridge.recipes/info와 같은 방식)
        self.sectors = {}
        self.recipes = {}
        self.resources = {}

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
        recipe = {
            "name": name,
            "need_resource": need_resource,
            "yield_rate": yield_rate
        }

        self.recipes[name] = recipe

        return recipe

    def delete_recipe(self, name: str):
        return self.recipes.pop(name, None)

    def sector_create_factory(
        self,
        x: float,
        y: float,
        sector: dict
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
            "x": x,
            "y": y,
            "capacity": 1.0,
            "inventory": {}
        }

        sector["factories"].append(factory)

        return factory

    def sector_delete_factory(
        self,
        sector: dict,
        factory: dict
    ):
        for index, saved_factory in enumerate(sector["factories"]):
            if saved_factory is factory:
                return sector["factories"].pop(index)
            
        return None
    

    def sector_factory_setting(
        self,
        factory: dict,
        **settings
    ):
        """
        2026/09/30
        이미 sector_make_factory를 통해 만들어진 공장에서 추가적인 부가적인 세팅을 하는것.
        
        해야할것
        1. sector_make_factory에 관한 정보를 받아와야함.
        2. 추가 정보를 더 붙힘
        """
        
        factory.update(settings)
        return factory

    def connect_supply_chain(
        self,
        first_connecter: dict,
        end_connect: str
    ):
        """
        2026/09/30: A라는 sector가 어떤걸 Input받고(자원 kg기준)
        어떤걸 Output(생산품 하나기준 int하는지

        지금은 하나의 재료를 투입해서 하나가 나오는거지만
        점진적으로 여러개를 투입해서 하나가 나오는식으로 진화 해야함.
        """
        
        """
        2026/10/02
        예를들어서 항공기에 비유 하면
        
        [강철, 카본, 석유] -> 항공에 맞게 가공 -> airplane 섹터 -> airplane output
        """

        recipe = self.recipes[end_connect]
        
        need = recipe["need_resource"]
        
        sector_name = first_connecter["name"]
        
        capacity = 0.0
        
        for f in first_connecter["factories"]:
            capacity += f["capacity"]
            
        # Lua Binding Support Model
        model_ = dynamic_model.SystemDynamicsModel.create_model

        # 투입 자원(kg)마다 stock 하나. 초기값은 set_resource의 reserve.
        stocks = {}
        
        for res in need:
            stocks[res] = model_.stock(res)
            stocks[res].initial_value = float(self.resources.get(res, {}).get("reserve", 0))

        # 생산 속도 = 재료 중 가장 모자란 것 / 필요량, 공장 capacity 상한
        rate = model_.converter(f"{sector_name}_rate")
        
        rate_eq = capacity
        
        for res, amount in need.items():
            rate_eq = sd.min(rate_eq, stocks[res] / amount)
            
        rate.equation = rate_eq

        # 재료 소모 flow -> 각 stock의 outflow
        for res, amount in need.items():
            use = model_.flow(f"{res}_use")
            use.equation = rate * amount
            
            stocks[res].equation = -use

        # 생산품 stock (yield_rate 반영)
        output = model_.stock(f"{sector_name}_output")
        output.initial_value = 0.0
        
        make = model_.flow(f"{sector_name}_make")
        make.equation = rate * recipe["yield_rate"]
        
        output.equation = make

        return model_