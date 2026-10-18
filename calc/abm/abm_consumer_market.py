from BPTK_Py import Agent
from enum import Enum
import random

# 이 파일은 ABM즉 Agent-Based-Model을 활용하는것이다.
# 1. 일단 자신의 재산에 따라 소비할지 안할지 결정만 하는 단순AI를 만드는것이다. FSM

class ConsumerState(Enum):
    SAVING = "saving"
    NORMAL = "normal"
    SPENDING = "spending"

class Consumer(Agent):
    """
    state: saving(절약) / normal(보통) / spending(소비)
    """

    def initialize(self, money: float, income: float, fixcost: float):        
        self.agent_type = "consumer"
        self.state = ConsumerState.NORMAL

        self.money = money
        self.income = income
        self.fixcost = fixcost

        return super().initialize()

    def act(self, time, round_no, step_no):

        if self.income < self.fixcost:
            self.state = "saving"

        if self.income > self.fixcost:
            self.state = "spending"

        return super().act(time, round_no, step_no)

    # 여기에 이제 def handle을 사용해서 위에 있는 FSM의 self.state = "spending" 이런쪽이랑 연결하기.