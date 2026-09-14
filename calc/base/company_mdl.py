from BPTK_Py import Model
from BPTK_Py import sd_functions as sd

import numpy as np

class CompanySDModel:
    
    def __init__(self, resource_price, sell_price, product_count) -> None:
        """
        - 원자재값
        - 판매가
        - 몇개 생산?
        """
        
        self.resource_price = resource_price
        self.sell_price = sell_price
        self.product_count = product_count
        
    # 2026/09/14 기업이 물리적 물건을 생산하는 함수.
    def production_func(self, model: Model):
        
        # 몇개 생산하는지.
        # 2026/09/14: country_mdl.py와 하나의 Model로 연동할 때 이름이 겹치지 않도록 company_production으로 명명
        production = model.stock("company_production")
        
        # 2026/09/14일 기준으로 일단은 하드코딩
        production.equation = self.product_count
        
        return production
        
    # 몇개를 판매할껀지. 일단 09/14 기준으로는 random을 사용하겠음.
    def sell_func(self, model: Model):

        # 2026/09/14: country_mdl.py와 하나의 Model로 연동할 때 이름이 겹치지 않도록 company_sell로 명명
        sell = model.converter("company_sell")
        sell.equation = sd.Random(1, 1000000)
        
        return sell
    
    # 최종이익 관련 함수.
    def profit_func(self, model: Model, sell, production):
        
        profit = model.converter("profit")
        profit.equation = sell * production
        
        return profit
    
    def profit_for_wage(self, model: Model, profit):

        wage = model.converter("wage")
        # 2026/09/14: 일단 이익의 30%를 임금 총액으로 배분 (하드코딩, 추후 근로자 수 반영해서 1인당 임금으로 확장 필요)
        wage.equation = profit * 0.3

        return wage

    def companyRun(self):

        model = Model(
            starttime=0.0,
            stoptime=5.0,
            dt=1.0,
            name="CompanyModel",
        )

        production = self.production_func(model)
        sell = self.sell_func(model)
        profit = self.profit_func(model, sell, production)
        wage = self.profit_for_wage(model, profit)

        df = model.simulate(equations=[
            "company_production",
            "company_sell",
            "profit",
            "wage"
        ])

        print_company_result(df)

        return model


# companyRun의 시뮬레이션 결과(DataFrame)를 JSON 스타일로 출력하는 함수.
def print_company_result(df):
    
    df = df.round().astype(int)
    df.index = df.index.round().astype(int)

    print(df.reset_index().to_json(
        orient="records",
        indent=2,
        force_ascii=False,
    ))


if __name__ == "__main__":
    CompanySDModel(
        resource_price=10.0,
        sell_price=100.0,
        product_count=50.0,
    ).companyRun()