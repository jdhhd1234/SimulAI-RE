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
        capital: float = 0.0,
        capital_equation: Any = 0,
        labor_equation: Any = 0,
        capacity_equation: Any = None
    ):
        """
        2026/09/24: 실제 생산 주체. sector + location + recipe를 가지고
        BPTK-Py가 알아먹는 stock/converter로 변환한다.
        """
        posx, posy = location
        establishment_id = f"{sector}_{posx}_{posy}"

        establishment_capital = model.stock(f"{establishment_id}_capital")
        establishment_capital.equation = capital_equation # 2026/09/23: 일단 0으로 처리한다. 나중에 공식화
        establishment_capital.initial_value = float(capital)

        establishment_labor = model.stock(f"{establishment_id}_labor")
        establishment_labor.equation = labor_equation
        establishment_labor.initial_value = float(recipe["labor"])

        establishment_capacity = model.converter(f"{establishment_id}_capacity")
        establishment_capacity.equation = recipe["capacity"] if capacity_equation is None else capacity_equation

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
        good_to_sector = {}
        for e in establishments:
            good_to_sector[e["recipe"]["output_good"]] = e["sector"]

        # 2026/09/24: 같은 sector에 사업장이 여러 개여도 전부 반영하고, 중복은 제거한다.
        targets = []
        for e in establishments:
            if e["sector"] == sector_id:
                targets.append(e)

        influenced_by = []
        my_output_goods = []
        for t in targets:
            for good in t["recipe"]["inputs"]:
                if good in good_to_sector and good_to_sector[good] not in influenced_by:
                    influenced_by.append(good_to_sector[good])
            my_output_goods.append(t["recipe"]["output_good"])

        influences = []
        for e in establishments:
            for good in e["recipe"]["inputs"]:
                if good in my_output_goods and e["sector"] not in influences:
                    influences.append(e["sector"])

        return {
            "sector_id": sector_id,
            "influenced_by": influenced_by,
            "influences": influences,
        }

    def sector_summary(self, sector_id: str, establishments: list):
        """
        2026/09/24: plan10(크기/위치)과 APIPlan(사업장 수, 종사자 수, 생산액) 반영.
        sector_link처럼 establishment들로부터 계산되는 조회용.
        production_capacity는 실제 생산액이 아니라 최대생산량 합이다.
        """
        count = 0
        locations = []
        labor = 0
        production_capacity = 0
        for e in establishments:
            if e["sector"] == sector_id:
                count += 1
                locations.append((e["posx"], e["posy"]))
                labor += e["recipe"]["labor"]
                production_capacity += e["recipe"]["capacity"]

        return {
            "sector_id": sector_id,
            "establishment_count": count,
            "locations": locations,
            "labor": labor,
            "production_capacity": production_capacity,
        }
