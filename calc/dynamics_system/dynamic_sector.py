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

    def make_good(self, id: str, unit: str):
        """
        2026/09/24: 철강(톤), 전기(kWh)처럼 단위를 가지는 재화 정의.
        """
        return {
            "id": id,
            "unit": unit,
        }

    def set_recipe(
        self,
        output_good: str,
        inputs: dict,
        labor: int,
        capacity: float
    ):
        """
        2026/09/24: output_good을 생산하는 레시피.
        inputs = {good_id: 수량}
        """
        return {
            "output_good": output_good,
            "inputs": inputs,
            "labor": labor,
            "capacity": capacity,
        }

    def make_establishment(
        self,
        model: Model,
        sector: str,
        location: tuple,
        recipe: dict,
        capital: float = 0.0
    ):
        """
        2026/09/24: 실제 생산 주체. sector + location + recipe를 가지고
        BPTK-Py가 알아먹는 stock/converter로 변환한다.
        """
        posx, posy = location
        establishment_id = f"{sector}_{posx}_{posy}"

        establishment_capital = model.stock(f"{establishment_id}_capital")
        establishment_capital.equation = 0 # 2026/09/23: 일단 0으로 처리한다. 나중에 공식화
        establishment_capital.initial_value = float(capital)

        establishment_labor = model.stock(f"{establishment_id}_labor")
        establishment_labor.equation = 0
        establishment_labor.initial_value = float(recipe["labor"])

        establishment_capacity = model.converter(f"{establishment_id}_capacity")
        establishment_capacity.equation = recipe["capacity"]

        return {
            "sector": sector,
            "posx": posx,
            "posy": posy,
            "recipe": recipe,
            "capital": establishment_capital,
            "labor": establishment_labor,
            "capacity": establishment_capacity,
        }

    def sector_link(self, sector_id: str, establishments: list):
        """
        2026/09/24: 레시피들로부터 자동 계산되는 조회용.
        Input = sector_id가 어떤 sector의 생산품에 영향을 받는지(influenced_by)
        Output = sector_id가 다른 sector에게 영향을 주는지(influences)
        """
        good_to_sector = {
            e["recipe"]["output_good"]: e["sector"]
            for e in establishments
        }

        target = next((e for e in establishments if e["sector"] == sector_id), None)
        input_goods = target["recipe"]["inputs"].keys() if target else []

        influenced_by = [
            good_to_sector[good]
            for good in input_goods
            if good in good_to_sector
        ]

        my_output_good = target["recipe"]["output_good"] if target else None
        influences = [
            e["sector"]
            for e in establishments
            if my_output_good is not None and my_output_good in e["recipe"]["inputs"]
        ]

        return {
            "sector_id": sector_id,
            "influenced_by": influenced_by,
            "influences": influences,
        }
