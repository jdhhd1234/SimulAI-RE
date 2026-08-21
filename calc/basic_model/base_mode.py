import numpy as np

from BPTK_Py import Model
from BPTK_Py import sd_functions as sd

        
class InitValue:
    def __init__(
        self,
        population_initial_value,
        capital_initial_value,
        birth_rate_equation,
        death_rate_equation,
        labor_participation_equation,
        labor_productivity_equation,
        capital_productivity_equation,
        saving_rate_equation,
        depreciation_rate_equation,
    ):
        self.population_initial_value = population_initial_value
        self.capital_initial_value = capital_initial_value
        self.birth_rate_equation = birth_rate_equation
        self.death_rate_equation = death_rate_equation
        self.labor_participation_equation = labor_participation_equation
        self.labor_productivity_equation = labor_productivity_equation
        self.capital_productivity_equation = capital_productivity_equation
        self.saving_rate_equation = saving_rate_equation
        self.depreciation_rate_equation = depreciation_rate_equation
    
def TestBPTK(init: InitValue):
    """극초소형 경제시뮬"""
    model = Model(
        starttime=0.0,
        stoptime=20.0,
        dt=0.1,
        name="Simple Economic Model",
    )
    
    #Stocks 쌓이는 값들
    
    
    
    return model