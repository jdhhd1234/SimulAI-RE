from BPTK_Py import Agent
import random

# 이 파일은 ABM즉 Agent-Based-Model을 활용하여 100%의 인구를 10%씩 계층을 분리하여 소비자묶음으로 움직이는것이다.
# 1. 일단 정규분포를 이용하여 중산층을 제일 많이 하고 저소득층과 고소득층 재벌을 적게한다.
# 2. 이제 10%씩 그룹을 나눈뒤에. FSM즉 유한체 바탕으로 소비자AI를 만든다.

# FSM 상태별 소득 대비 소비 비율
CONSUME_RATE = {
    "saving": 0.5,
    "normal": 0.8,
    "spending": 1.1,
}


class ConsumerAgent(Agent):
    """
    10% 인구 그룹 하나를 대표하는 소비자 묶음.
    state: saving(절약) / normal(보통) / spending(소비)
    """

    def initialize(self):
        self.agent_type = "consumer"
        self.state = "normal"

    def next_state(self):
        # 보유 현금이 소득 대비 얼마나 되는지로 상태 전이
        cash = self.get_property_value("cash")
        income = self.get_property_value("income")

        # Consumer FSM
        if cash < income:
            return "saving"
        if cash > income * 5:
            return "spending"
        return "normal"

    def act(self, time, round_no, step_no):
        income = self.get_property_value("income")
        cash = self.get_property_value("cash") + income

        self.set_property_value("cash", cash)
        self.state = self.next_state()

        consume = min(cash, income * CONSUME_RATE[self.state])

        self.set_property_value("cash", cash - consume)
        self.set_property_value("consume", consume)


    def make_consumer_groups(self, model, population=10000, mean=300.0, std=100.0, groups=10):
        """
        정규분포로 인구 소득을 뽑고 낮은 순으로 정렬하여 10%씩 묶어 ConsumerAgent를 만든다.
        """
        incomes = sorted(
            max(0.0, random.gauss(mean, std)) 
            for _ in range(population)
        )
        
        size = population // groups
        agents = []

        for i in range(groups):
            chunk = incomes[i * size:(i + 1) * size]
            avg_income = sum(chunk) / len(chunk)
            agent = ConsumerAgent(i, model, {
                "decile": {"type": "Integer", "value": i + 1},
                "population": {"type": "Integer", "value": len(chunk)},
                "income": {"type": "Double", "value": avg_income},
                "cash": {"type": "Double", "value": avg_income * 2},
                "consume": {"type": "Double", "value": 0.0},
            })
            agent.initialize()
            agents.append(agent)

        return agents