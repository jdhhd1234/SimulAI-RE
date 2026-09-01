import numpy as np
from scipy.stats import iqr

class CompanyCEOAI:
    def __init__(self, debt, cash, workers, profit, previous_demand) -> None:
        self.debt = debt
        self.cash = cash
        self.workers = workers
        self.profit = profit
        self.previous_demand = previous_demand
    
    def debt_score(self):
        """기업 부채 점수 (UtilityAI용)"""
        
        _debt_score = 
    
    def high_score_select(self, scores: list) -> int:
        """List중에서 가장 높은거 고르는 함수"""
        return int(np.argmax(scores))