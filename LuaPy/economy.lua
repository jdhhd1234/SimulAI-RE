-- 2026/09/24: 간단 경제 테스트. 철강 -> 자동차 공급망.
-- api.* 는 Python(LuaBridge), get(name, t)는 다른 stock/converter의 값을 읽는다.
-- 사업장 위치(x, y)는 지도의 (위도, 경도)다. WAR ECONOMY UI에서 이 파일을 실행하면 지도에 표시된다.
-- make_establishment가 돌려주는 id로 그 사업장의 값을 읽는다: get(steel_id .. "_labor", t)
-- UI의 "위치 추가"로 넣은 위치가 전역 locations 테이블(locations[1].name/.lat/.lon)로 들어온다.
-- 위치가 없으면 아래 기본 좌표를 쓴다.

local steel_loc = locations[1] or {name = "포항 제철소", lat = 36.019, lon = 129.343}
local car_loc = locations[2] or {name = "도요타 공장", lat = 35.083, lon = 137.156}
local fashion_loc = locations[3] or {name = "의류 공장", lat = 35.8779, lon = 128.6115}

local WAGE = 5
local STEEL_PRICE = 10
local CAR_PRICE = 50

api.make_sector("steel", "철강")
api.make_sector("car", "자동차")
api.make_sector("fashion", "의류")

api.make_good("steel", "톤")
api.make_good("car", "대")
api.make_good("fashion", "벌")

api.set_recipe("steel", {}, 100, 1000)
api.set_recipe("car", {steel = 2}, 50, 200)
api.set_recipe("fashion", {steel = 1}, 5, 100)

local steel_id, car_id

-- capital의 변화율 = 매출 - 비용
steel_id = api.make_establishment("steel", steel_loc.lat, steel_loc.lon, "steel", 5000,
    function(t) return get("steel_sold", t) * STEEL_PRICE - get(steel_id .. "_labor", t) * WAGE end)

car_id = api.make_establishment("car", car_loc.lat, car_loc.lon, "car", 8000,
    function(t)
        return get("car_output", t) * CAR_PRICE
            - get("steel_sold", t) * STEEL_PRICE
            - get(car_id .. "_labor", t) * WAGE
    end)

local FASHION_PRICE = 30
local fashion_id

fashion_id = api.make_establishment("fashion", fashion_loc.lat, fashion_loc.lon, "fashion", 3000,
    function(t)
        return get("fashion_output", t) * FASHION_PRICE
            - get("fashion_output", t) * STEEL_PRICE
            - get(fashion_id .. "_labor", t) * WAGE
    end)

api.describe(steel_id, steel_loc.name)
api.describe(car_id, car_loc.name)
api.describe(fashion_id, fashion_loc.name)

-- 생산량 = min(최대생산량, 노동자 * 1인당 생산성). 자동차는 철강 공급(철강 2톤/대)도 한계.
api.make_converter("steel_output", function(t)
    return math.min(get(steel_id .. "_capacity", t), get(steel_id .. "_labor", t) * 10)
end)

api.make_converter("car_output", function(t)
    return math.min(
        get(car_id .. "_capacity", t),
        get(car_id .. "_labor", t) * 4,
        get("steel_output", t) / 2
    )
end)

-- 의류: 생산량 = min(최대생산량, 노동자 * 20, 자동차에 쓰고 남은 철강(1톤/벌))
api.make_converter("fashion_output", function(t)
    return math.min(
        get(fashion_id .. "_capacity", t),
        get(fashion_id .. "_labor", t) * 20,
        get("steel_output", t) - get("car_output", t) * 2
    )
end)

-- 자동차 공장이 사가는 철강만큼만 팔린다.
api.make_converter("steel_sold", function(t)
    return math.min(get("steel_output", t), get("car_output", t) * 2)
end)