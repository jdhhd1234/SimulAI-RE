from BPTK_Py import Model

class SystemDynamicsModel:
    
    def create_model(self, startTime: float, endTime: float, deltaTime: float, name: str):
        
        model = Model(
            starttime=startTime,
            stoptime=endTime,
            dt=deltaTime,
            name=name
        )
        
        return model