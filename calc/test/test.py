import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import calc.dynamics_system.dynamic_sector as ds

factory = ds.SystemDynamicSector()

steel_sector = factory.make_sector("steel")
car_sector = factory.make_sector("car")

steel_recipe = factory.make_recipe("steel_recipe", "iron", "steel", 0.9)
car_recipe = factory.make_recipe("car_recipe", "steel", "car", 0.5)
iron = factory.set_resource("iron", 1000, 100, 1.0, 0.8)

steel_factory = factory.sector_create_factory(0, 0, steel_sector)
car_factory = factory.sector_create_factory(1, 1, car_sector)
factory.sector_factory_setting(steel_factory, recipe=steel_recipe["name"], capacity=1000)
factory.sector_factory_setting(car_factory, recipe=car_recipe["name"], capacity=200)

assert factory.sector_supply_chain(100, 0.9, iron) == 72.0
assert iron["reserve"] == 900
assert len(steel_sector["factories"]) == 1
assert len(car_sector["factories"]) == 1

print(factory.sectors)
