import os
import lua_runtime as lr

import register_api

lua_runtime = lr.lua

# 1. 현재 Python 스크립트가 있는 폴더의 절대 경로를 구합니다.
current_dir = os.path.dirname(os.path.abspath(__file__))

# 2. 스크립트 위치 기준으로 Lua 파일의 경로를 절대 경로로 결합합니다.
lua_file_path = os.path.join(current_dir, "main.lua")

# 3. 안전하게 파일 열기
with open(lua_file_path, "r", encoding="utf-8") as f:
    lua_code = f.read()
    
lua_runtime.execute(lua_code=lua_code)

print(register_api.ds_sector.sectors)
print(register_api.ds_sector.resources)