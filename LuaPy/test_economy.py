import os

from lua_bridge import LuaBridge

bridge = LuaBridge(0, 10, 1, "lua_economy")

# 2026/09/24: 파일 실행하는곳.
bridge.run_file(os.path.join(os.path.dirname(__file__), "economy.lua"))

print("sector_link automobile:", bridge.sector_link("automobile"))
print("sector_link steel     :", bridge.sector_link("steel"))
print("summary steel         :", bridge.sector_summary("steel"))

print(f"{'t':>2} {'steel_output':>12} {'automobile_output':>17}")
for t in range(0, 11):
    print(f"{t:>2} {bridge.value('steel_output', t):>12} {bridge.value('automobile_output', t):>17}")

# 기대값: 철강 capacity 300 * 수율 1.0, 자동차 capacity 150 * 수율 0.9 = 135/step 생산.
assert bridge.value("steel_output", 10) == 300 * 10
assert bridge.value("automobile_output", 10) == 135 * 10
print("OK")
