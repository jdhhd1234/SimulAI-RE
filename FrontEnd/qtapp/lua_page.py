from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QSplitter, QGroupBox,
    QComboBox, QDoubleSpinBox, QCheckBox, QPushButton, QPlainTextEdit, QApplication,
)

from FrontEnd.qtapp.common import fmt, make_plot, render_line_chart, make_table, render_table
from FrontEnd.qtapp.state import LuaRunError

# Lua 실행 화면 (구 lua/lua.js). Lua 코드는 LuaPy/*.lua 파일로 작성하고, 여기서는 실행과 결과 표시만 한다.
SECTOR_COLUMNS = ["섹터", "생산 규칙", "공장 수", "capacity", "위치"]


def _spin(minimum, maximum, value):
    spin = QDoubleSpinBox()
    spin.setRange(minimum, maximum)
    spin.setDecimals(4)
    spin.setValue(value)
    return spin


class LuaPage(QWidget):
    status = Signal(str, bool)
    companies_changed = Signal()

    def __init__(self, state):
        super().__init__()
        self.state = state
        mono = QFontDatabase.systemFont(QFontDatabase.FixedFont)

        # 실행
        side = QWidget()
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(0, 0, 0, 0)
        box = QGroupBox("실행")
        form = QFormLayout(box)
        self.file_select = QComboBox()
        self.start = _spin(-1e9, 1e9, 0)
        self.stop = _spin(-1e9, 200, 10)
        self.dt = _spin(0.0001, 1e9, 1)
        self.to_map = QCheckBox("지도 자산으로 등록")
        self.run_button = QPushButton("실행")
        self.run_button.clicked.connect(self.run_lua)
        form.addRow("파일", self.file_select)
        form.addRow("start", self.start)
        form.addRow("stop", self.stop)
        form.addRow("dt", self.dt)
        form.addRow(self.to_map)
        form.addRow(self.run_button)
        side_layout.addWidget(box)

        box = QGroupBox("콘솔")
        self.console = QPlainTextEdit("실행 전")
        self.console.setReadOnly(True)
        self.console.setFont(mono)
        QVBoxLayout(box).addWidget(self.console)
        side_layout.addWidget(box, 1)

        # 결과
        main = QWidget()
        main_layout = QVBoxLayout(main)
        main_layout.setContentsMargins(0, 0, 0, 0)
        box = QGroupBox("결과")
        self.chart = make_plot()
        QVBoxLayout(box).addWidget(self.chart)
        main_layout.addWidget(box, 2)

        box = QGroupBox("섹터")
        self.sector_table = make_table(SECTOR_COLUMNS)
        QVBoxLayout(box).addWidget(self.sector_table)
        main_layout.addWidget(box, 1)

        box = QGroupBox("소스")
        self.source = QPlainTextEdit()
        self.source.setReadOnly(True)
        self.source.setFont(mono)
        QVBoxLayout(box).addWidget(self.source)
        main_layout.addWidget(box, 2)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(side)
        splitter.addWidget(main)
        splitter.setSizes([300, 1000])
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

        self.file_select.currentTextChanged.connect(self.load_source)
        self.load_files()

    def load_files(self):
        names = self.state.lua_files()
        self.file_select.addItems(names)
        if not names:
            self.status.emit("LuaPy 폴더에 .lua 파일이 없습니다.", True)

    def load_source(self, name):
        if name:
            self.source.setPlainText(self.state.lua_source(name))

    def render_console(self, lines, error=None):
        lines = list(lines) + ([f"ERROR: {error}"] if error else [])
        self.console.setPlainText("\n".join(lines) or "출력이 없습니다.")

    def render_sectors(self, sectors):
        rows = []
        for sector in sectors:
            rule = sector["link"]["production_rule"]
            summary = sector["summary"]
            rows.append([
                summary["sector"],
                (", ".join(f"{name} x{amount}" for name, amount in rule["need_resource"].items())
                 + f" → output ({rule['yield_rate']})") if rule else "-",
                summary["factory_count"],
                fmt(summary["capacity"]),
                " ".join(f"({lat}, {lon})" for lat, lon in summary["locations"]) or "-",
            ])
        render_table(self.sector_table, rows, SECTOR_COLUMNS)

    def run_lua(self):
        name = self.file_select.currentText()
        if not name:
            return
        self.status.emit("실행 중...", False)
        self.run_button.setEnabled(False)
        QApplication.processEvents()
        try:
            result = self.state.run_lua(
                name, self.start.value(), self.stop.value(), self.dt.value(), self.to_map.isChecked()
            )
        except LuaRunError as error:
            self.render_console(error.console, str(error))
            self.status.emit(str(error), True)
            return
        finally:
            self.run_button.setEnabled(True)

        self.render_console(result["console"])
        render_line_chart(self.chart, result["time"], result["series"])
        self.render_sectors(result["sectors"])
        if result["company_ids"]:
            self.companies_changed.emit()
            self.status.emit(f"완료 · 지도 자산 {len(result['company_ids'])}개 등록", False)
        else:
            self.status.emit("완료", False)
