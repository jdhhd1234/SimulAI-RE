import numpy as np

# 이 파일은 AI System그중에서 경제관련 AI System관련한 파일이다.


# 기업관련 AI
# 스팩
"""
1. Utility AI를 사용한다.
2. 여러 각종 지표는 Lua에서 받아온다.
"""
class CompanyUtilityAI:

    def decide(self, npc):
        # 후보 행동과 각각의 점수 계산 로직

        # 이걸 또 이제 Lua에서 추가할수 있게 한다. (즉 Lua Bridge랑 하는것)
        actions = [
            # 예시코드.
            # ("eat", self.score_hunger(npc)),
        ]
        
        # 약간의 랜덤성을 추가해 로봇처럼 똑같이 움직이는 현상 방지
        scored = [(action, score + np.random.uniform(0, 0.1)) for action, score in actions]
        
        # 가장 높은 점수의 행동 반환
        best_action = max(scored, key=lambda x: x[1])
        return best_action[0]

    # 여기에서 Lua에서 action관련 함수를 만들면 여기에 추가되는걸로 한다.