import numpy as np
import pandas as pd

import random

from dataclasses import dataclass

from BPTK_Py import Model
from BPTK_Py import sd_functions as sd

# 국가경제
class CountryEconomic:
    def __init__(
        self,
        gdp,
        population,
        tax_rate,
        resource_power
    ) -> None:
        self.gdp = gdp
        self.population = population
        self.tax_rate = tax_rate
        self.resource_power = resource_power

    def gdp_func(self, model: Model, sell):
        """GDP는 국내총생산이라서 여기에 뭐 국내생산에 다 들어감"""
        gdp = model.converter("gdp")
        gdp.equation = sell * self.tax_rate

        return gdp

    def tax_revenue_func(self, model: Model, gdp, tax_rate):
        tax_revenue = model.converter("tax_revenue")
        tax_revenue.equation = gdp * tax_rate

        return tax_revenue
    
    def hire_func(self, model: Model, population):
        # 일단 지금은 복잡하게 말고 random으로 처리(# 2026/09/07)
        hire = model.flow("hire")
        hire.equation = np.random.randint(1, population)
        
        return hire
    
    def labor_func(self, model: Model, hire):
        
        labor = model.stock("labor")
        labor.equation = hire
        
        return labor
    
    def production_func(self, model: Model, labor_count):
        
        # 노동자 한명당 일단 5개씩 생산
        production = model.stock("production")
        production.equation = labor_count * 5
        
        return production
    
    def sell_func(self, model: Model, sell_price, production):
        
        sell = model.converter("sell")
        sell.equation = production * sell_price
        
        return sell

    def countryModel(self):

        model = Model(
            starttime=0.0,
            stoptime=5.0,
            dt=1.0,
            name="CountryModel"
        )
        
        
        hire = self.hire_func(model, self.population)
        labor = self.labor_func(model, hire)
        production = self.production_func(model, labor)
        sell = self.sell_func(model, 1000, production)
        
        gdp = self.gdp_func(model, sell)

        tax_revenue = self.tax_revenue_func(
            model,
            gdp,
            self.tax_rate
        )

        return model

def mainRun(Pretty: bool, Integer: bool = True, company=None):
    maindata = []
    sim_data = company or CountryEconomic(
        gdp=1000.0,
        population=1200.0,
        tax_rate=0.12,
        resource_power=7.0
    )
    
    economic_model = sim_data.countryModel()
    
    print("[CLI] 시뮬레이션 엔진 가동 및 결과 연산...")
    df = economic_model.simulate(equations=[
        "gdp",
        "tax_revenue",
        "hire",
        "labor",
        "production",
        "sell"
    ])

    if Integer is True:
        df = df.round().astype(int)
        
        #round Error무시해도 괜찮음
        df.index = df.index.round().astype(int)
    
    for time, row in df.iterrows():
        maindata.append({
            # Time Error은 무시해도 괜찮음.
            "time": float(time),
            "gdp": float(row["gdp"]),
            "tax_revenue": float(row["tax_revenue"]),
            "hire": float(row["hire"]),
            "labor": float(row["labor"]),
            "production": float(row["production"]),
            "sell": float(row["sell"]),
        })

    if Integer is True:
        maindata = [{key: int(round(value)) if isinstance(value, (int, float)) else value for key, value in row.items()} for row in maindata]
        
    if Pretty is True:
        return df.reset_index().to_json(
            orient="records",
            indent=2,
            force_ascii=False,
        )
    
    return maindata


if __name__ == "__main__":
    print(mainRun(True))