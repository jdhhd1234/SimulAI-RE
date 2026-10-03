import os

from lua_bridge import LuaBridge

bridge = LuaBridge(0, 10, 1, "lua_economy")

# 2026/09/24: 파일 실행하는곳.
bridge.run_file(os.path.join(os.path.dirname(__file__), "economy.lua"))

print("sector_link car  :", bridge.sector_link("car"))
print("sector_link steel:", bridge.sector_link("steel"))
print("summary steel    :", bridge.sector_summary("steel"))

# economy.lua의 사업장 위치는 지도 좌표(위도, 경도)다.
steel_id = "steel_plant"
car_id = "car_plant"

print(f"{'t':>2} {'steel_output':>12} {'car_output':>10} {'steel_capital':>13} {'car_capital':>11}")
for t in range(0, 11):
    print(
        f"{t:>2} {bridge.value('steel_output', t):>12} {bridge.value('car_output', t):>10}"
        f" {bridge.value('steel_output', t):>13} {bridge.value('car_output', t):>11}"
    )

# 기대값: 수율 적용 후 철강 3150/step, 자동차 2875/step 생산.
assert bridge.value("steel_output", 10) == 3150 * 10
assert bridge.value("car_output", 10) == 2875 * 10
print("OK")
