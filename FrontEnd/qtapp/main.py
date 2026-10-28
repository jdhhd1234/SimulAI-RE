import sys
from pathlib import Path

# python FrontEnd/qtapp/main.py 로 바로 실행할 수 있도록 프로젝트 루트를 경로에 넣는다.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pyqtgraph as pg
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QLabel, QPushButton, QButtonGroup, QStackedWidget,
    QHBoxLayout, QVBoxLayout,
)

from FrontEnd.qtapp.common import STYLE_SHEET, MUTED, DANGER
from FrontEnd.qtapp.state import AppState
from FrontEnd.qtapp.map_page import MapPage
from FrontEnd.qtapp.lua_page import LuaPage

# 2026/10/15: WebUI(FastAPI + HTML/JS) 대신 PySide6 + PyQtGraph 데스크톱 앱.
# 실행: python FrontEnd/qtapp/main.py
# 2026/10/17: 상단 헤더(제목 + 단계 탭 + 상태) / 가운데 화면 / 하단 실행 바 구조로 변경.

TABS = ("세계 설정", "실행 및 분석")


class MainWindow(QMainWindow):

    def __init__(self, state):
        super().__init__()
        self.state = state
        self.setWindowTitle("SIMULAI-RE")
        self.resize(1600, 900)

        self.map_page = MapPage(state)
        self.lua_page = LuaPage(state)
        self.pages = QStackedWidget()
        self.pages.addWidget(self.map_page)
        self.pages.addWidget(self.lua_page)

        # 2026/10/23: 헤더 + 하단 실행 바 → 상단 HUD 한 줄 (제목 / 수치 칩 / 단계 탭 / 상태 + 실행)
        header = QFrame(objectName="card")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(12, 8, 12, 8)
        header_layout.addWidget(QLabel("◎", objectName="logo"))
        header_layout.addWidget(QLabel("SIMULAI-RE", objectName="title"))
        header_layout.addWidget(QLabel("시나리오 편집기", objectName="badge"))
        header_layout.addSpacing(16)
        # 자산 / 위치 / 매장지 개수 (set_status 때 갱신)
        self.stats = {key: QLabel(objectName="stat") for key in ("자산", "위치", "매장지")}
        for label in self.stats.values():
            header_layout.addWidget(label)
        header_layout.addStretch()
        self.tab_group = QButtonGroup(self)
        for i, label in enumerate(TABS):
            button = QPushButton(label, objectName="tab", checkable=True, checked=i == 0)
            self.tab_group.addButton(button, i)
            header_layout.addWidget(button)
        self.tab_group.idClicked.connect(self.pages.setCurrentIndex)
        header_layout.addStretch()
        self.status_label = QLabel("시뮬레이션 준비 상태")
        self.chip = QLabel("준비 중", objectName="badge")
        run_button = QPushButton("▶  시뮬레이션 실행", objectName="primary")
        run_button.clicked.connect(self.run_simulation)
        header_layout.addWidget(self.status_label)
        header_layout.addWidget(self.chip)
        header_layout.addWidget(run_button)

        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        layout.addWidget(header)
        layout.addWidget(self.pages, 1)
        self.setCentralWidget(central)

        for page in (self.map_page, self.lua_page):
            page.status.connect(self.set_status)
        self.lua_page.companies_changed.connect(self.map_page.refresh)
        self.map_page.refresh()

    def set_status(self, message, is_error=False):
        self.status_label.setStyleSheet(f"color: {DANGER if is_error else MUTED};")
        self.status_label.setText(message)
        counts = {"자산": len(self.state.get_companies()), "위치": len(self.state.locations), "매장지": len(self.state.deposits)}
        for key, label in self.stats.items():
            label.setText(f"<span style='color:{MUTED}; font-size:11px'>{key}</span>&nbsp; {counts[key]:,}")
        # 상태 표시는 Lua 실행 결과만 반영한다 (지도 화면의 주기적 메시지는 무시)
        if is_error:
            self.chip.setText("오류")
        elif message.startswith("실행 중"):
            self.chip.setText("실행 중")
        elif message.startswith("완료"):
            self.chip.setText("완료")

    def run_simulation(self):
        """하단 실행 버튼: 실행 및 분석 탭으로 이동해 선택된 Lua 파일을 실행"""
        self.tab_group.button(1).setChecked(True)
        self.pages.setCurrentIndex(1)
        self.lua_page.run_lua()

    def closeEvent(self, event):
        self.state.stop()
        super().closeEvent(event)


def main():
    pg.setConfigOptions(antialias=True)
    app = QApplication(sys.argv)
    app.setStyleSheet(STYLE_SHEET)
    state = AppState()
    state.start_auto_companies()
    window = MainWindow(state)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
