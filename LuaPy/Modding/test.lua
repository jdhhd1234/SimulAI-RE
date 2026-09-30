-- 새 API(LuaBridge) 테스트. 실행: LuaBridge(0, 10, 1, ...).run_file("LuaPy/Modding/test.lua")
-- api.make_sector / sector_make_factory / make_stock / make_flow / make_converter / describe를 모두 쓴다.

local bio_loc = locations[1] or {name = "바이오 1공장", lat = 1200, lon = 720}
local bio_loc2 = locations[2] or {name = "바이오 2공장", lat = 1400, lon = 800}

-- 1. sector + factory
local bio = api.make_sector("bio")
local fac1 = api.sector_make_factory(bio_loc.lat, bio_loc.lon, bio)
local fac2 = api.sector_make_factory(bio_loc2.lat, bio_loc2.lon, bio)

api.describe(fac1, bio_loc.name, "KR")
api.describe(fac2, bio_loc2.name, "KR")

-- 2. system dynamics: 매출(income)에서 비용(cost)을 뺀 이익(profit)이 자본(capital)에 쌓인다.
-- 기대값: income=100/스텝 고정 -> capital(t) = 5000 + 100*t, profit = 70 고정
api.make_converter("income", function(t) return 100 end)
api.make_converter("cost", function(t) return 30 end)
api.make_converter("profit", function(t) return get("income", t) - get("cost", t) end)
api.make_stock("capital", function(t) return get("income", t) end, 5000.0)

-- 3. flow: 출하량(시계열에만 기록, stock과 연결되지 않은 단독 값)
api.make_flow("shipment", function(t) return 20 end)

-- 4. 조회 API (에러 없이 도는지 확인)
api.sector_link(bio)
api.sector_summary(bio)