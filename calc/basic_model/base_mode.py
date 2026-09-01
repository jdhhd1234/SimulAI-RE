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

class CompanyModel:
    def __init__(
        self,
        cash_init,
        previous_demand,
        workers,
        workers_wage,
        production_per_worker,
        origin_price,
        sell_price,
        deltatime,
        stoptime
    ):
        self.cash_init = cash_init       # 현금보유 초기 가격
        self.debt_init = 1.0             # 부채 초기 가격

        self.previous_demand = previous_demand

        self.workers = workers   # 근로자 몇명인지
        self.workers_wage = workers_wage
        self.production_per_worker = production_per_worker # 근로자 한명당 몇개 생성 하는지 / 즉 capacity비슷한거

        self.origin_price = origin_price # 원가격 즉 생산하는데 쓰인 값
        self.sell_price = sell_price     # 판매가격

        self.deltatime = deltatime       # 델타타임
        self.stoptime = stoptime         # 멈추는 타이밍

        
        self.consumption = np.random.randint(1, 1000) # 소비 / 일단 랜덤으로 한다. 나중에는 ABM으로 처리
        
    def _create_cash_section(self, model):
        # 현금관련 메인쪽
        cash = model.stock("cash")
        debt = model.stock("debt")
        
        cash.initial_value = self.cash_init
        
        debt.initial_value = self.debt_init

        cash_ratio = model.converter("cash_ratio")
        cash_ratio.equation = debt / sd.max(cash, 0.0001)

        return cash, debt

    def _create_workforce_part_hiring(self, model, demand, production_per_worker):
        # 고용관련

        ## 고용은 기본적으로 수요가 증가하고 이익이 많을떄 고용하는 흐름을 가진다
        hiring = model.flow("hiring")  # 고용

        ## 주문이 많아지면 많아 질수록 고용은 점점 증가한다
        hiring.equation = sd.sqrt(sd.max(0, demand - production_per_worker))

        return hiring

    def _create_workforce_part_layoffs(self, model, demand, debt):
        # 해고관련

        ## 해고는 기본적으로 부채가 커지고 수요가 적어지면 해고한다
        ## 해고는 부채가 너무 심각할떄 그리고 계속 적자일떄
        layoffs = model.flow("layoffs") # 해고
        order_shortage = model.flow("order_shortage")
        debt_pressure = model.flow("debt_pressure")
                
        ## 주문 감소압력
        order_shortage.equation = sd.max((100 - demand) / 100, 0)

        ## 부채 증가 압력
        ## 일단 지금 debt가 0 이라서 FSM으로 적자 12000원 되면 대출 하는걸로
        ## debt_pressure(부채압박)은 적자가 점점 생길떄 증가하는걸로
        debt_pressure.equation = sd.max(debt / 1000, 0)

        ## 주문이 점점 적어지고 부채가 점점 증가할떄 해고는 증가한다
        
        ## 지금 order_shortage랑 debt_pressure이 재대로 작동을 안함
        layoffs.equation = (0.5 * order_shortage + 0.5 * debt_pressure)

        ## 일단 임시 디버깅으로 order_shortage, debt_pressure 추가
        return layoffs, order_shortage, debt_pressure

    def _create_workforce_section(self, model, demand, debt, profit):
        # 취업 해고 고용관련
        workers = model.stock("workers") # 근로자 수
        workers.initial_value = self.workers

        hiring = self._create_workforce_part_hiring(model, demand, self.production_per_worker)
        layoffs, order_shortage, debt_pressure = self._create_workforce_part_layoffs(model, demand, debt)
        workers.equation = hiring - layoffs

        # 디버깅으로 order_shortage, debt_pressure 이거 추가
        return workers, hiring, layoffs, order_shortage, debt_pressure

    def _create_production_section(self, model, workers):
        # 생산관련
        factory_count = model.converter("factory_count") # 공장수

        ## 생산량은 실판매가 얼마 됐는지에 따라서 조절한다
        factory_production = model.flow("factory_production") # 생산량

        ## 'self.labor_count / x' 여기서 X가 공장수임 공장수는 이익 수요을 보고 따져야 하는데 일단 이렇게 x로 한다
        ## 겪고있는 문제: 생산량과 수익에 관련하여 어떻게 공장갯수를 정하는가?
        factory_count.equation = workers / 100

        ## 기업이 몇게 생산할껀지 공식
        ## 일단 중형에서는 1개당 300개 생산으로 고정 (매달)
        ## factory_count * x / 여기서 x도 나중에 판매량 따라서 조절

        ## 2026/08/28
        ## 이거는 수요를 보고 결정한다
        factory_production.equation = workers * self.production_per_worker

        return factory_production

    def _create_market_demand_part(self, model):
        previous_demand = model.converter("previous_demand") # 이전 수요 / 일단은 초기수요로 하려고 한다
        previous_demand.equation = sd.delay(model, model.converter("demand"), 
                                            float(self.deltatime), float(self.previous_demand))
        return previous_demand

    def _create_market_section(self, model, factory_production):
        # 판매 수요 관련 / 시장 previous_demand
        inventory = model.stock("inventory") # 재고

        demand = model.converter("demand") # 수요
        sales = model.flow("sales")        # 실제 팔린거

        # 그전 수요
        previous_demand_data = self._create_market_demand_part(model)

        ## 수요 공식
        ## 나중에 이건 ABM으로 뺼 예정
        ## 일단 지금은 random쓴다
        # 수요 = 이전 수요의 영향 + 무작위 충격
        demand.equation = sd.max(sd.round(previous_demand_data + sd.normal(0.0, 5.0), 0), 0)

        ## 판매 재고 공식 / 판매는 / 판매 = 수요
        sales.equation = sd.min(demand, inventory)
        inventory.equation = factory_production - sales

        return sales, demand

    def _create_profit_section(self, model, sales, workers):
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
        wage_cost = model.converter("workers_wage")
        wage_cost.initial_value = self.workers_wage
        wage_cost.equation = self.workers_wage * self.workers

        # 최종적으로 남은돈
        profit = model.converter("profit")
        profit.equation = (
            revenue
            - sales * self.origin_price
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
        
        # 나중에 이 구조는 생각조금 해보겠음
        demand = model.converter("demand")
        profit = model.converter("profit")
        
        workers, hiring, layoffs, order_shortage, debt_pressure = self._create_workforce_section(model, demand, debt, profit)
        factory_production = self._create_production_section(model, workers)
        
        # 고용 로직은 나중에 개선
        # 현재는 기업 모델 단순화를 위해 고용 중지

        ## hiring는 고용이 증가하고 돈이 많을떄 한다.
        
        sales, demand = self._create_market_section(model, factory_production)
        profit = self._create_profit_section(model, sales, workers)
        
        ## 일단은 단순 현금은 profit와 같다로 한다
        cash.equation = profit

        return model
        

def mainRun(Pretty: bool, Integer: bool = True):
    maindata = []
    sim_data = CompanyModel(
        cash_init=1000.0, 
        previous_demand=random.randint(1, 1000),
        origin_price=250.0,
        sell_price=500.0,  
        workers=120.0,
        workers_wage=2500,
        production_per_worker=10,
        deltatime=1.0,
        stoptime=12.0
    )
    
    economic_model = sim_data.CompanyModel()
    
    print("[CLI] 시뮬레이션 엔진 가동 및 결과 연산...")
    df = economic_model.simulate(equations=[
        "cash",
        "debt",
        "workers",
        "profit",
        "revenue",
        "demand",
        "previous_demand",
        "hiring",
        "layoffs",
        "order_shortage",
        "debt_pressure",
    ])

    if Integer is True:
        df = df.round().astype(int)
        
        #round Error무시해도 괜찮음
        df.index = df.index.round().astype(int)
    
    for time, row in df.iterrows():
        maindata.append({
            # Time Error은 무시해도 괜찮음.
            "time": float(time),
            "cash": float(row["cash"]),
            "debt": float(row["debt"]),
            "workers": float(row["workers"]),
            "profit": float(row["profit"]),
            "revenue": float(row["revenue"]),
            "demand": float(row["demand"]),
            "previous_demand": float(row["previous_demand"]),
            "hiring": float(row["hiring"]),
            "layoffs": float(row["layoffs"]),
            "order_shortage": float(row["order_shortage"]),
            "debt_pressure": float(row["debt_pressure"]),
        })

    if Integer is True:
        maindata = [{key: int(round(value)) for key, value in row.items()} for row in maindata]
        
    if Pretty is True:
        return df.reset_index().to_json(
            orient="records",
            indent=2,
            force_ascii=False,
        )
    
    return maindata


if __name__ == "__main__":
    print(mainRun(True))
