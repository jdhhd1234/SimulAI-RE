import numpy as np
import pandas as pd

import random

from BPTK_Py import Model
from BPTK_Py import sd_functions as sd

"""
1. 무엇이 쌓이는가? → Stock
2. 무엇 때문에 늘고 줄어드는가? → Flow
3. 흐름을 결정하는 조건은 무엇인가? → Converter
4. 고정된 설정값은 무엇인가? → Constant
"""

'''def market_demand(start: int, end: int):
    return random.randrange(start, end)'''

class MainModel:
    def __init__(
        self,
        cash_init,
        debt_init,
        workers,
        origin_price,
        sell_price,
        deltatime,
        stoptime
    ):
        self.cash_init = cash_init       # 현금보유 초기 가격
        self.debt_init = debt_init       # 부채 초기 가격

        self.workers = workers

        self.origin_price = origin_price # 원가격 즉 생산하는데 쓰인 값
        self.sell_price = sell_price     # 판매가격

        self.deltatime = deltatime       # 델타타임
        self.stoptime = stoptime         # 멈추는 타이밍    

    def _create_cash_section(self, model):
        # 현금관련 메인쪽
        cash = model.stock("cash")
        debt = model.stock("debt")

        cash.initial_value = self.cash_init
        debt.initial_value = self.debt_init

        cash_ratio = model.converter("cash_ratio")
        cash_ratio.equation = debt / sd.max(cash, 0.0001)

        return cash, debt

    def _create_workforce_section(self, model):
        # 취업 해고 고용관련
        workers = model.stock("workers") # 근로자 수
        workers.initial_value = float(self.workers)

        ## 고용은 회사이익이 늘어나면 늘어 날수록 그리고 주문많아질수록 고용
        hiring = model.flow("hiring")  # 고용
        layoffs = model.flow("layoffs") # 해고

        return workers, hiring, layoffs

    def _connect_workforce_section(
        self,
        workers,
        hiring,
        layoffs,
        profit,
        debt
    ):
        ## 공식은 일단 단순히 부채보다 많으면 하는걸로 일단 단순히
        hiring.equation = profit > debt

        ## 해고는 적자에다가 부채까지 많으면 하는걸로 일단 단순히
        layoffs.equation = profit < debt

        workers.equation = hiring - layoffs

    def _create_production_section(self, model, workers):
        # 생산관련
        factory_count = model.converter("factory_count") # 공장수

        ## 생산량은 실판매가 얼마 됐는지에 따라서 조절한다
        factory_production = model.flow("factory_production") # 생산량

        ## self.labor_count / x 여기서 X가 공장수임 공장수는 이익보고 따져야 하는데 일단 이렇게 x로 한다
        factory_count.equation = workers / 100

        ## 기업이 몇게 생산할껀지 공식
        ## 일단 중형에서는 1개당 300개 생산으로 고정 (매달)
        ## factory_count * x / 여기서 x도 나중에 판매량 따라서 조절
        factory_production.equation = factory_count * 300

        return factory_production

    def _create_market_section(self, model, factory_production):
        # 판매 수요 관련 / 시장
        inventory = model.stock("inventory") # 재고

        ## 현재 제고
        inventory.equation = factory_production
        print("인벤", inventory)

        demand = model.converter("demand") # 수요
        sales = model.flow("sales") # 판매요구

        ## 수요 공식 / 일단 임시로 500고정 / 500이 고객임
        ## 나중에 이건 ABM으로 뺼 예정
        demand.equation = random.randint(1, 1500)

        ## 판매 재고 공식 / 판매는 / 판매 = 수요
        sales.equation = sd.min(demand, inventory)
        inventory.equation = factory_production - sales

        return sales

    def _create_profit_section(self, model, sales):
        # 수익 관련
        revenue = model.converter("revenue")

        ## 최종 수익 공식
        revenue.equation = sales * self.sell_price

        # 마케팅및 연구, 임금관련

        ## 공식 연구비용 = 전체비용 
        ## 연구비용은 일단 10%
        ## 이거 일단 연구 마케팅 임금도 나중에는 AI가 하는걸로
        research_cost = model.converter("research_cost")
        research_cost.equation = revenue * (10 / 100)

        ## 마케팅 비용
        ## 이거는 10% 정도
        marketing_cost = model.converter("marketing_cost")
        marketing_cost.equation = revenue * (10 / 100)

        ## 임금관련 
        ## 이거는 20% 정도
        wage_cost = model.converter("wage_cost")
        wage_cost.equation = revenue * (20 / 100)

        # 최종적으로 남은돈
        profit = model.converter("profit")
        profit.equation = (
            revenue
            - research_cost
            - marketing_cost
            - wage_cost
        )

        return profit

    def CompanyModel(self):
        """기업경제시뮬(중형)"""
        model = Model(
            starttime=0.0,
            stoptime=self.stoptime,
            dt=self.deltatime,
            name="Company Model",
        )

        cash, debt = self._create_cash_section(model)
        workers, hiring, layoffs = self._create_workforce_section(model)
        factory_production = self._create_production_section(model, workers)
        
        sales = self._create_market_section(model, factory_production)
        
        profit = self._create_profit_section(model, sales)
        self._connect_workforce_section(   
            workers,
            hiring,
            layoffs,
            profit,
            debt
        )
        cash.equation = profit

        return model

'''    def countryEcnomic(self):
        """이거는 국가경제시뮬레이션"""
        model_country = Model(  
            starttime=0.0,
            stoptime=self.stoptime,
            dt=self.deltatime,
            name="country Model",
        )'''

if __name__ == "__main__":
    
    sim_data = MainModel(
        cash_init=1000.0, 
        debt_init=2000.0, 
        origin_price=250.0,
        sell_price=500.0,
        workers=120,
        deltatime=0.1,
        stoptime=5.0
    )
    
    economic_model = sim_data.CompanyModel()
    
    print("[CLI] 시뮬레이션 엔진 가동 및 결과 연산...")
    df = economic_model.simulate(equations=[
        "cash", 
        "debt", 
        "cash_ratio", 
        "factory_count",
        "factory_production",
        "inventory",
        "sales",
        "demand",
        "revenue",
        "research_cost",
        "marketing_cost",
        "wage_cost",
        "profit"
    ])
    print(df)