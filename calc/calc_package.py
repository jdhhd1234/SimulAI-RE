import numpy as np
import pandas as pd

class CalcPackage:
    def __init__(self) -> None:
        pass
    
    def sigmoid_utilityai(
        self, 
        arrData: np.ndarray,
        midpoint: float = 50.0,
        steepness: float = 0.1
    ):
        """Sigmoid처리를 한다 보통은 0 ~ 1로 하지만"""
        return 1 / (1 + np.exp(
            -steepness * (arrData - midpoint)
        ))
    
    def logzip(self, arrData: np.ndarray):
        log_data = np.log10(arrData)
        return log_data
    
main = CalcPackage()