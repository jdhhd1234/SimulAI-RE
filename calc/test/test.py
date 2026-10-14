import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import calc.dynamics_system.dynamic_model as dmodel
import calc.dynamics_system.dynamic_sector as ds

model = dmodel.SystemDynamicsModel().create_model(0, 10, 1, "test")
factory = ds.SystemDynamicSector()

factory.set_resource("iron", 1000, 100, 1.0, 0.8)
factory.set_production_rule("steel_rule", {"iron": 2.0}, 0.9)
factory.make_sector("steel")
factory.set_sector_production_rule("steel", "steel_rule")
factory.sector_create_factory("steel_factory", "steel")
factory.sector_factory_setting("steel_factory", capacity=40)
chain = factory.connect_supply_chain("steel", model)

# capacity 40 * yield 0.9 = 36/step, iron 40 * 2 = 80/step 소비
assert model.memoize(chain["production"], 0) == 36.0
assert model.memoize(chain["output"], 10) == 360.0
assert model.memoize(chain["resources"]["iron"], 10) == 200.0
assert factory.sectors["steel"]["factories"] == ["steel_factory"]

print("OK")
