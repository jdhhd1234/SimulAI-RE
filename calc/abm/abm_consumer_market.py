from BPTK_Py import Agent
from BPTK_Py import Event
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

        self.register_event_handler(list(ConsumerState), "normal_event", self.handle_normal_event)
        self.register_event_handler(list(ConsumerState), "spending", self.handle_spending_event)
        self.register_event_handler(list(ConsumerState), "saving", self.handle_saving_event)

        return super().initialize()

    # 여기에 이제 def handle을 사용해서 위에 있는 FSM의 self.state = "spending" 이런쪽이랑 연결하기.

    def handle_normal_event(self, event):
        self.state = ConsumerState.NORMAL

    def handle_spending_event(self, event):
        self.state = ConsumerState.SPENDING

    def handle_saving_event(self, event):
        self.state = ConsumerState.SAVING

    def act(self, time, round_no, step_no):

        # FSM
        if self.income < self.fixcost:
            event_name = "saving"
        elif self.income > self.fixcost:
            event_name = "spending"
        else:
            event_name = "normal_event"

        self.receive_instantaneous_event(Event(event_name, self.id, self.id))

        return super().act(time, round_no, step_no)