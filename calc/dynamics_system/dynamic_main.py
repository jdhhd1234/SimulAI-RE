from BPTK_Py import Model
from BPTK_Py import sd_functions as sd

from typing import Any

class ModelSystemDynamics:
    
    def __init__(self, start_time, stop_time, dt, name: str) -> None:
        self.start_time = start_time
        self.stop_time = stop_time
        self.dt = dt
        self.name = name
    
    def system_dynamics_makeModel_func(self):
        
        model = Model(
            starttime=self.start_time,
            stoptime=self.stop_time,
            dt=self.dt,
            name=self.name
        )
        
        return model

# 2026/09/21: 일단 sd stock function을 만듬.
class SystemDynamics:
    
    def system_dynamics_stock_func(
        self, 
        model: Model, 
        name: str, 
        formula: Any, 
        init_value: float
    ):
        """
        This Role is stock. in System Dynamics
        It will use for Lua.
        """
        stock_name = model.stock(f"{name}")
        stock_name.equation = formula
        stock_name.initial_value = init_value
        
        return stock_name
    
    def system_dynamics_flow_func(
        self,
        model: Model,
        name: str,
        formula: Any
    ):
        """
        This Role is Flow. in System Dynamics
        It will use for Lua.
        """
        flow_name = model.flow(f"{name}")
        flow_name.equation = formula
        
        return flow_name
    
    def system_dynamics_converter_func(
        self,
        model: Model,
        name: str,
        formula: Any
    ):
        """
        This Role is converter. in System Dynamics
        It will use for Lua.
        """
        converter_name = model.converter(f"{name}")
        converter_name.equation = formula
        
        return converter_name