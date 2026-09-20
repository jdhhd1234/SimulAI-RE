from BPTK_Py import Model

from calc.base.country_mdl import CountryEconomic
from calc.base.company_mdl import SectorFactoryModel, print_company_result

# 2026/09/14: country_mdl(국가경제)과 company_mdl(기업)을 하나의 Model로 연동해서 실행한다.
# 연동 지점: 기업 profit -> 국가 tax_revenue (법인세로 합산)
def mainRun(corporate_tax_rate=0.2):

    model = Model(
        starttime=0.0,
        stoptime=5.0,
        dt=1.0,
        name="IntegratedModel",
    )

    company = SectorFactoryModel(
        resource_price=10.0,
        sell_price=100.0,
        product_count=50.0,
    )

    company_production = company.production_func(model)
    company_sell = company.sell_func(model)
    company_profit = company.profit_func(model, company_sell, company_production)
    wage = company.profit_for_wage(model, company_profit)

    country = CountryEconomic(
        gdp=1000.0,
        population=1200.0,
        tax_rate=0.12,
        resource_power=7.0,
    )

    labor = model.stock("labor")
    hire = country.hire_func(model, country.population, labor)
    labor = country.labor_func(model, hire, labor)
    production = country.production_func(model, labor, country.resource_power)
    sell_price = country.gdp / country.population
    sell = country.sell_func(model, sell_price, production)
    gdp = country.gdp_func(model, sell)
    tax_revenue = country.tax_revenue_func(
        model,
        gdp,
        country.tax_rate,
        company_profit=company_profit,
        corporate_tax_rate=corporate_tax_rate,
    )

    print("[CLI] 국가-기업 연동 모델 가동 및 결과 연산...")
    df = model.simulate(equations=[
        "gdp",
        "tax_revenue",
        "hire",
        "labor",
        "production",
        "sell",
        "company_production",
        "company_sell",
        "profit",
        "wage",
    ])

    print_company_result(df)

    return model


if __name__ == "__main__":
    mainRun()
