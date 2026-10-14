-- =========================================================
-- Medium Economy Model
-- 2026/10/03
--
-- 자원:
--   iron, coal, oil, bauxite, lithium
--
-- 산업:
--   steel
--   energy
--   automobile
--   aircraft
--   electronics
--
-- 현재 엔진 구조:
--   Resource -> Production Rule -> Sector -> Factory
-- =========================================================


-- =========================================================
-- 1. Resource
-- =========================================================

api.set_resource(
    "iron",
    5000000,   -- reserve
    80000,     -- extraction_capacity
    1.2,       -- extraction_cost
    0.90       -- processing_yield
)

api.set_resource(
    "coal",
    3500000,
    70000,
    0.8,
    0.85
)

api.set_resource(
    "oil",
    2500000,
    50000,
    2.0,
    0.88
)

api.set_resource(
    "bauxite",
    1500000,
    30000,
    1.5,
    0.82
)

api.set_resource(
    "lithium",
    500000,
    8000,
    4.0,
    0.75
)


-- =========================================================
-- 2. Sector
-- =========================================================

local steel_sector =
    api.make_sector("steel")

local energy_sector =
    api.make_sector("energy")

local automobile_sector =
    api.make_sector("automobile")

local aircraft_sector =
    api.make_sector("aircraft")

local electronics_sector =
    api.make_sector("electronics")


-- =========================================================
-- 3. Production Rule
-- =========================================================

-- 철강 생산
local steel_rule =
    api.set_production_rule(
        "steel_rule",

        {
            iron = 100,
            coal = 40
        },

        1.0
    )


-- 에너지 생산
local energy_rule =
    api.set_production_rule(
        "energy_rule",

        {
            coal = 30,
            oil = 15
        },

        1.0
    )


-- 자동차 생산
local automobile_rule =
    api.set_production_rule(
        "automobile_rule",

        {
            iron = 70,
            oil = 20,
            lithium = 5
        },

        0.90
    )


-- 항공기 생산
local aircraft_rule =
    api.set_production_rule(
        "aircraft_rule",

        {
            iron = 200,
            oil = 80,
            bauxite = 120
        },

        0.70
    )


-- 전자 산업
local electronics_rule =
    api.set_production_rule(
        "electronics_rule",

        {
            lithium = 10,
            oil = 5
        },

        0.95
    )


-- =========================================================
-- 4. Sector <-> Production Rule
-- =========================================================

api.set_sector_production_rule(
    steel_sector,
    steel_rule
)

api.set_sector_production_rule(
    energy_sector,
    energy_rule
)

api.set_sector_production_rule(
    automobile_sector,
    automobile_rule
)

api.set_sector_production_rule(
    aircraft_sector,
    aircraft_rule
)

api.set_sector_production_rule(
    electronics_sector,
    electronics_rule
)


-- =========================================================
-- 5. Factory
-- =========================================================

-- -------------------------
-- Steel
-- -------------------------

local steel_factory_1 =
    api.sector_create_factory(
        "steel_factory_1",
        steel_sector,
        37.45,
        126.70
    )

api.sector_factory_setting(
    steel_factory_1,
    {
        capacity = 120
    }
)


local steel_factory_2 =
    api.sector_create_factory(
        "steel_factory_2",
        steel_sector,
        35.95,
        129.40
    )

api.sector_factory_setting(
    steel_factory_2,
    {
        capacity = 180
    }
)


-- -------------------------
-- Energy
-- -------------------------

local energy_factory_1 =
    api.sector_create_factory(
        "energy_factory_1",
        energy_sector,
        36.10,
        129.35
    )

api.sector_factory_setting(
    energy_factory_1,
    {
        capacity = 250
    }
)


local energy_factory_2 =
    api.sector_create_factory(
        "energy_factory_2",
        energy_sector,
        35.20,
        129.10
    )

api.sector_factory_setting(
    energy_factory_2,
    {
        capacity = 170
    }
)


-- -------------------------
-- Automobile
-- -------------------------

local automobile_factory_1 =
    api.sector_create_factory(
        "automobile_factory_1",
        automobile_sector,
        35.54,
        129.31
    )

api.sector_factory_setting(
    automobile_factory_1,
    {
        capacity = 90
    }
)


local automobile_factory_2 =
    api.sector_create_factory(
        "automobile_factory_2",
        automobile_sector,
        37.40,
        127.10
    )

api.sector_factory_setting(
    automobile_factory_2,
    {
        capacity = 60
    }
)


-- -------------------------
-- Aircraft
-- -------------------------

local aircraft_factory =
    api.sector_create_factory(
        "aircraft_factory_1",
        aircraft_sector,
        35.18,
        128.10
    )

api.sector_factory_setting(
    aircraft_factory,
    {
        capacity = 35
    }
)


-- -------------------------
-- Electronics
-- -------------------------

local electronics_factory_1 =
    api.sector_create_factory(
        "electronics_factory_1",
        electronics_sector,
        37.25,
        127.05
    )

api.sector_factory_setting(
    electronics_factory_1,
    {
        capacity = 140
    }
)


local electronics_factory_2 =
    api.sector_create_factory(
        "electronics_factory_2",
        electronics_sector,
        36.70,
        127.45
    )

api.sector_factory_setting(
    electronics_factory_2,
    {
        capacity = 100
    }
)


-- =========================================================
-- 6. Supply Chain -> BPTK-Py
-- =========================================================

api.connect_supply_chain(
    steel_sector
)

api.connect_supply_chain(
    energy_sector
)

api.connect_supply_chain(
    automobile_sector
)

api.connect_supply_chain(
    aircraft_sector
)

api.connect_supply_chain(
    electronics_sector
)


-- =========================================================
-- 7. UI Information
-- =========================================================

api.describe(
    steel_factory_1,
    "Incheon Steel Plant",
    "Korea"
)

api.describe(
    steel_factory_2,
    "Pohang Steel Plant",
    "Korea"
)

api.describe(
    energy_factory_1,
    "East Coast Energy Complex",
    "Korea"
)

api.describe(
    energy_factory_2,
    "Busan Energy Complex",
    "Korea"
)

api.describe(
    automobile_factory_1,
    "Ulsan Automobile Plant",
    "Korea"
)

api.describe(
    automobile_factory_2,
    "Gyeonggi Automobile Plant",
    "Korea"
)

api.describe(
    aircraft_factory,
    "Aerospace Plant",
    "Korea"
)

api.describe(
    electronics_factory_1,
    "Suwon Electronics Plant",
    "Korea"
)

api.describe(
    electronics_factory_2,
    "Cheongju Electronics Plant",
    "Korea"
)


-- =========================================================
-- 8. Region (지역 특성)
-- =========================================================

local korea =
    api.make_region("Korea")

-- set_resource로 등록된 자원만 지역에 넣을 수 있다.
api.set_region_resource(korea, "iron", 1200000)
api.set_region_resource(korea, "coal", 800000)
api.set_region_resource(korea, "lithium", 50000)

api.set_population(
    korea,
    51000000,   -- total
    0.002,      -- growth_rate
    0.62        -- labor_ratio
)

api.set_infrastructure(
    korea,
    0.98,   -- power
    0.92,   -- transport
    0.95,   -- water
    0.99    -- telecom
)

local korea_info =
    api.get_region(korea)

print("Korea labor_force:", korea_info.population.labor_force)


-- =========================================================
-- 9. Consumer ABM (10% 소득계층 소비자)
-- =========================================================

-- 실제 인구 전체를 쓰면 느려서 1/1000 표본으로 만든다.
local consumer_groups =
    api.make_consumer_groups(
        korea_info.population.total / 1000,
        300.0,   -- mean income
        100.0,   -- std
        10       -- groups
    )

print("consumer groups:", consumer_groups)


-- =========================================================
-- 10. Custom System Dynamics
-- =========================================================

-- 전체 산업 생산량
api.make_converter("industrial_output", function(t)
    return get("steel_production", t)
        + get("energy_production", t)
        + get("automobile_production", t)
        + get("aircraft_production", t)
        + get("electronics_production", t)
end)

-- 인프라 수준이 높을수록 생산 효율이 오른다.
local infra = korea_info.infrastructure
local infra_bonus = (infra.power + infra.transport + infra.water + infra.telecom) / 4

api.make_converter("effective_output", function(t)
    return get("industrial_output", t) * infra_bonus
end)

-- 철강 판매는 자동차/항공기 생산 수요만큼 (생산량을 넘지 않음)
api.make_flow("steel_sales", function(t)
    local demand = get("automobile_production", t) * 0.5
        + get("aircraft_production", t) * 1.5
    return math.min(demand, get("steel_production", t))
end)

-- 철강 재고 = 생산 - 판매 누적
api.make_stock("steel_inventory", function(t)
    return get("steel_production", t) - get("steel_sales", t)
end, 0.0)


-- =========================================================
-- 11. WebUI 위치 마커
-- =========================================================

-- WebUI에서 추가한 위치가 있으면 첫번째 위치에 연구소를 짓는다.
if #locations > 0 then
    local marker = locations[1]

    local lab =
        api.sector_create_factory(
            "electronics_lab",
            electronics_sector,
            marker.lat,
            marker.lon
        )

    api.sector_factory_setting(lab, { capacity = 20 })
    api.describe(lab, marker.name .. " Electronics Lab", "Korea")
end


-- =========================================================
-- 12. 조회
-- =========================================================

local steel_summary =
    api.sector_summary(steel_sector)

print("steel factories:", steel_summary["factory_count"])
print("steel capacity :", steel_summary["capacity"])
print("steel_inventory t=10:", get("steel_inventory", 10))
