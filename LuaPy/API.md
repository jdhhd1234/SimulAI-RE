# Lua API

Lua scripts use the global `api` object. Creation methods return name handles.
`calc` owns the simulation logic; the bridge converts arguments and results.

## Sector And Region

```lua
api.set_resource("iron", 10000, 100, 1.0, 1.0)
local sector = api.make_sector("steel")
local rule = api.set_production_rule("steel_rule", {iron = 2}, 0.9)
api.set_sector_production_rule(sector, rule)

local factory = api.sector_create_factory("steel_factory", sector, 37.5, 127.0)
api.sector_factory_setting(factory, {capacity = 10})
api.connect_supply_chain(sector)

local region = api.make_region("Seoul")
api.set_region_resource(region, "iron", 1000)
api.set_population(region, 10000, 0.01, 0.6)
api.set_infrastructure(region, 0.9, 0.8, 0.9, 0.95)
local population = api.get_region(region).population.total
```

Configure factory capacity before calling `connect_supply_chain`.
Regional resources and population are stored settings, not automatic inputs to
sector production equations.

## Consumers

```lua
local count = api.make_consumer_groups(10000, 300, 100, 10)
local rows = api.consumer_series({0, 1, 2})
print(count, rows[1].groups[1].state)
```

Arguments are `population`, `mean`, `std`, and `groups`.
Initial money is twice group-average income; fixed cost is `mean`.
States are `saving`, `normal`, and `spending` strings in the returned rows.
The current consumer FSM only changes state. It does not update cash or
calculate consumption, so `consume` remains zero.

## Companies

```lua
local company = api.make_company("steel_buyer")
api.set_company(company, 500000, {
    {name = "iron", price = 120000},
    {name = "coal", price = 10000}
})

local data = api.get_company(company)
print(data.cash, data.objects[1].name)

local rows = api.company_series({0, 1, 2})
print(rows[1].companies[1].state)
```

`make_company(name)` uses `CompanyConsumer.initialize()` defaults.
`set_company(name, cash, objects)` changes the existing agent attributes.
Pass `nil` to leave a setting unchanged, or `{}` to clear the object list.
`get_company(name)` returns a Lua snapshot table, or `nil` for an unknown name.
Duplicate creation and settings for an unknown company raise errors.

The current company `act()` calculates affordable quantity but does not store
purchases, deduct cash, or change inventory. This API does not add that logic.
Companies are not automatically connected to factories or utility AI.

## SD And Results

```lua
api.make_converter("tax_rate", 0.1)
api.make_flow("sales", function(t) return get("steel_production", t) * 100 end)
api.make_stock("revenue", function(t) return get("sales", t) end, 0)
print(api.value("revenue", 2))
```

Stock callbacks define the rate of change. `get(name, t)` reads an SD value.
Python callers use `bridge.results()` or `bridge.series()` for time series.
Results include `consumers` and `companies` when those agents exist.
Repeated result reads reuse cached ABM rows; changing company settings clears
the company cache. Direct `consumer_series` and `company_series` calls execute
`act()` on every call and return Lua tables when given Lua time arrays.
Configure agents before reading results; cache invalidation does not rewind
agent state.

## Qt Debugging

The Lua execution page has an analysis / AI debugging button. After a run,
the window shows SD indicators, previous-sample differences, a selected
indicator's trend, and recorded agent decisions for each sample.

Consumer snapshots include `decision` with the selected event, previous state,
income, and fixed cost. Company snapshots include `decisions` with each object's
price, cash, skipped/calculated action, and affordable quantity. These records
observe the existing rules; they do not add purchases or utility-AI decisions.
Browsing the debug window reads snapshots without advancing agents.
