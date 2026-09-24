# 2026/09/24

목표: 고수준 경제관련 API를 제공해주는것이 목표.

## 경제 sector관련 API들
1. make_sector
그냥 빈 껍대기 뿐인 sector을 만드는것.
- 사업장 수(위치도 포함)
- 종사자 수
- 매출액 생산액

2. sector_link
이 sector가 어떤 sector에 영향을 받는지 설계하는것.
Input = 어떤 sector에 생산품에 영향을 받는다.
Output = 다른 sector에게 영향을 준다.

### CLAUDE의 제안
make_sector(id, name)                          # 분류 정보만
make_good(id, unit)                            # 철강(톤), 전기(kWh) 등
make_establishment(sector, location, recipe)   # 실제 생산 주체
set_recipe(output_good, inputs={good: 수량}, labor=인원, capacity=최대생산량)
sector_link(sector_id)                          # 레시피들로부터 자동 계산되는 조회용