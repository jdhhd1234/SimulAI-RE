"""Registry for economic models exposed by the web API.

To add a model, copy an entry and update the metadata:
- Required: id, name, module, class, builder, inputs.
- ``inputs`` keys must exactly match the registered class constructor
  parameters. Each input needs label/default; min/max/step are optional UI and
  validation hints.
- ``builder`` is the method called on the constructed class. It may have any
  name, but must return a BPTK model with starttime, stoptime, and dt.
- Optional: description and outputs. ``outputs`` supplies labels/colors for
  series discovered from the built model.
  
Example:

"new_model": {
    "id": "new_model",
    "name": "name",
    "module": "calc.basic_model.new_model",
    "class": "NewInitValue",
    "builder": "BuildModel",
    "inputs": {
        # 생성자 인자와 동일하게 작성
    },
}
"""

MODEL_REGISTRY = {
    "company_model": {
        "id": "company_model",
        "name": "기업 재무·생산 모델",
        "description": "현금, 부채, 생산, 판매, 비용 흐름을 단순화해 살펴보는 기업 시뮬레이션 모델입니다.",
        "module": "calc.basic_model.base_mode",
        "class": "InitValue",
        "builder": "CompanyModel",
        "inputs": {
            "cash_init": {
                "label": "초기 현금",
                "default": 1000.0,
                "min": 0.0,
                "step": 100.0,
            },
            "debt_init": {
                "label": "초기 부채",
                "default": 2000.0,
                "min": 0.0,
                "step": 100.0,
            },
            "origin_price": {
                "label": "원가",
                "default": 250.0,
                "min": 0.0,
                "step": 10.0,
            },
            "sell_price": {
                "label": "판매 가격",
                "default": 500.0,
                "min": 0.01,
                "step": 10.0,
            },
            "labor_count": {
                "label": "노동자 수",
                "default": 120.0,
                "min": 0.0,
                "step": 1.0,
            },
            "deltatime": {
                "label": "시간 간격",
                "default": 0.1,
                "min": 0.000001,
                "step": 0.1,
            },
            "stoptime": {
                "label": "종료 시간",
                "default": 5.0,
                "min": 0.000001,
                "step": 0.1,
            },
        },
        "outputs": {
            "cash": {"label": "현금", "color": "#2E86AB"},
            "debt": {"label": "부채", "color": "#C73E1D"},
            "inventory": {"label": "재고", "color": "#6A994E"},
            "factory_production": {"label": "생산량", "color": "#F18F01"},
            "sales": {"label": "판매량", "color": "#8E44AD"},
            "cash_ratio": {"label": "부채/현금 비율", "color": "#33658A"},
            "factory_count": {"label": "공장 수", "color": "#86BBD8"},
            "demand": {"label": "수요", "color": "#F6AE2D"},
            "revenue": {"label": "매출", "color": "#2A9D8F"},
            "research_cost": {"label": "연구 비용", "color": "#E76F51"},
            "marketing_cost": {"label": "마케팅 비용", "color": "#9B5DE5"},
            "wage_cost": {"label": "임금 비용", "color": "#F15BB5"},
            "profit": {"label": "이익", "color": "#00BBF9"},
        },
    }
}
