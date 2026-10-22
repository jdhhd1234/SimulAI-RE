from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox,
    QComboBox, QSplitter, QGroupBox, QTabWidget,
)

from FrontEnd.qtapp.common import fmt, make_plot, render_line_chart, make_table, render_table


INDICATOR_COLUMNS = ["지표", "현재 값", "이전 값", "변화량"]
AGENT_COLUMNS = ["에이전트", "이전 상태", "현재 상태", "행동", "판단 입력", "판단 근거", "실행 결과"]


class DebugWindow(QMainWindow):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("분석 / AI 디버깅")
        self.resize(1200, 800)
        self.result = {}

        body = QWidget()
        self.setCentralWidget(body)
        layout = QVBoxLayout(body)
        self.summary = QLabel("실행 결과가 없습니다. Lua 시뮬레이션을 먼저 실행하세요.")
        self.summary.setWordWrap(True)
        layout.addWidget(self.summary)

        controls = QHBoxLayout()
        controls.addWidget(QLabel("샘플 번호 (0부터)"))
        self.sample = QSpinBox()
        self.sample.setEnabled(False)
        controls.addWidget(self.sample)
        self.time_label = QLabel("시점: -")
        controls.addWidget(self.time_label)
        controls.addStretch()
        controls.addWidget(QLabel("추세 지표"))
        self.indicator = QComboBox()
        self.indicator.setMinimumWidth(220)
        controls.addWidget(self.indicator)
        layout.addLayout(controls)

        self.chart = make_plot()
        self.chart.setLabel("bottom", "시뮬레이션 시간")
        tables = QTabWidget()
        self.indicator_table = make_table(INDICATOR_COLUMNS)
        self.agent_table = make_table(AGENT_COLUMNS)
        tables.addTab(self.indicator_table, "지표 / 변화량")
        tables.addTab(self.agent_table, "AI 행동 / 판단 근거")

        box = QGroupBox("선택 지표의 전체 추세")
        QVBoxLayout(box).addWidget(self.chart)
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(box)
        splitter.addWidget(tables)
        splitter.setSizes([260, 440])
        layout.addWidget(splitter, 1)

        self.note = QLabel(
            "실행 완료 후 저장된 결과를 조회합니다. 시점을 바꿔도 AI를 다시 실행하지 않습니다.\n"
            "소비자는 FSM 상태만 변경하며, 기업은 구매 가능 수량만 계산합니다. 실제 소비·구매는 아직 실행하지 않습니다."
        )
        self.note.setWordWrap(True)
        self.note.setProperty("muted", True)
        layout.addWidget(self.note)
        self.sample.valueChanged.connect(self.render_sample)
        self.indicator.currentTextChanged.connect(self.render_chart)

    def set_result(self, result, name):
        self.result = result
        times = result.get("time", [])
        self.setWindowTitle(f"분석 / AI 디버깅 - {name}")
        self.summary.setText(f"최근 성공 실행: {name} | 샘플 {len(times)}개 | 지표 {len(result.get('series', {}))}개")
        self.sample.blockSignals(True)
        self.sample.setRange(0, max(0, len(times) - 1))
        self.sample.setValue(0)
        self.sample.setEnabled(bool(times))
        self.sample.blockSignals(False)
        self.indicator.blockSignals(True)
        self.indicator.clear()
        self.indicator.addItems(list(result.get("series", {})))
        self.indicator.blockSignals(False)
        self.render_chart()
        self.render_sample()

    def show_error(self, message):
        previous = "아래 표는 이전 성공 실행의 결과입니다." if self.result else "표시할 성공 실행 결과가 없습니다."
        self.summary.setText(f"최근 실행 실패: {message}\n{previous}")

    def render_chart(self):
        name = self.indicator.currentText()
        series = self.result.get("series", {})
        render_line_chart(self.chart, self.result.get("time", []), {name: series[name]} if name in series else {})

    def render_sample(self):
        times = self.result.get("time", [])
        index = self.sample.value()
        rows = []
        agents = []
        if times:
            self.time_label.setText(f"시점: {fmt(times[index])}")
            for name, values in self.result.get("series", {}).items():
                current = values[index]
                previous = values[index - 1] if index else None
                delta = current - previous if isinstance(current, (int, float)) and isinstance(previous, (int, float)) else None
                rows.append([name, current, previous, delta])

            consumers = self.result.get("consumers", [])
            if index < len(consumers):
                for group in consumers[index]["groups"]:
                    decision = group.get("decision", {})
                    income = decision.get("income")
                    fixcost = decision.get("fixcost")
                    reason = "판단 기록 없음"
                    if income is not None and fixcost is not None:
                        reason = "소득 < 고정비" if income < fixcost else "소득 > 고정비" if income > fixcost else "소득 = 고정비"
                    agents.append([
                        f"소비자 그룹 {group['decile']}", decision.get("previous_state"), group["state"],
                        decision.get("action", "기록 없음"), f"소득 {fmt(income)} / 고정비 {fmt(fixcost)}",
                        reason, f"현금 {fmt(group['cash'])} / 소비액 {fmt(group['consume'])} (상태 변경만 수행)",
                    ])

            companies = self.result.get("companies", [])
            if index < len(companies):
                for company in companies[index]["companies"]:
                    decisions = company.get("decisions", [])
                    if not decisions:
                        agents.append([company["name"], None, company["state"], "판단 기록 없음", None, "대상 상품 또는 기록 없음", "구매 실행 없음"])
                    for decision in decisions:
                        skipped = decision["action"] == "skip"
                        agents.append([
                            f"{company['name']} / {decision['object']}", None, company["state"],
                            "상품 건너뛰기" if skipped else "구매 가능 수량 계산",
                            f"현금 {fmt(decision['cash'])} / 가격 {fmt(decision['price'])}",
                            "가격 <= 0" if skipped else "현금 // 가격 (상품별 독립 계산)",
                            "계산 제외" if skipped else f"가능 수량 {fmt(decision['quantity'])} / 실제 구매·차감 없음",
                        ])
        else:
            self.time_label.setText("시점: -")

        render_table(self.indicator_table, rows, INDICATOR_COLUMNS)
        render_table(self.agent_table, agents, AGENT_COLUMNS)
        if times and not agents:
            self.time_label.setText(f"시점: {fmt(times[index])} | ABM 에이전트 없음")
