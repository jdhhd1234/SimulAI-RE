import numpy as np

class MineSelectorAI:
    
    def __init__(self) -> None:
        pass
    
    def mine_generator(self, minecount):
        
        mine_score_list = []
        
        for i in range(minecount):
            resource_score = np.random.randint(1, 10)
            position_score = np.random.randint(1, 10)
            
            mine_score_list.append({
                "resource_score": resource_score,
                "position_score": position_score,
                "final_score": resource_score + position_score
            })
        
        return mine_score_list
    
    def select_mine(self, mine_score_list):
        
        select = max(mine_score_list)
        
        return select
    
    def mainRun(self):
        
        # 광산개수
        gen = self.mine_generator(12)
        sel = self.select_mine(gen)
        
        print(sel)
        
mine_selAI = MineSelectorAI()
run = mine_selAI.mainRun()