-- 2026/09/24: 옛 calc/base/country_mdl(국가경제)을 새 엔진(Lua)으로 옮긴 것.
-- params(gdp, population, tax_rate, resource_power)는 Python(country_mdl.py)이 넣어준다.

local sell_price = params.gdp / params.population

api.make_sector("country", "국가")
api.make_good("goods", "개")

-- 국가 하나를 사업장 하나로 본다. labor는 0에서 시작해서 매 턴 hire만큼 늘어난다.
api.set_recipe("goods", {}, 0, params.population * 5 * params.resource_power)
api.make_establishment("country", 0, 0, "goods", 0, nil,
    function(t) return get("hire", t) end)

-- 남은 인원(population - labor)의 10%를 고용한다. (옛 모델은 random이었지만 여기서는 고정값)
api.make_converter("hire", function(t)
    return (params.population - get("country_0_0_labor", t)) * 0.1
end)

-- 노동자 한명당 5개씩 생산 x 자원력
api.make_converter("production", function(t)
    return get("country_0_0_labor", t) * 5 * params.resource_power
end)

api.make_converter("sell", function(t)
    return get("production", t) * sell_price
end)

api.make_converter("gdp", function(t)
    return get("sell", t)
end)

api.make_converter("tax_revenue", function(t)
    return get("gdp", t) * params.tax_rate
end)
