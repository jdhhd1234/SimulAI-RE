-- Country model used by country_mdl.py.
-- params is supplied by Python before this file is executed.

local country = api.make_sector("country")
api.set_resource("labor", params.population * 6, params.population * 0.1, 0, 1.0)
local recipe = api.set_production_rule("country_goods", {labor = 1}, 5 * params.resource_power)
local factory = api.sector_create_factory("country_factory", country)
api.sector_factory_setting(factory, {
    capacity = params.population * 5 * params.resource_power,
})
api.set_sector_production_rule(country, recipe)
api.connect_supply_chain(country)

local sell_price = params.gdp / params.population

api.make_converter("hire", function(t)
    return (params.population - get("country_labor", t)) * 0.1
end)

api.make_stock("country_labor", function(t)
    return get("hire", t)
end, 0.0)

api.make_converter("sell", function(t)
    return get("country_output", t) * sell_price
end)

api.make_converter("gdp", function(t)
    return get("sell", t)
end)

api.make_converter("tax_revenue", function(t)
    return get("gdp", t) * params.tax_rate
end)
