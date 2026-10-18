import BPTK_Py
from BPTK_Py import Agent
from BPTK_Py import Event
from BPTK_Py import DataCollector
from BPTK_Py import SimultaneousScheduler

# 이 코드는 ABM바탕으로 하는 기업이 자신이 가진 현금을 바탕으로 공장에서 나온 물건을 구입하는것이다.
# 2026/10/18: 일단 현금은 하드코딩하고. 공장에서 나온 물건도 하드코딩 하는걸로 
class CompanyConsumer(Agent):

    def initialize(self):
        self.agent_type = "company"
        self.state = "idle"

        self.cash = 120_000_000

        # 2026/10/18
        # 여기서는 이제 Lua랑 Python이랑 연동하는코드로 할꺼임(이쪽은 Claude Code랑 협력해서.)
        # 일단은 iron이랑 이런건 하드코딩
        self.objects = [
            {"name": "iron", "price": 120_000},
        ]

        return super().initialize()

    def act(self, time, round_no, step_no):

        # 지금코드는 일단 그냥 현금 다 써서 물건 사는거뿐임.
        for obj in self.objects:
            price = obj["price"]

            if price <= 0:
                continue

            quantity = int(self.cash // price)

        return super().act(time, round_no, step_no)


if __name__ == "__main__":
    from BPTK_Py import Model

    model = Model(starttime=0.0, stoptime=5.0, dt=1.0, name="company_test")

    agent = CompanyConsumer(0, model, {})
    agent.initialize()

    print(f"초기 현금: {agent.cash:,}")

    for t in range(10):
        agent.act(t, t, 0)
        print(f"스텝 {t + 1}: 현금 {agent.cash:,}")