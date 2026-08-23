from mesa import Agent, Model
import numpy as np

"""
한국기준으로 데이터 예제 할꺼임

소비자 시장 기준으로 이 제품을 볼떄 자신에 소득과 상황에 따라서 어떤선택을 하는지 결정하는 ABM
mesa기반

"""

class Person(Agent):
    def __init__(
        self, 
        model,
        low_asset,
        normal_asset,
        max_asset,
        size
    ):
        super().__init__(model)
        self.low_asset = low_asset
        self.normal_asset = normal_asset
        self.max_asset = max_asset
        self.size = size
    
    def step(self):
        """
        #### 자기 소득수준을 파악하고 
        #### 소득이 적으면 많이구입 하다가 많으면 점점 적게구입
        #### 소득이 많으면 많이구입 하다가 점점 적게구입
        #### 이거는 구입을 나타내는거임
        **일단은 FSM으로 처리 if문으로**
        """
        myasset = np.random.normal(loc=self.normal_asset, scale=1, size=self.size)
        
        buy_list = []
        
        if myasset is np.isclose(self.normal_asset):
            
            if 
        

'''class ConsumerMarketModel(Model):
    def __init__(
        self
    ):
        '''