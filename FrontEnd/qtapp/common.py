import math

import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView

# 지도/Lua 화면 공용 함수 (흑백 테마) (구 main/common.js)
BG = "#000000"
PANEL = "#0d0d0d"
LINE = "#262626"
MUTED = "#7a7a7a"
TEXT = "#e6e6e6"
STRONG = "#ffffff"

GRAYS = ["#ffffff", "#b3b3b3", "#808080", "#5c5c5c"]
DASHES = [Qt.SolidLine, Qt.DashLine, Qt.DotLine, Qt.DashDotLine]

STYLE_SHEET = f"""
* {{ font-family: "Segoe UI", "Malgun Gothic"; font-size: 13px; }}
QWidget {{ background: {BG}; color: {TEXT}; }}
QTabWidget::pane {{ border-top: 1px solid {LINE}; }}
QTabBar::tab {{ background: {BG}; color: {MUTED}; padding: 6px 14px; border: 1px solid transparent; }}
QTabBar::tab:selected, QTabBar::tab:hover {{ color: {STRONG}; border-color: {LINE}; }}
QGroupBox {{ border: 1px solid {LINE}; margin-top: 18px; padding: 8px; }}
QGroupBox::title {{ subcontrol-origin: margin; left: 8px; color: {STRONG}; font-weight: 600; }}
QLineEdit, QDoubleSpinBox, QComboBox, QPlainTextEdit, QListWidget, QTableWidget {{
    background: {PANEL}; border: 1px solid {LINE}; padding: 3px;
}}
QPushButton {{ background: {PANEL}; border: 1px solid {LINE}; padding: 4px 10px; }}
QPushButton:hover {{ background: {LINE}; color: {STRONG}; }}
QPushButton:disabled {{ color: {MUTED}; }}
QListWidget::item:selected, QTableWidget::item:selected {{ background: {LINE}; color: {STRONG}; }}
QHeaderView::section {{ background: {PANEL}; color: {MUTED}; border: 0; border-bottom: 1px solid {LINE}; padding: 3px; }}
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
