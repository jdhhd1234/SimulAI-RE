import sys
from pathlib import Path

# python FrontEnd/qtapp/main.py 로 바로 실행할 수 있도록 프로젝트 루트를 경로에 넣는다.
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pyqtgraph as pg
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget

from FrontEnd.qtapp.common import STYLE_SHEET, MUTED, STRONG
from FrontEnd.qtapp.state import AppState
from FrontEnd.qtapp.map_page import MapPage
from FrontEnd.qtapp.lua_page import LuaPage

# 2026/10/15: WebUI(FastAPI + HTML/JS) 대신 PySide6 + PyQtGraph 데스크톱 앱.
# 실행: python FrontEnd/qtapp/main.py


class MainWindow(QMainWindow):

    def __init__(self, state):
        super().__init__()
        self.state = state
        self.setWindowTitle("SIMULAI-RE")
        self.resize(1600, 900)

        self.map_page = MapPage(state)
        self.lua_page = LuaPage(state)
        tabs = QTabWidget()
        tabs.addTab(self.map_page, "지도")
        tabs.addTab(self.lua_page, "Lua")
        self.setCentralWidget(tabs)

        for page in (self.map_page, self.lua_page):
            page.status.connect(self.set_status)
        self.lua_page.companies_changed.connect(self.map_page.refresh)
        self.map_page.refresh()

    def set_status(self, message, is_error=False):
        self.statusBar().setStyleSheet(f"color: {STRONG if is_error else MUTED};")
        self.statusBar().showMessage(message)

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
