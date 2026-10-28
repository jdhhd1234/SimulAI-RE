import os
import sys
import lua_runtime as lr

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import calc.dynamics_system.dynamic_sector as dynamic_sector

ds_sector = dynamic_sector.SystemDynamicSector()

api = lr.lua.table()
api.make_sector = ds_sector.make_sector
api.delete_sector = ds_sector.delete_sector
api.set_resource = ds_sector.set_resource
api.delete_resource = ds_sector.delete_resource
api.set_production_rule = ds_sector.set_production_rule
api.delete_recipe = ds_sector.delete_recipe
api.set_sector_production_rule = ds_sector.set_sector_production_rule
api.sector_create_factory = ds_sector.sector_create_factory
api.sector_delete_factory = ds_sector.sector_delete_factory
api.sector_factory_setting = ds_sector.sector_factory_setting

lr.lua.globals().api = api