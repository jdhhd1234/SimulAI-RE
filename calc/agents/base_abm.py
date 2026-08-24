from mesa import Agent, Model
import numpy as np

"""
한국기준으로 데이터 예제 할꺼임

소비자 시장 기준으로 이 제품을 볼떄 자신에 소득과 상황에 따라서 어떤선택을 하는지 결정하는 ABM
mesa기반

일단 이거는 지금 개발보다는 국가경제 어느정도 잡히면 하는걸로
"""

class Person(Agent):
    def __init__(
        self, 
        model,
        purchase_importance, # 구입 중요도 0 ~ 1
        
    ):
        super().__init__(model)
        self.purchase_importance = purchase_importance
    
    def step(self):
        """
        #### 자기 소득수준을 파악하고 
        #### 소득이 적으면 많이구입 하다가 많으면 점점 적게구입
        #### 소득이 많으면 많이구입 하다가 점점 적게구입
        #### 이거는 구입을 나타내는거임
        **일단은 UtilityAI로 처리**
        """
        
        

'''class ConsumerMarketModel(Model):
    def __init__(
        self
    ):
        '''