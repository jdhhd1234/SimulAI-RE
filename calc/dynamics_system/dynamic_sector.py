import dynamic_main as dm

from typing import Any

class SystemDynamicMakeSector:

    def make_sector(self, name: str):
        """
        2026/09/24: APIPlan.md 반영. sector은 분류 정보만 가진다.
        수치/모델 데이터(capital, labor 등)는 make_establishment가 가진다.
        
        2026/09/30: 지금 보니까 이 정보를 단발성 휘발성으로 가지고 있는게 아니라.
        계속 지속을 해야할거 같음.
        """
        return {
            "name": name
        }
        
    def sector_make_factory(
        self, 
        x: float, 
        y: float,
        name: str
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
        
        # 2026/09/30: 여기다가 이제 외부에서 make_sector에서 만든정보를 받아야함
        """ Lua
        make_sec_bio = make_sector("bio")
        make_fac_1 = sector_make_factory(1200, 720, make_sec_bio)
        """
        
        