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

    def make_consumer_groups(self, model, population: int, mean: float, std: float, groups: int):

        if not population >= groups > 0 or std < 0:
            raise ValueError("population >= groups > 0 and std >= 0 are required")
        
        incomes = sorted(max(0.0, random.gauss(mean, std)) for _ in range(population))

        agents = []

        for i in range(groups):
            chunk = incomes[i * population // groups:(i + 1) * population // groups]

            income = sum(chunk) / len(chunk)

            agent = Consumer(i, model, {
                "decile": {"type": "Integer", "value": i + 1},
                "population": {"type": "Integer", "value": len(chunk)},
                "income": {"type": "Double", "value": income},
                "cash": {"type": "Double", "value": income * 2},
                "consume": {"type": "Double", "value": 0.0},
            })

            agent.initialize(income * 2, income, mean)

            agents.append(agent)

        return agents

    def initialize(self, money: float, income: float, fixcost: float):        
        self.agent_type = "consumer"
        self.state = ConsumerState.NORMAL
        
        self.money = money
        self.income = income
        self.fixcost = fixcost

        for state in ConsumerState:
            self.register_event_handler(list(ConsumerState), state.value, self.handle_state_event)

        return super().initialize()

    # 여기에 이제 def handle을 사용해서 위에 있는 FSM의 self.state = "spending" 이런쪽이랑 연결하기.

    def handle_state_event(self, event):
        self.state = ConsumerState(event.name)

    def act(self, time, round_no, step_no):

        # FSM AI
        if self.income < self.fixcost:
            new_state = ConsumerState.SAVING
        elif self.income > self.fixcost:
            new_state = ConsumerState.SPENDING
        else:
            new_state = ConsumerState.NORMAL

        self.decision = {
            "action": new_state.value,
            "previous_state": self.state.value,
            "income": self.income,
            "fixcost": self.fixcost,
        }

        self.receive_instantaneous_event(Event(new_state.value, self.id, self.id))

        return super().act(time, round_no, step_no)
