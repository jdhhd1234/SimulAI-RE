import dynamic_main as dm

from typing import Any

class SystemDynamicSector:

    def __init__(self):
        # 2026/09/30: make_sector가 만든 sector 정보를 단발성으로 흘려보내지 않고
        # factory가 살아있는 동안 계속 보관한다. (LuaBridge.recipes/info와 같은 방식)
        self.sectors = {}

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
        - factory_size
        - product_type
        
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
        }

        sector["factories"].append(factory)

        return factory
    

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
    
    def sector_supply_chain(
        self, 
        input_mass: float,
        output_mass: float,
        # yield product
        yield_rate: float
    ):
        """
        2026/09/30: A라는 sector가 어떤걸 Input받고 어떤걸 Output하는지
        KG기준
        
        지금은 하나의 재료를 투입해서 하나가 나오는거지만
        점진적으로 여러개를 투입해서 하나가 나오는식으로 진화 해야함.
        """
        
        output_mass = input_mass * yield_rate
        
        return output_mass