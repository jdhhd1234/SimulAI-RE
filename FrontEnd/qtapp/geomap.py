import json
import math
from pathlib import Path

import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal, QPointF
from PySide6.QtGui import QPainterPath, QPolygonF, QCursor, QColor
from PySide6.QtWidgets import QGraphicsPathItem, QToolTip

from FrontEnd.qtapp.common import BG

# 지도 로직 (구 geomap/geo_main.js). 경도 = x, 위도 = y 로 그대로 그린다.
# 페이지와는 아래 함수와 Signal로만 주고받는다.
#   set_companies(companies), set_locations(locations), set_territories(territories),
#   set_selected(id), set_deposits(deposits, selected_id), pan_to(latitude, longitude)
#   Signal: company_clicked(id), deposit_clicked(id), map_clicked(latitude, longitude)
COUNTRIES_PATH = Path(__file__).resolve().parents[1] / "geomap" / "countries.geojson"

COUNTRY_EMPTY = "#202122"
COUNTRY_OWNED = "#4a3d26"
COUNTRY_SELECTED = "#8a6a2e"
COUNTRY_LINE = "#3a3a36"
MARKER = "#e3a83b"


class GeoMap(pg.PlotWidget):
    company_clicked = Signal(str)
    deposit_clicked = Signal(str)
    map_clicked = Signal(float, float)

    def __init__(self):
        super().__init__(background=BG)
        self.hideAxis("left")
        self.hideAxis("bottom")
        self.setMenuEnabled(False)
        self.hideButtons()
        self.setAspectLocked(True)
        self.getViewBox().setLimits(xMin=-200, xMax=200, yMin=-100, yMax=100)
        self.setRange(xRange=(-180, 180), yRange=(-60, 85), padding=0)

        self.territories = {}
        self.selected_id = None
        self.companies = []

        self.countries = []  # [(name, QGraphicsPathItem)]
        self._load_countries()

        # 광물/에너지 매장지: 원 크기 = 매장량(log), 광물 = 채운 원, 에너지 = 검은 원 + 흰 테두리
        self.deposit_points = pg.ScatterPlotItem(pxMode=True)
        self.location_points = pg.ScatterPlotItem(pxMode=True)
        self.company_points = pg.ScatterPlotItem(pxMode=True)
        for z, item in enumerate((self.deposit_points, self.location_points, self.company_points), start=1):
            item.setZValue(z)
            self.addItem(item)

        self.scene().sigMouseMoved.connect(self._on_move)
        self.scene().sigMouseClicked.connect(self._on_click)

    def _load_countries(self):
        features = json.loads(COUNTRIES_PATH.read_text(encoding="utf-8"))["features"]
        pen = pg.mkPen(COUNTRY_LINE, width=0.6)
        for feature in features:
            geometry = feature["geometry"]
            polygons = [geometry["coordinates"]] if geometry["type"] == "Polygon" else geometry["coordinates"]
            path = QPainterPath()
            path.setFillRule(Qt.OddEvenFill)
            for rings in polygons:
                for ring in rings:
                    path.addPolygon(QPolygonF([QPointF(lon, lat) for lon, lat in ring]))
            item = QGraphicsPathItem(path)
            item.setPen(pen)
            item.setBrush(pg.mkBrush(COUNTRY_EMPTY))
            self.addItem(item)
            self.countries.append((feature["properties"]["name"], item))

    # ---------- 영토 / 선택 ----------

    def _refresh_countries(self):
        """영토 색상: 자산이 점유한 국가는 밝게, 선택된 자산의 영토는 더 밝게"""
        for name, item in self.countries:
            owner = self.territories.get(name)
            if owner is None:
                color = COUNTRY_EMPTY
            else:
                color = COUNTRY_SELECTED if owner["company_id"] == self.selected_id else COUNTRY_OWNED
            item.setBrush(pg.mkBrush(color))

    def set_territories(self, territories):
        self.territories = territories
        self._refresh_countries()

    def set_selected(self, company_id):
        self.selected_id = company_id
        self.set_companies(self.companies)
        self._refresh_countries()

    # ---------- 마커 ----------

    def set_companies(self, companies):
        self.companies = companies
        spots = []
        for company in companies:
            active = company["id"] == self.selected_id
            spots.append({
                "pos": (company["longitude"], company["latitude"]),
                "size": 14 if active else 8,
                "brush": pg.mkBrush(MARKER if active else "#000000"),
                "pen": pg.mkPen(MARKER, width=2 if active else 1),
                "data": company["id"],
            })
        self.company_points.setData(spots)

    def set_locations(self, locations):
        self.location_points.setData([{
            "pos": (location["longitude"], location["latitude"]),
            "size": 8,
            "brush": pg.mkBrush(None),
            "pen": pg.mkPen("#808080", width=1, style=Qt.DashLine),
            "data": location["name"],
        } for location in locations])

    def set_deposits(self, deposits, selected_id=None):
        """매장지 목록(필터 적용된 것)과 선택된 매장지 id를 지도에 반영"""
        spots = []
        for deposit in deposits:
            radius = 4 + min(max(math.log(deposit["reserve"] + 1) / 20, 0), 1) * 20
            fill = QColor("#000000" if deposit["category"] == "energy" else "#e6e6e6")
            fill.setAlphaF(0.8)
            spots.append({
                "pos": (deposit["longitude"], deposit["latitude"]),
                "size": radius * 2,
                "brush": pg.mkBrush(fill),
                "pen": pg.mkPen("#ffffff", width=3 if deposit["id"] == selected_id else 1),
                "data": deposit,
            })
        self.deposit_points.setData(spots)

    def pan_to(self, latitude, longitude):
        rect = self.getViewBox().viewRect()
        self.setRange(
            xRange=(longitude - rect.width() / 2, longitude + rect.width() / 2),
            yRange=(latitude - rect.height() / 2, latitude + rect.height() / 2),
            padding=0,
        )

    # ---------- 마우스 ----------

    def _points_at(self, item, view_pos):
        points = item.pointsAt(view_pos)
        return points[0].data() if len(points) else None

    def _on_move(self, scene_pos):
        """마우스를 올린 매장지/국가 이름 표시 (점유 중이면 자산 이름 포함)"""
        pos = self.getViewBox().mapSceneToView(scene_pos)
        deposit = self._points_at(self.deposit_points, pos)
        company = self._points_at(self.company_points, pos)

        if company is not None or deposit is not None:
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.unsetCursor()

        if company is not None:
            text = next((c["name"] for c in self.companies if c["id"] == company), company)
        elif deposit is not None:
            text = f"{deposit['name']} · {deposit['resource']} · {deposit['reserve']:,.0f}"
        else:
            name = next((name for name, item in self.countries if item.path().contains(pos)), None)
            owner = self.territories.get(name)
            text = f"{name} · {owner['company_name']}" if owner else name

        if text:
            QToolTip.showText(QCursor.pos(), text, self)
        else:
            QToolTip.hideText()

    def _on_click(self, event):
        """마커를 누르면 자산/매장지 선택, 그 외 지점을 누르면 좌표 전달(map_clicked)"""
        if event.button() != Qt.LeftButton or event.double():
            return
        pos = self.getViewBox().mapSceneToView(event.scenePos())

        company = self._points_at(self.company_points, pos)
        if company is not None:
            self.company_clicked.emit(company)
            return
        deposit = self._points_at(self.deposit_points, pos)
        if deposit is not None:
            self.deposit_clicked.emit(deposit["id"])
            return

        longitude = (pos.x() + 180) % 360 - 180
        latitude = max(-90.0, min(90.0, pos.y()))
        self.map_clicked.emit(latitude, longitude)
