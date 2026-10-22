import json

from lua_bridge import LuaBridge


bridge = LuaBridge(0, 2, 1, "lua_abm")
bridge.lua.execute("""
    assert(api.make_consumer_groups(11, 300, 0, 3) == 3)

    local company = api.make_company("steel_buyer")
    assert(company == "steel_buyer")
    assert(api.get_company(company).cash == 120000000)

    api.set_company(company, 500000, {
        {name = "iron", price = 120000},
        {name = "coal", price = 10000}
    })

    local data = api.get_company(company)
    assert(data.cash == 500000)
    assert(#data.objects == 2)
    assert(data.objects[1].name == "iron")
    assert(data.objects[2].price == 10000)
    assert(api.get_company("missing") == nil)
    assert(not pcall(function() api.make_company(company) end))
    assert(not pcall(function() api.set_company("missing", 1) end))

    local rows = api.company_series({0, 2})
    assert(#rows == 2)
    assert(rows[1].time == 0)
    assert(rows[2].time == 2)
    assert(rows[1].companies[1].state == "idle")
    assert(rows[2].companies[1].cash == 500000)
""")

bridge.consumers[0].income = 100.0
bridge.consumers[1].income = 300.0
bridge.consumers[2].income = 500.0

bridge.lua.execute("""
    local rows = api.consumer_series({0, 2})
    assert(#rows == 2)
    assert(rows[1].time == 0)
    assert(rows[2].time == 2)
    local groups = rows[1].groups
    assert(groups[1].state == "saving")
    assert(groups[2].state == "normal")
    assert(groups[3].state == "spending")
    assert(groups[1].population + groups[2].population + groups[3].population == 11)
""")

result = bridge.results()
json.dumps(result)
assert len(result["consumers"]) == 3
assert len(result["companies"]) == 3
assert result["companies"][0]["companies"][0]["objects"][0]["name"] == "iron"
assert bridge.results()["consumers"] is result["consumers"]
assert bridge.results()["companies"] is result["companies"]

bridge.lua.execute('api.set_company("steel_buyer", 1000, {})')
assert bridge.company_rows is None
assert result["companies"][0]["companies"][0]["cash"] == 500000
assert bridge.results()["companies"][0]["companies"][0]["cash"] == 1000
assert len(bridge.companies["steel_buyer"].objects) == 0

print("ABM Lua API OK")
