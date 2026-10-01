-- Minimal sector test used by the Lua UI and test_economy.py.

local steel_loc = locations[1] or {name = "Steel plant", lat = 36.019, lon = 129.343}
local car_loc = locations[2] or {name = "Car plant", lat = 35.083, lon = 137.156}

local steel = api.make_sector("steel")
local car = api.make_sector("car")
local steel_recipe = api.make_recipe("steel_recipe", "iron", "steel", 0.9)
local car_recipe = api.make_recipe("car_recipe", "steel", "car", 0.5)

local steel_id = api.sector_create_factory(steel_loc.lat, steel_loc.lon, steel)
local car_id = api.sector_create_factory(car_loc.lat, car_loc.lon, car)
api.sector_factory_setting(steel_id, {recipe = steel_recipe, capacity = 3500})
api.sector_factory_setting(car_id, {recipe = car_recipe, capacity = 5750})

api.describe(steel_id, steel_loc.name, "KR")
api.describe(car_id, car_loc.name, "JP")

api.make_converter("steel_output", function(t)
    return 3500
end)

api.make_converter("car_output", function(t)
    return 5750
end)

api.make_stock("steel_inventory", function(t)
    return get("steel_output", t)
end, 0.0)

api.make_stock("car_inventory", function(t)
    return get("car_output", t)
end, 0.0)

api.make_stock(steel_id .. "_capital", function(t)
    return get("steel_output", t)
end, 5000.0)

api.make_stock(car_id .. "_capital", function(t)
    return get("car_output", t)
end, 8000.0)
