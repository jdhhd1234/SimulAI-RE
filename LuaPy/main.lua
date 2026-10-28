
-- 자원 설정
api.set_resource(
    "iron",  -- 자원 이름
    10000,   -- 매장량
    100,     -- 채굴 용량
    1.0,     -- 채굴 비용
    0.9      -- 가공 수율
)

api.set_resource(
    "coal", 
    5000,
    200,
    0.5,
    1.0
)

-- 산업 생성
local steel = api.make_sector("steel")
local energy = api.make_sector("energy")

-- 산업 정보 읽기
local info = api.get_sector(steel)

print(info["production"])
  