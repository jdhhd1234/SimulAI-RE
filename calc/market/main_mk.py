from BPTK_Py import Model
from BPTK_Py import Agent, Event

import random

# 2026/09/10
# 시장이라는건 단순 랜덤이 아니라 여러명의 소비자가 원함 원하지않음에 따라서 결정이된다
# 일단 기업수요는 예외처리 하겠음
# 소비자들이 물건을 살지 안살지는 일단 random으로 하겠음

class MarketModel(Model):

    def instantiate_model(self):
        self.register_agent_factory(
            agent_type="consumer",
            agent_factory=lambda agent_id, model, properties: Market(agent_id, model, properties)
        )

class Market(Agent):

    def initialize(self):

        self.agent_type = "consumer"
        self.assets = 12000

        self.price = 3000

        # 일단 살지 안살지는 random으로 결정 buy or wait (2026/09/10)
    

    def act(self, time, round_no, step_no):

        self.state = random.choice(["buy", "wait"])

        if self.state == "buy":

            # 2026/09/10
            # 여기서 빠져나간돈이 기업으로 가야함
            # 근데 기업구현이 아직 안됨
            self.assets -= self.price