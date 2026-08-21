import numpy as np

class BaseModel:
    def __init__(
        self, 
        population: int,
        factories: int,
        resources: int,
    ):
        self.population = population
        self.factories = factories
        self.resources = resources
        self.total_score = 100
        
    def industry_power(self):
        log_population = np.log(self.population)
        
        if (self.factories and self.resources < log_population):
            self.total_score = self.total_score - 5
        elif np.any(np.rtol(self.factories, log_population, self.resources)):
            self.total_score = self.total_score + 10
            
        return self.total_score