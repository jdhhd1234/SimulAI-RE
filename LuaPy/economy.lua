-- 자원
api.set_resource("iron", 10000, 100, 1.0, 1.0)

-- 철강 산업
local steel = api.make_sector("steel")
local rule = api.set_production_rule(
    "steel_rule",
    {iron = 2},
    0.9
)

api.set_sector_production_rule(steel, rule)

-- 공장
local factory = api.sector_create_factory(
    "steel_factory", steel, 37.5, 127.0
)

api.sector_factory_setting(factory, {
    capacity = 10
})

api.connect_supply_chain(steel)

-- 소비자 그룹
api.make_consumer_groups(10000, 300, 100, 10)

-- 세율
api.make_converter("tax_rate", 0.1)

-- 매출
api.make_flow("sales", function(t)
    return get("steel_production", t) * 100
end)

-- 세수 누적
api.make_stock("tax_revenue", function(t)
    return get("sales", t) * get("tax_rate", t)
end, 0)

print(api.value("tax_revenue", 2))