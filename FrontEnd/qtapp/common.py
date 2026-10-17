import math

import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView

# 지도/Lua 화면 공용 함수 (흑백 테마) (구 main/common.js)
# 2026/10/17: 흑백 → 시나리오 편집기 스타일 (남색 계열 어두운 배경 + 둥근 카드)
BG = "#0e1014"
PANEL = "#1b1f26"
INPUT = "#14171c"
LINE = "#2b313b"
SELECT = "#2c3644"
MUTED = "#8a93a3"
TEXT = "#d5dae2"
STRONG = "#ffffff"
ACCENT = "#8ab4f8"
DANGER = "#f28b82"

GRAYS = ["#ffffff", "#b3b3b3", "#808080", "#5c5c5c"]
DASHES = [Qt.SolidLine, Qt.DashLine, Qt.DotLine, Qt.DashDotLine]

# QGroupBox와 QFrame#card는 모두 둥근 카드로 그린다.
STYLE_SHEET = f"""
* {{ font-family: "Segoe UI", "Malgun Gothic"; font-size: 13px; }}
QWidget {{ background: transparent; color: {TEXT}; }}
QMainWindow {{ background: {BG}; }}
QFrame#card, QGroupBox {{ background: {PANEL}; border: 1px solid {LINE}; border-radius: 10px; }}
QGroupBox {{ margin-top: 0; padding: 34px 8px 8px 8px; }}
QGroupBox::title {{
    subcontrol-origin: padding; subcontrol-position: top left; left: 12px; top: 10px;
    color: {STRONG}; font-weight: 700; font-size: 14px;
}}
QFrame#divider {{ background: {LINE}; border: 0; max-height: 1px; min-height: 1px; }}
QLabel#title {{ color: {STRONG}; font-size: 20px; font-weight: 800; }}
QLabel#logo {{ color: {ACCENT}; font-size: 20px; }}
QLabel#badge {{ background: #2c3340; color: {TEXT}; border-radius: 10px; padding: 3px 10px; font-weight: 600; }}
QLabel[accent="true"] {{ color: {ACCENT}; font-weight: 600; }}
QLineEdit, QDoubleSpinBox, QComboBox, QPlainTextEdit, QListWidget, QTableWidget {{
    background: {INPUT}; border: 1px solid {LINE}; border-radius: 6px; padding: 3px;
}}
QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus {{ border-color: {ACCENT}; }}
QComboBox QAbstractItemView {{ background: {PANEL}; border: 1px solid {LINE}; selection-background-color: {SELECT}; }}
QToolTip {{ background: {PANEL}; color: {TEXT}; border: 1px solid {LINE}; padding: 4px; }}
QPushButton {{ background: #262c36; border: 1px solid {LINE}; border-radius: 6px; padding: 6px 12px; }}
QPushButton:hover {{ background: #344052; color: {STRONG}; }}
QPushButton:disabled {{ color: {MUTED}; }}
QPushButton#tab {{ background: transparent; border: 0; color: {MUTED}; font-size: 14px; font-weight: 600; padding: 8px 12px; }}
QPushButton#tab:hover {{ color: {TEXT}; }}
QPushButton#tab:checked {{ background: {SELECT}; color: {ACCENT}; }}
QPushButton#primary {{ background: {SELECT}; border: 0; color: {STRONG}; font-size: 14px; font-weight: 700; padding: 8px 16px; }}
QPushButton#primary:hover {{ background: #344052; color: {ACCENT}; }}
QListWidget#nav {{ background: transparent; border: 0; }}
QListWidget#nav::item {{ padding: 7px 8px; border-radius: 6px; }}
QListWidget#nav::item:hover {{ background: #232934; }}
QListWidget::item {{ padding: 3px; }}
QListWidget::item:selected, QTableWidget::item:selected {{ background: {SELECT}; color: {ACCENT}; }}
QHeaderView::section {{ background: {INPUT}; color: {MUTED}; border: 0; border-bottom: 1px solid {LINE}; padding: 3px; }}
QSplitter::handle:horizontal {{ width: 10px; }}
QScrollArea {{ border: 0; }}
QLabel[muted="true"] {{ color: {MUTED}; }}
QScrollBar {{ background: {BG}; width: 10px; height: 10px; }}
QScrollBar::handle {{ background: {LINE}; min-height: 20px; min-width: 20px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: none; }}
QStatusBar {{ color: {MUTED}; border-top: 1px solid {LINE}; }}
"""


def fmt(value):
    if isinstance(value, bool) or value is None:
        return "-" if value is None else str(value)
    if isinstance(value, (int, float)):
        return f"{value:,.2f}".rstrip("0").rstrip(".")
    return str(value)


def make_plot():
    plot = pg.PlotWidget(background=BG)
    plot.showGrid(x=True, y=True, alpha=0.15)
    for axis in ("left", "bottom"):
        plot.getAxis(axis).setTextPen(MUTED)
        plot.getAxis(axis).setPen(LINE)
    plot.addLegend(offset=(8, 8), labelTextColor=GRAYS[1])
    return plot


def render_line_chart(plot, labels, series):
    """값 차이가 너무 크면 부호 유지 log 스케일로 그린다."""
    plot.clear()
    keys = [key for key, values in series.items() if any(_finite(v) for v in values)]
    max_abs = max((abs(v) for key in keys for v in series[key] if _finite(v)), default=0)
    use_log = max_abs > 10000

    def scale(v):
        if not _finite(v):
            return math.nan
        return math.copysign(math.log10(1 + abs(v)), v) if use_log else v

    for i, key in enumerate(keys):
        pen = pg.mkPen(GRAYS[i % len(GRAYS)], width=1.5, style=DASHES[(i // len(GRAYS)) % len(DASHES)])
        plot.plot(list(labels), [scale(v) for v in series[key]], pen=pen, name=key, connect="finite")
    plot.setLabel("left", "log10(1+|x|)" if use_log else "", color=MUTED)


def _finite(value):
    return isinstance(value, (int, float)) and math.isfinite(value)


def make_table(columns=None):
    table = QTableWidget()
    table.setEditTriggers(QAbstractItemView.NoEditTriggers)
    table.setSelectionBehavior(QAbstractItemView.SelectRows)
    table.verticalHeader().setVisible(False)
    table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    table.horizontalHeader().setStretchLastSection(True)
    if columns:
        table.setColumnCount(len(columns))
        table.setHorizontalHeaderLabels(columns)
    return table


def render_table(table, rows, columns=None):
    """rows: dict 목록(columns가 없으면 첫 행의 키) 또는 columns와 같이 넘긴 값 목록."""
    if columns is None:
        columns = list(rows[0].keys()) if rows else []
        rows = [[row[column] for column in columns] for row in rows]
    table.clear()
    table.setColumnCount(len(columns))
    table.setHorizontalHeaderLabels(columns)
    table.setRowCount(len(rows))
    for r, row in enumerate(rows):
        for c, value in enumerate(row):
            table.setItem(r, c, QTableWidgetItem(fmt(value)))
