import numpy as np

from BPTK_Py import Model
from BPTK_Py import sd_functions as sd

"""
BPTK-Py로 만들 때는 우선 다음 순서로 생각하면 됩니다.
1. 무엇이 쌓이는가? → Stock
2. 무엇 때문에 늘고 줄어드는가? → Flow
3. 흐름을 결정하는 조건은 무엇인가? → Converter
4. 고정된 설정값은 무엇인가? → Constant
"""

class InitValue:
    def __init__(
        self,
        resource,
        product_price,
        population,
        buy_expense
    ):
        self.resource = resource
        self.product_price = product_price
        self.population = population
        self.buy_expense = buy_expense
    
def TestBPTK(init: InitValue):
    """극초소형 경제시뮬"""
    model = Model(
        starttime=0.0,
        stoptime=20.0,
        dt=0.1,
        name="Simple Economic Model",
    )
    
    #Stocks / 쌓이는 값들
    cash = model.stock("cash")
    raw_material = model.stock("raw_material")
    products = model.stock("products")
    profit = model.stock("profit")

    # Flows / 여기 값들은 이제 위에 Stocks에서 늘고 줄어드는가?
    purchase = model.flow("purchase")
    production = model.flow("production")
    sales = model.flow("sales")

    # Converters / 흐름이 결정되는 조건
    demand = model.converter("demand")
    profit_rate = model.converter("profit_rate")
    
    # Constants 고정값
    population = model.constant("population")
    consumption_per_person = model.constant("consumption_per_person")
    buy_price = model.constant("buy_price")
    sell_price = model.constant("sell_price")
    raw_per_product = model.constant("raw_per_product")
    production_capacity = model.constant("production_capacity")
        
    # Stocks랑 Constants는 Init해줘야함
    # Init는 근데 BackEnd에서 받은걸로 할꺼임
    
    #공식작성

    # Demand
    demand.equation = population * consumption_per_person

    # Buy raw materials, limited by available cash
    purchase.equation = sd.min(100.0, cash / buy_price)

    # Produce products, limited by raw materials and capacity
    production.equation = sd.min(
        raw_material / raw_per_product,
        production_capacity
    )

    # Sell products, limited by demand and inventory
    sales.equation = sd.min(products, demand)

    # Stock equations
    raw_material.equation = purchase - production * raw_per_product
    products.equation = production - sales

    # Cash and profit
    profit_rate.equation = sales * sell_price - purchase * buy_price
    cash.equation = profit_rate
    profit.equation = profit_rate
    
    return model