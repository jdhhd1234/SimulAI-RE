from BPTK_Py import Model
from BPTK_Py import sd_functions as sd

from typing import Any

class SystemDynamicMakeSector:
    
    # posx = Position X
    # posy = position Y
    def __init__(self, posx, posy) -> None:
        self.posx = posx
        self.posy = posy
        
    def _make_sector(
        self,
        model: Model,
        sector_type: str,
        capital: float,
        labor: int,
        productivity: float
    ):
        """
        2026/09/22: 일단은 그냥 아무연결도 없는 개인정보만 가지고 있는 sector을 만들기.
        sector_type -> Lua -> 유저가 만든 서로엮이는 sector공식들
        2026/09/23: 입력값을 BPTK-Py가 알아먹는 stock/converter로 변환한다.
        """
        sector_capital = model.stock(f"{sector_type}_capital")
        sector_capital.equation = 0 # 2026/09/23: 일단 0으로 처리한다. 나중에 공식화
        sector_capital.initial_value = float(capital)

        sector_labor = model.stock(f"{sector_type}_labor")
        sector_labor.equation = 0
        sector_labor.initial_value = float(labor)

        sector_productivity = model.converter(f"{sector_type}_productivity")
        sector_productivity.equation = productivity

        return {
            "sector_type": sector_type,
            "capital": sector_capital,
            "labor": sector_labor,
            "productivity": sector_productivity,
            "posx": self.posx,
            "posy": self.posy,
        }
    
    def connect_sector(self, sector_a: dict, sector_b: dict):
        """
        2026/09/23: 이 부분은 기존에 sector을 연결해주는 함수이다.
        """
        return {
            "from": sector_a["sector_type"],
            "to": sector_b["sector_type"],
        }
        
    