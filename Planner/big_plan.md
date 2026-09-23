# 큰 계획 즉 로드맵
# pip freeze > requirements.txt
1. 일단 단순 그래프랑 지표입력및 처리정도만
2. 공식을 알맞게 강화하고 가능하다면 자바스크립트나 HTML동적 처리도 검토하겠음
3. 지도데이터및 가능하다면 QGIS같은 툴과 연동시키는것
4. 군사관련 데이터및 공식
5. Lua or Python을 제한적 지원 하는걸로

# 중요 HOI4와 차별점이 무엇인가?

- HOI4는 예를들어서 

동원 ↑
→ 병력 ↑
→ 민간 노동력 ↓
→ 생산 ↓
→ 세수 ↓
→ 군수생산 압박 ↑

이걸 규칙으로 해야하는데

나의 SimulAI-RE는 이걸 결과를 만들어내는 메커니즘을 재현하려는 모델이다.
(물론 HOI4도 포함하기는 함)

전투 자체를 상세하게 시뮬레이션할 것인지, 아니면 전투는 단순화하고 국가의 경제·산업·인구·군수·물류가 전쟁 수행능력을 어떻게 결정하는지를 시뮬레이션할 것인지.

## 일반유저와 혹은 모더가 봤을떄 차이점
- 그냥 우리가 TABS라는 게임에서 "전투가 어떻게 될까? 궁금하다" 마치 레고같은 느낌으로 지켜보는마인드를 자극한다

- 이런쪽은 단순히 보이는것보다는 논리와 내부 구조가 중요하다 판단 즉 UI는 거의 똑같아보여도 내부적인 단기 / 중기 / 장기성이 매우 중요함


## 2026/08/23 1차 모델 기준점 잡기

1. 경제
- 소비자 = Agent Based Model
    - 재산확인
    - 재산에 맞게 구입

- 기업 = System Dynamic
    - 생산
    - 판매
    - 이익
    - 연구 / 임금 / 세금
    - 현금

## 2026/09/21 Big Fix Flow

엔진과 모딩영역은 나누기

1. 엔진(Python/C++)
- 유닛생성
- System Dynamics의 복잡성을 덜어내는 추상화 API
- Agent Based Model의 복잡성을 덜어내는 추상화 API

2. 모딩(Lua)
- API를 사용하여 유닛을 설정하고 
- Web UI를 사용하여 지도와 병력위치를 설정한다

### ChatGPT의 말:
Python/C++ Engine
- Unit/Formation/Weapon/Terrain 같은 핵심 도메인 객체
- SD 추상화 API
- ABM 추상화 API
- Simulation Tick / Time
- Event System
- Save/Load
- Lua Binding
- 가능하면 BPTK-Py 타입은 여기 밖으로 노출하지 않음

Lua Modding
- 유닛 스탯
- 무기/센서
- 교전 규칙
- 보급/사기/손실 공식
- 이벤트와 트리거
- 승리 조건

Web UI
- 지도 편집
- 유닛 배치
- Faction 설정
- Waypoint/Objective 설정
- 시나리오 시간대와 환경 설정
- 결과 시각화