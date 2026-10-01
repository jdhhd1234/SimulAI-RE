-- Country model used by country_mdl.py.
-- params is supplied by Python before this file is executed.

local country = api.make_sector("country")
local recipe = api.make_recipe("country_goods", "labor", "goods", params.resource_power)
local factory = api.sector_create_factory(0, 0, country)
api.sector_factory_setting(factory, {
    recipe = recipe,
    capacity = params.population * 5 * params.resource_power,
})

local sell_price = params.gdp / params.population

api.make_converter("hire", function(t)
    return (params.population - get("country_0_0_labor", t)) * 0.1
end)

api.make_stock("country_0_0_labor", function(t)
    return get("hire", t)
end, 0.0)

api.make_converter("production", function(t)
    return get("country_0_0_labor", t) * 5 * params.resource_power
end)

api.make_stock("production_inventory", function(t)
    return get("production", t)
end, 0.0)

api.make_converter("sell", function(t)
    return get("production", t) * sell_price
end)

api.make_converter("gdp", function(t)
    return get("sell", t)
end)

api.make_converter("tax_revenue", function(t)
    return get("gdp", t) * params.tax_rate
end)
