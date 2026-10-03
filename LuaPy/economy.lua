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