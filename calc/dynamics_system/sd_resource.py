from dataclasses import dataclass

@dataclass
class Resource:
    # Korea: 매장량
    reserves: int

    # Korea: 생산량
    production: int

    # Korea: 생산비용
    production_cost: float