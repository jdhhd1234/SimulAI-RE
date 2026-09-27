from BPTK_Py import Model
from BPTK_Py import sd_functions as sd

from typing import Any

class SystemDynamicMakeSector:

    def make_sector(self, id: str, name: str):
        """
        2026/09/24: APIPlan.md 반영. sector은 분류 정보만 가진다.
        수치/모델 데이터(capital, labor 등)는 make_establishment가 가진다.
        """
        return {
            "id": id,
            "name": name,
        }
        
    def sector_make_factory(self, x: float, y: float, sec_type: str):
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