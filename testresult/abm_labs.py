import numpy as np
import pandas as pd

from BPTK_Py import Agent, Model, SimultaneousScheduler, AgentDataCollector, Event


class Company(Agent):

    def initialize(self):
        self.agent_type = "company"
        self.set_property("money", {"type": "Double", "value": 100})

        self.register_event_handler(
            ["active"],          # 이벤트를 받을 수 있는 상태
            "payment",           # 이벤트 이름
            self.receive_payment
        )

    def receive_payment(self, event):
        self.money += event.data["amount"]

    def act(self, time, round_no, step_no):
        # 첫 번째 회사가 최초 한 번만 다른 회사에 10을 송금
            if self.id == 1 and time == 10:
                receiver_id = self.model.agent_ids("company")[1]

                self.money -= 30

                self.model.enqueue_event(
                    Event(
                        name="payment",
                        sender_id=self.id,
                        receiver_id=receiver_id,
                        data={"amount": 10}
                    )
                )


class CountryModel(Model):

    def __init__(self):

        super().__init__(
            starttime=0,
            stoptime=10,
            dt=1,
            scheduler=SimultaneousScheduler(),
            data_collector=AgentDataCollector()
        )

        self.register_agent_factory(
            "company",
            lambda agent_id, model, properties:
                Company(agent_id, model, properties)
        )

        self.create_agents({"name": "company", "count": 10})

model = CountryModel()
model.run_specs(0, 10, 1)
model.run()

for agent in model.agents:
    print(agent.money)