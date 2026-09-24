import dynamics_system.dynamic_main as dm
import dynamics_system.dynamic_sector as ds

model = dm.ModelSystemDynamics(0, 10, 1, "test_model").system_dynamics_makeModel_func()
factory = ds.SystemDynamicMakeSector()

steel_sector = factory.make_sector("steel", "철강")
car_sector = factory.make_sector("car", "자동차")

steel_good = factory.make_good("steel", "톤")
car_good = factory.make_good("car", "대")

steel_recipe = factory.set_recipe("steel", inputs={}, labor=100, capacity=1000)
car_recipe = factory.set_recipe("car", inputs={"steel": 2}, labor=50, capacity=200)

steel_establishment = factory.make_establishment(model, "steel", (0, 0), steel_recipe, capital=5000)
car_establishment = factory.make_establishment(model, "car", (1, 1), car_recipe, capital=8000)

establishments = [steel_establishment, car_establishment]

print(factory.sector_link("car", establishments))
print(factory.sector_link("steel", establishments))
