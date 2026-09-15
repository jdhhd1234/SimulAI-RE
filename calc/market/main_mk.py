from BPTK_Py import Model
from BPTK_Py import Agent, Event
from BPTK_Py import sd_functions as sd

import random

# 2026/09/10
# 시장이라는건 단순 랜덤이 아니라 여러명의 소비자가 원함 원하지않음에 따라서 결정이된다
# 일단 기업수요는 예외처리 하겠음
# 소비자들이 물건을 살지 안살지는 일단 random으로 하겠음

class BasicConsumer(Agent):

    def initialize(self):
        self.agent_type = "consumer"
        self.state = "idle"
        self.set_property("remaining_effort", {"type": "Double", "value": self.effort})

        # 2026/09/15: 이거는 소비자가 구입을 하지도 사지도 않는 즉 대기상태.
        self.register_event_handler(["idle"], "consumer_idle", self.consumer_idle)

        # 2026/09/15: 이거는 소비자가 구입을 하는상황.
        self.register_event_handler(["buy"], "consumer_buy", self.consumer_buy)

        return super().initialize()

    def randomMoney(self):
        # 2026/09/15: 랜덤으로 돈을 소비자한테 주는 함수.
        return sd.Random(1, 10000)

    def consumer_idle(self, event):
        # 아무것도 안하는 상태: 소비도 구입도 하지 않고 state를 "idle"로 유지한다.
        return

    def consumer_buy(self, event):
        pass
