import numpy as np
import pandas as pd

from BPTK_Py import Agent, Model

# 이거는 일단 Country루프 완성되면 하는걸로'
# 2026/09/10 기준으로 1차 Country Loop완성성공함.
## 이제부터 ABM + UtilityAI기반의 기업들을 만들겠음.

# 일단은 국방/전자전기/생활 이렇게 하겠음

class SectorModel(Model):

    def __init__(self, starttime=0, stoptime=0, dt=1, name="", scheduler=None, data_collector=None):
        super().__init__(starttime, stoptime, dt, name, scheduler, data_collector)

class Sector(Agent):

    def __init__(self, agent_id, model, properties, agent_type="sector"):
        super().__init__(agent_id, model, properties, agent_type)

    