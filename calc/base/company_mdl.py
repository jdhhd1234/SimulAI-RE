from BPTK_Py import Model
from BPTK_Py import sd_functions as sd

import numpy as np

class SectorKind:
    
    def __init__(self, energy_score, iron_score, electronic_score, car_score) -> None:
        self.energy = energy_score
        self.iron = iron_score
        self.electronic = electronic_score
        self.car = car_score
        
class SectorFactoryModel:
        
    # 2026/09/20: 공장이 물건을 어느정도 생산하는지. 일단은 하드코딩.
    def factory_production(self, model: Model, production):
        
        factory_production = model.converter("factory_production")
        factory_production.equation = production
        
        return factory_production
    
    # 2026/09/20: 공장이 속해있는 sector
    def sector_main(self, model: Model):
        pass
        

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
    SectorFactoryModel().companyRun()