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

    def population_func(self, model: Model):
        population = model.stock("population")
        population.initial_value = self.population

        return population

    def tax_rate_func(self, model: Model):
        tax_rate = model.converter("tax_rate")
        tax_rate.equation = self.tax_rate

        return tax_rate

    def gdp_func(self, model: Model):
        gdp = model.converter("gdp")
        gdp.equation = self.gdp

        return gdp

    def tax_revenue_func(self, model: Model, gdp, tax_rate):
        tax_revenue = model.converter("tax_revenue")
        tax_revenue.equation = gdp * tax_rate

        return tax_revenue

    def countryModel(self):

        model = Model(
            starttime=0.0,
            stoptime=5.0,
            dt=0.1,
            name="CountryModel"
        )

        population = self.population_func(model)
        gdp = self.gdp_func(model)
        tax_rate = self.tax_rate_func(model)

        tax_revenue = self.tax_revenue_func(
            model,
            gdp,
            tax_rate
        )

        return model

def mainRun(Pretty: bool, Integer: bool = True, company=None):
    maindata = []
    sim_data = company or CountryEconomic(
        gdp=100000.0,
        population=1200000.0,
        tax_rate=12.0,
        resource_power=7.0
    )
    
    economic_model = sim_data.countryModel()
    
    print("[CLI] 시뮬레이션 엔진 가동 및 결과 연산...")
    df = economic_model.simulate(equations=[
        "population",
        "tax_rate",
        "gdp",
        "tax_revenue"
    ])

    if Integer is True:
        df = df.round().astype(int)
        
        #round Error무시해도 괜찮음
        df.index = df.index.round().astype(int)
    
    for time, row in df.iterrows():
        maindata.append({
            # Time Error은 무시해도 괜찮음.
            "time": float(time),
            "population": float(row["population"]),
            "tax_rate": float(row["tax_rate"]),
            "gdp": float(row["gdp"]),
            "tax_revenue": float(row["tax_revenue"]),
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