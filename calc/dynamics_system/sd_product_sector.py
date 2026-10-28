import sd_model_main as sd_mdl_main
import sd_resource as resource

from BPTK_Py import sd_functions as sd

def create_sector(name: str) -> dict:

    # create_setor에서 name에 "iron" 이라고 입력하면, iron이라는 이름을 가진 빈 껍대기 dict를 하나 간단하게 만드는 코드.
    sector = {
        "sector_type": name
    }

    return sector

def create_resource(name: str, setting: resource.Resource) -> dict:

    resource_set = {
        "reserves": setting.reserves,
        "production": setting.production,
        "production_cost": setting.production_cost
    }

    return resource_set

def create_production_rule(input_res: dict, output_res: dict, yield_product: float) -> dict:

    production_rule = {
        "input_res": input_res,
        "yield_product": yield_product,
        "output": output_res
    }

    return production_rule


# 2026/10/28: 이 코드는 sector와 자원 그리고 생산규칙을 연결하는 코드이다.
def assign_production_rule(sector: dict, )