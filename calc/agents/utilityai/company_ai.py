import numpy as np

class CompanyCEOAI:
    def __init__(self, debt, cash, workers, profit, previous_demand) -> None:
        self.debt = debt
        self.cash = cash
        self.workers = workers
        self.profit = profit
        self.previous_demand = previous_demand
    
    def debt_score(self):
        """기업 부채 점수 (UtilityAI용)"""
        # 현금이 부족하고 수요가 있으면 부채 발행을 선택한다.
        cash_score = 1 - min(max(self.cash / 1000, 0), 1)
        profit_score = min(max(-self.profit / 1000, 0), 1)
        demand_score = min(max(self.previous_demand / 1000, 0), 1)

        return (cash_score + profit_score + demand_score) / 3

    def hire_score(self):
        """기업 고용 점수 (UtilityAI용)"""
        demand_score = min(max(self.previous_demand / max(self.workers * 10, 1), 0), 1)
        profit_score = min(max(self.profit / 1000, 0), 1)

        return (demand_score + profit_score) / 2

    def layoff_score(self):
        """기업 해고 점수 (UtilityAI용)"""
        debt_score = min(max(self.debt / max(self.cash, 1), 0), 1)
        profit_score = min(max(-self.profit / 1000, 0), 1)
        demand_score = 1 - min(max(self.previous_demand / 1000, 0), 1)

        return (debt_score + profit_score + demand_score) / 3

    def production_score(self):
        """기업 생산 점수 (UtilityAI용)"""
        return min(max(self.previous_demand / max(self.workers * 10, 1), 0), 1)

    def decide_action(self):
        """Utility가 가장 높은 기업 행동을 선택한다."""
        actions = ["hire", "layoff", "production", "debt"]
        scores = [
            self.hire_score(),
            self.layoff_score(),
            self.production_score(),
            self.debt_score(),
        ]

        return actions[self.high_score_select(scores)]
    
    def high_score_select(self, scores: list) -> int:
        """List중에서 가장 높은거 고르는 함수"""
        return int(np.argmax(scores))