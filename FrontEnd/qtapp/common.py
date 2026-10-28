import math

import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView

# 지도/Lua 화면 공용 함수 (흑백 테마) (구 main/common.js)
# 2026/10/17: 흑백 → 시나리오 편집기 스타일 (남색 계열 어두운 배경 + 둥근 카드)
# 2026/10/23: 전술 HUD 스타일 (지도 위 반투명 패널 + 앰버 강조색)
BG = "#101113"
PANEL = "rgba(20, 21, 23, 0.92)"
INPUT = "#17181b"
LINE = "#34342f"
SELECT = "rgba(227, 168, 59, 0.16)"
MUTED = "#8f8b80"
TEXT = "#dcd8cd"
STRONG = "#ffffff"
ACCENT = "#e3a83b"
DANGER = "#e5534b"

GRAYS = ["#ffffff", "#b3b3b3", "#808080", "#5c5c5c"]
DASHES = [Qt.SolidLine, Qt.DashLine, Qt.DotLine, Qt.DashDotLine]

# QGroupBox와 QFrame#card는 모두 둥근 카드로 그린다.
STYLE_SHEET = f"""
* {{ font-family: "Segoe UI", "Malgun Gothic"; font-size: 13px; }}
QWidget {{ background: transparent; color: {TEXT}; }}
QMainWindow {{ background: {BG}; }}
QFrame#card, QGroupBox {{ background: {PANEL}; border: 1px solid {LINE}; border-radius: 4px; }}
QFrame#hud {{ background: {PANEL}; border: 1px solid {LINE}; border-radius: 4px; margin: 12px; }}
QGroupBox {{ margin-top: 0; padding: 30px 8px 8px 8px; }}
QGroupBox::title {{
    subcontrol-origin: padding; subcontrol-position: top left; left: 10px; top: 8px;
    color: {ACCENT}; font-weight: 700; font-size: 13px;
}}
QFrame#divider {{ background: {LINE}; border: 0; max-height: 1px; min-height: 1px; }}
QLabel#title {{ color: {STRONG}; font-size: 18px; font-weight: 800; }}
QLabel#logo {{ color: {ACCENT}; font-size: 20px; }}
QLabel#badge {{ background: {INPUT}; color: {ACCENT}; border: 1px solid {LINE}; border-radius: 4px; padding: 3px 10px; font-weight: 600; }}
QLabel#stat {{ background: {INPUT}; border: 1px solid {LINE}; border-radius: 4px; padding: 4px 10px; font-size: 15px; font-weight: 700; color: {STRONG}; }}
QLabel[accent="true"] {{ color: {ACCENT}; font-weight: 600; }}
QLineEdit, QDoubleSpinBox, QComboBox, QPlainTextEdit, QListWidget, QTableWidget {{
    background: {INPUT}; border: 1px solid {LINE}; border-radius: 6px; padding: 3px;
}}
QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus, QPlainTextEdit:focus {{ border-color: {ACCENT}; }}
QComboBox QAbstractItemView {{ background: {INPUT}; border: 1px solid {LINE}; selection-background-color: {SELECT}; }}
QToolTip {{ background: {INPUT}; color: {TEXT}; border: 1px solid {ACCENT}; padding: 4px; }}
QPushButton {{ background: #222320; border: 1px solid {LINE}; border-radius: 4px; padding: 6px 12px; }}
QPushButton:hover {{ border-color: {ACCENT}; color: {STRONG}; }}
QPushButton:disabled {{ color: {MUTED}; }}
QPushButton#tab {{ background: {INPUT}; border: 1px solid {LINE}; color: {MUTED}; font-weight: 700; padding: 5px 12px; }}
QPushButton#tab:hover {{ color: {TEXT}; }}
QPushButton#tab:checked {{ background: {SELECT}; border-color: {ACCENT}; color: {ACCENT}; }}
QPushButton#primary {{ background: {ACCENT}; border: 0; color: #15130e; font-size: 14px; font-weight: 800; padding: 7px 16px; }}
QPushButton#primary:hover {{ background: #f0bd5c; }}
QListWidget#nav {{ background: transparent; border: 0; }}
QListWidget#nav::item {{ padding: 7px 8px; border-left: 2px solid transparent; }}
QListWidget#nav::item:hover {{ background: #222320; }}
QListWidget#nav::item:selected {{ border-left: 2px solid {ACCENT}; }}
QListWidget::item {{ padding: 3px; }}
QListWidget::item:selected, QTableWidget::item:selected {{ background: {SELECT}; color: {ACCENT}; }}
QHeaderView::section {{ background: {INPUT}; color: {MUTED}; border: 0; border-bottom: 1px solid {LINE}; padding: 3px; }}
QSplitter::handle:horizontal {{ width: 10px; }}
QScrollArea {{ border: 0; }}
QLabel[muted="true"] {{ color: {MUTED}; }}
QScrollBar {{ background: transparent; width: 8px; height: 8px; }}
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
