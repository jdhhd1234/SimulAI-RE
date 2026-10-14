# 2026/10/12: 여기에서는 이제 지표를 상세적 세부적으로 알수있는/맞추는 세팅과 sector을 바탕으로 정보를 수집할 예정.

class SystemDynamicChara:

    def __init__(self):
        # 2026/10/12: 지역(국가/도시)별 특성 정보를 계속 보관한다.
        # (SystemDynamicSector.sectors/resources와 같은 방식)

        # 어떤 지역이 있는지
        self.regions = {}

    def make_region(self, name: str):
        """
        2026/10/12: 지역을 만든다. 자원/인구/인프라는 아래 set_* 함수로 채운다.
        """
        if name not in self.regions:
            self.regions[name] = {
                "name": name,
                "resources": {},
                "population": {},
                "infrastructure": {}
            }

        return self.regions[name]

    def delete_region(self, name: str):
        return self.regions.pop(name, None)

    def get_region(self, name: str):
        return self.regions.get(name)

    def set_region_resource(self, region_name: str, resource: str, amount: float, sector):
        """
        2026/10/12: 지역에 자원이 어느정도 있는지 설정한다.
        sector(SystemDynamicSector)의 resources에 등록된 자원만 받는다.
        """
        if region_name not in self.regions:
            raise ValueError(f"Dont Exist Region: {region_name}")

        if resource not in sector.resources:
            raise ValueError(f"Dont Exist Resource: {resource}")

        amount = float(amount)

        if amount < 0:
            raise ValueError(f"{resource} amount must not be negative")

        self.regions[region_name]["resources"][resource] = amount

        return self.regions[region_name]["resources"]

    def delete_region_resource(self, region_name: str, resource: str):
        if region_name not in self.regions:
            return None

        return self.regions[region_name]["resources"].pop(resource, None)

    def set_population(
        self,
        region_name: str,
        total: int,
        growth_rate: float = 0.0,
        labor_ratio: float = 0.0
    ):
        """
        2026/10/12: 지역 인구가 어느정도인지 설정한다.
        - total: 총 인구
        - growth_rate: 인구 증가율 (0.01 = 1%)
        - labor_ratio: 노동 가능 인구 비율 (0.0 ~ 1.0)
        """
        if region_name not in self.regions:
            raise ValueError(f"Dont Exist Region: {region_name}")

        if total < 0:
            raise ValueError("Population must not be negative")

        if not 0.0 <= labor_ratio <= 1.0:
            raise ValueError("labor_ratio must be between 0 and 1")

        population = {
            "total": int(total),
            "growth_rate": float(growth_rate),
            "labor_ratio": float(labor_ratio),
            "labor_force": int(total * labor_ratio)
        }

        self.regions[region_name]["population"] = population

        return population

    def set_infrastructure(
        self,
        region_name: str,
        power: float = 0.0,
        transport: float = 0.0,
        water: float = 0.0,
        telecom: float = 0.0
    ):
        """
        2026/10/12: 지역 인프라가 어느정도인지 설정한다.
        각 수치는 0.0 ~ 1.0 (보급/수준 비율)
        """
        if region_name not in self.regions:
            raise ValueError(f"Dont Exist Region: {region_name}")

        infrastructure = {
            "power": float(power),
            "transport": float(transport),
            "water": float(water),
            "telecom": float(telecom)
        }

        for key, value in infrastructure.items():
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{key} must be between 0 and 1")

        self.regions[region_name]["infrastructure"] = infrastructure

        return infrastructure