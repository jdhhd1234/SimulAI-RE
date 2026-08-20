import numpy as np
import random
from inspect import signature

#[value, min, max]
class Country:
    def __init__(
        self, 
        name, 
        resource: int, 
        manpower: int, 
        worker: int,
        factory: int, 
        logistic_percentage #Any Num
    ):
        self.name = name
        self.resource = resource
        self.manpower = manpower
        self.factory = factory
        self.logistic_percentage = logistic_percentage
        self.worker = worker
        
    """
    lst안에 지표별 각각의 리스트를 넣으면 정규화 해주는 함수
    """
    def minmax_norm(lst: list[list]):
        normalized = []

        for item in lst:
            value = item[0]
            min_value = item[1]
            max_value = item[2]
            
            value_log = np.log10(value)
            min_log = np.log10(min_value)
            max_log = np.log10(max_value)
            
            normalized_num = (
                (value_log - min_log)
                / (max_log - min_log)
            )

            normalized.append(float(normalized_num))
            
        return normalized
    
    def static_battle(self):
        """
        일단 지금은 단순히 정규화만 할꺼임
        """ 
        
        resource_ratio = self.resource / max(self.factory, 1)
        worker_ratio = self.worker / max(self.factory, 1)
        power_ratio = self.manpower / max(self.factory, 1)
        
        print(resource_ratio, worker_ratio, power_ratio)
        
         # 2. 공장 효율 결정
        factory_efficiency = min(
            resource_ratio,
            worker_ratio,
            power_ratio,
            1.0
        )
        
        production = self.factory * factory_efficiency
        
        '''normalized_num = Country.minmax_norm([
            self.resource,
            self.manpower,
            self.factory
        ])'''

        return production

rnd = random.randrange(1, 100)

cls = Country(
    "DD",
    1000,
    120000,
    60000,
    50,
    rnd
)

static_btl = cls.static_battle()
print(static_btl)