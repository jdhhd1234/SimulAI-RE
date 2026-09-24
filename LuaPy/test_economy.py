import os

from lua_bridge import LuaBridge

bridge = LuaBridge(0, 10, 1, "lua_economy")

# 2026/09/24: 파일 실행하는곳.
bridge.run_file(os.path.join(os.path.dirname(__file__), "economy.lua"))

print("sector_link car  :", dict(bridge.sector_link("car")["influenced_by"].items()), dict(bridge.sector_link("car")["influences"].items()))
print("sector_link steel:", dict(bridge.sector_link("steel")["influenced_by"].items()), dict(bridge.sector_link("steel")["influences"].items()))
print("summary steel    :", dict(bridge.sector_summary("steel").items()))

# economy.lua의 사업장 위치는 지도 좌표(위도, 경도)다.
steel_id = "steel_36.019_129.343"
car_id = "car_35.083_137.156"

print(f"{'t':>2} {'steel_output':>12} {'car_output':>10} {'steel_capital':>13} {'car_capital':>11}")
for t in range(0, 11):
    print(
        f"{t:>2} {bridge.value('steel_output', t):>12} {bridge.value('car_output', t):>10}"
        f" {bridge.value(steel_id + '_capital', t):>13} {bridge.value(car_id + '_capital', t):>11}"
    )

# 기대값: 철강 3500/step, 자동차 5750/step 이익 -> t=10에서 5000+35000, 8000+57500
assert bridge.value(steel_id + "_capital", 10) == 5000 + 3500 * 10
assert bridge.value(car_id + "_capital", 10) == 8000 + 5750 * 10
print("OK")
