from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QFormLayout, QGridLayout, QSplitter, QScrollArea,
    QGroupBox, QLabel, QLineEdit, QComboBox, QDoubleSpinBox, QPushButton, QListWidget, QListWidgetItem,
)

from FrontEnd.qtapp.common import fmt, make_plot, render_line_chart, make_table, render_table
from FrontEnd.qtapp.geomap import GeoMap

# 지도 화면 (구 main/main.js + company.js + location.js + deposit.js)
#   왼쪽: 자산 / 위치 추가 / 광물·에너지 매장지, 가운데: 지도, 오른쪽: 자산 정보 / 추이 / 턴별 데이터
DEPOSIT_CATEGORY = {"mineral": "광물", "energy": "에너지"}
# 자원 입력 추천 목록. 여기 없는 이름도 자유롭게 입력할 수 있다.
RESOURCE_PRESETS = {
    "iron": "mineral", "copper": "mineral", "chrome": "mineral", "nickel": "mineral", "lithium": "mineral",
    "cobalt": "mineral", "rare_earth": "mineral", "bauxite": "mineral", "gold": "mineral",
    "oil": "energy", "gas": "energy", "coal": "energy", "uranium": "energy", "carbon": "energy",
}
REFRESH_MS = 3000


def _spin(minimum, maximum, value=0.0, decimals=4):
    spin = QDoubleSpinBox()
    spin.setRange(minimum, maximum)
    spin.setDecimals(decimals)
    spin.setValue(value)
    return spin


def _render_metrics(grid, values):
    """{이름: 값}을 2열 격자로 그린다."""
    while grid.count():
        grid.takeAt(0).widget().deleteLater()
    for i, (key, value) in enumerate(values.items()):
        cell = QLabel(f"<span style='color:#7a7a7a'>{key}</span><br><b>{fmt(value)}</b>")
        grid.addWidget(cell, i // 2, i % 2)


class MapPage(QWidget):
    status = Signal(str, bool)

    def __init__(self, state):
        super().__init__()
        self.state = state
        self.selected_id = None
        self.selected_deposit_id = None
        self.company_ids = []

        self.map = GeoMap()
        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self._build_side())
        splitter.addWidget(self.map)
        splitter.addWidget(self._build_panel())
        splitter.setSizes([300, 900, 380])
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(splitter)

        self.map.company_clicked.connect(self.select_company)
        self.map.deposit_clicked.connect(self.edit_deposit)
        self.map.map_clicked.connect(self._on_map_click)

        self.load_locations()
        self.render_deposits()
        self.refresh()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(REFRESH_MS)

    # ---------- 레이아웃 ----------

    def _build_side(self):
        side = QWidget()
        layout = QVBoxLayout(side)

        # 자산
        box = QGroupBox("자산")
        box_layout = QVBoxLayout(box)
        self.company_list = QListWidget()
        self.company_list.itemClicked.connect(lambda item: self.select_company(item.data(Qt.UserRole)))
        delete_company = QPushButton("선택 자산 삭제")
        delete_company.clicked.connect(self._delete_selected_company)
        box_layout.addWidget(self.company_list)
        box_layout.addWidget(delete_company)
        layout.addWidget(box)

        # 위치 추가 (Lua locations 테이블)
        box = QGroupBox("위치 추가")
        form = QFormLayout(box)
        hint = QLabel("지도를 클릭하면 좌표가 입력됩니다. Lua의 locations 테이블로 전달됩니다.")
        hint.setWordWrap(True)
        hint.setProperty("muted", True)
        form.addRow(hint)
        self.location_name = QLineEdit()
        self.location_name.setPlaceholderText("포항")
        self.location_lat = _spin(-90, 90)
        self.location_lon = _spin(-180, 180)
        add_location = QPushButton("추가")
        add_location.clicked.connect(self._add_location)
        self.location_list = QListWidget()
        self.location_list.itemClicked.connect(
            lambda item: self.map.pan_to(*item.data(Qt.UserRole)[1:]))
        delete_location = QPushButton("선택 위치 삭제")
        delete_location.clicked.connect(self._delete_selected_location)
        form.addRow("이름", self.location_name)
        form.addRow("위도", self.location_lat)
        form.addRow("경도", self.location_lon)
        form.addRow(add_location)
        form.addRow(self.location_list)
        form.addRow(delete_location)
        layout.addWidget(box)

        # 2026/10/12: 광물/에너지 매장지 편집
        box = QGroupBox("광물 / 에너지 매장지")
        form = QFormLayout(box)
        hint = QLabel("지도를 클릭하면 좌표가 입력됩니다. 매장지를 누르면 수정할 수 있습니다. Lua의 deposits 테이블로 전달됩니다.")
        hint.setWordWrap(True)
        hint.setProperty("muted", True)
        form.addRow(hint)
        self.deposit_inputs = {
            "name": QLineEdit(),
            "category": QComboBox(),
            "resource": QComboBox(),
            "latitude": _spin(-90, 90),
            "longitude": _spin(-180, 180),
            "reserve": _spin(0, 1e15, 100000, 2),
            "extraction_capacity": _spin(0, 1e15, 1000, 2),
            "extraction_cost": _spin(0, 1e15, 10, 2),
            "processing_yield": _spin(0, 1e6, 1, 4),
        }
        self.deposit_inputs["name"].setPlaceholderText("필바라 철광산")
        for key, label in DEPOSIT_CATEGORY.items():
            self.deposit_inputs["category"].addItem(label, key)
        resource = self.deposit_inputs["resource"]
        resource.setEditable(True)
        resource.addItems(list(RESOURCE_PRESETS))
        resource.setCurrentText("")
        resource.lineEdit().setPlaceholderText("iron")
        # 추천 자원을 고르면 분류를 자동으로 맞춘다
        resource.currentTextChanged.connect(self._on_resource_changed)
        for key, label in (("name", "이름"), ("category", "분류"), ("resource", "자원"), ("latitude", "위도"),
                           ("longitude", "경도"), ("reserve", "매장량"), ("extraction_capacity", "채굴능력"),
                           ("extraction_cost", "채굴비용"), ("processing_yield", "가공수율")):
            form.addRow(label, self.deposit_inputs[key])

        buttons = QHBoxLayout()
        self.deposit_submit = QPushButton("추가")
        self.deposit_submit.clicked.connect(self._submit_deposit)
        self.deposit_cancel = QPushButton("취소")
        self.deposit_cancel.clicked.connect(self._reset_deposit_form)
        self.deposit_cancel.hide()
        buttons.addWidget(self.deposit_submit)
        buttons.addWidget(self.deposit_cancel)
        form.addRow(buttons)

        self.deposit_filter_category = QComboBox()
        self.deposit_filter_category.addItem("전체", "")
        for key, label in DEPOSIT_CATEGORY.items():
            self.deposit_filter_category.addItem(label, key)
        self.deposit_filter_resource = QComboBox()
        self.deposit_filter_resource.addItem("전체", "")
        self.deposit_filter_category.currentIndexChanged.connect(self.render_deposits)
        self.deposit_filter_resource.currentIndexChanged.connect(self.render_deposits)
        form.addRow("표시", self.deposit_filter_category)
        form.addRow("자원", self.deposit_filter_resource)

        self.deposit_totals = QGridLayout()
        form.addRow(self.deposit_totals)
        self.deposit_list = QListWidget()
        self.deposit_list.itemClicked.connect(lambda item: self.edit_deposit(item.data(Qt.UserRole)))
        delete_deposit = QPushButton("선택 매장지 삭제")
        delete_deposit.clicked.connect(self._delete_selected_deposit)
        form.addRow(self.deposit_list)
        form.addRow(delete_deposit)
        layout.addWidget(box)
        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setWidget(side)
        return scroll

    def _build_panel(self):
        panel = QWidget()
        layout = QVBoxLayout(panel)

        box = QGroupBox("자산 정보")
        box_layout = QVBoxLayout(box)
        self.detail_title = QLabel("자산 정보")
        self.detail_title.setStyleSheet("font-weight: 600; color: #ffffff;")
        self.detail_sub = QLabel("자산을 선택하세요.")
        self.detail_sub.setProperty("muted", True)
        self.metrics = QGridLayout()
        box_layout.addWidget(self.detail_title)
        box_layout.addWidget(self.detail_sub)
        box_layout.addLayout(self.metrics)
        layout.addWidget(box)

        box = QGroupBox("추이")
        self.chart = make_plot()
        self.chart.setMinimumHeight(260)
        QVBoxLayout(box).addWidget(self.chart)
        layout.addWidget(box, 1)

        box = QGroupBox("턴별 데이터")
        self.table = make_table()
        self.table.setMinimumHeight(240)
        QVBoxLayout(box).addWidget(self.table)
        layout.addWidget(box, 1)

        # 창이 작으면 패널이 잘리지 않고 스크롤되도록 한다.
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(panel)
        return scroll

    # ---------- 자산(companies) 목록 / 상세 / 영토 ----------

    def render_companies(self, companies):
        self.company_list.clear()
        if not companies:
            self.company_list.addItem("자산이 없습니다.")
        for company in companies:
            item = QListWidgetItem(f"{company['name']}\n{company['country']} · {company['id']}")
            item.setData(Qt.UserRole, company["id"])
            self.company_list.addItem(item)
            item.setSelected(company["id"] == self.selected_id)
        self.map.set_companies(companies)

    def refresh(self):
        companies = self.state.get_companies()
        ids = [company["id"] for company in companies]
        if ids != self.company_ids:
            self.company_ids = ids
            self.render_companies(companies)
        self.map.set_territories(self.state.get_territories())
        self.status.emit(f"연결됨 · 자산 {len(companies)}개", False)

    def select_company(self, company_id):
        company = self.state.get_company(company_id)
        if company is None:
            return
        self.selected_id = company_id
        self.render_companies(self.state.get_companies())
        self.map.set_selected(company_id)

        rows = company.get("data") or []
        self.detail_title.setText(company["name"])
        self.detail_sub.setText(f"{company['country']} · {fmt(company['latitude'])}, {fmt(company['longitude'])}")
        _render_metrics(self.metrics, rows[-1] if rows else {})

        keys = [key for key in (rows[0] if rows else {}) if key != "time" and isinstance(rows[0][key], (int, float))]
        render_line_chart(self.chart, [row["time"] for row in rows], {key: [row[key] for row in rows] for key in keys})
        render_table(self.table, rows)
        self.map.pan_to(company["latitude"], company["longitude"])

    def _delete_selected_company(self):
        # 목록을 누르면 render_companies가 목록을 다시 그려 currentItem이 사라지므로 선택 id로 지운다.
        company_id = self.selected_id
        if company_id is None:
            return
        self.state.delete_company(company_id)
        if self.selected_id == company_id:
            self.selected_id = None
            self.map.set_selected(None)
            self.chart.clear()
            _render_metrics(self.metrics, {})
            self.detail_title.setText("자산 정보")
            self.detail_sub.setText("자산을 선택하세요.")
            render_table(self.table, [])
        self.refresh()

    # ---------- 위치 추가 (Lua locations 테이블) ----------

    def load_locations(self):
        self.location_list.clear()
        for location in self.state.locations:
            item = QListWidgetItem(f"{location['name']}\n{fmt(location['latitude'])}, {fmt(location['longitude'])}")
            item.setData(Qt.UserRole, (location["id"], location["latitude"], location["longitude"]))
            self.location_list.addItem(item)
        self.map.set_locations(self.state.locations)

    def _add_location(self):
        self.state.add_location(self.location_name.text(), self.location_lat.value(), self.location_lon.value())
        self.location_name.clear()
        self.load_locations()

    def _delete_selected_location(self):
        item = self.location_list.currentItem()
        if item is not None:
            self.state.delete_location(item.data(Qt.UserRole)[0])
            self.load_locations()

    # ---------- 광물/에너지 매장지 ----------

    def render_deposits(self):
        deposits = self.state.deposits
        resource_names = sorted({deposit["resource"] for deposit in deposits})
        current_resource = self.deposit_filter_resource.currentData()
        self.deposit_filter_resource.blockSignals(True)
        self.deposit_filter_resource.clear()
        self.deposit_filter_resource.addItem("전체", "")
        for name in resource_names:
            self.deposit_filter_resource.addItem(name, name)
        self.deposit_filter_resource.setCurrentIndex(max(self.deposit_filter_resource.findData(current_resource), 0))
        self.deposit_filter_resource.blockSignals(False)

        category = self.deposit_filter_category.currentData()
        resource = self.deposit_filter_resource.currentData()
        visible = [deposit for deposit in deposits
                   if (not category or deposit["category"] == category)
                   and (not resource or deposit["resource"] == resource)]

        self.deposit_list.clear()
        if not visible:
            self.deposit_list.addItem("매장지가 없습니다.")
        for deposit in visible:
            item = QListWidgetItem(
                f"{deposit['name']}\n{DEPOSIT_CATEGORY[deposit['category']]} · {deposit['resource']} · {fmt(deposit['reserve'])}")
            item.setData(Qt.UserRole, deposit["id"])
            self.deposit_list.addItem(item)
            item.setSelected(deposit["id"] == self.selected_deposit_id)

        # 자원별 총 매장량 (현재 필터 기준)
        totals = {}
        for deposit in visible:
            key = f"{deposit['resource']} 총 매장량"
            totals[key] = totals.get(key, 0) + deposit["reserve"]
        _render_metrics(self.deposit_totals, totals)

        self.map.set_deposits(visible, self.selected_deposit_id)

    def edit_deposit(self, deposit_id):
        deposit = next((item for item in self.state.deposits if item["id"] == deposit_id), None)
        if deposit is None:
            return
        self.selected_deposit_id = deposit_id
        inputs = self.deposit_inputs
        inputs["name"].setText(deposit["name"])
        inputs["category"].setCurrentIndex(inputs["category"].findData(deposit["category"]))
        inputs["resource"].setCurrentText(deposit["resource"])
        for key in ("latitude", "longitude", "reserve", "extraction_capacity", "extraction_cost", "processing_yield"):
            inputs[key].setValue(deposit[key])
        self.deposit_submit.setText("수정")
        self.deposit_cancel.show()
        self.map.pan_to(deposit["latitude"], deposit["longitude"])
        self.render_deposits()

    def _reset_deposit_form(self):
        self.selected_deposit_id = None
        inputs = self.deposit_inputs
        inputs["name"].clear()
        inputs["category"].setCurrentIndex(0)
        inputs["resource"].setCurrentText("")
        for key, value in (("latitude", 0), ("longitude", 0), ("reserve", 100000),
                           ("extraction_capacity", 1000), ("extraction_cost", 10), ("processing_yield", 1)):
            inputs[key].setValue(value)
        self.deposit_submit.setText("추가")
        self.deposit_cancel.hide()
        self.render_deposits()

    def _submit_deposit(self):
        inputs = self.deposit_inputs
        values = {
            "name": inputs["name"].text(),
            "category": inputs["category"].currentData(),
            "resource": inputs["resource"].currentText(),
            **{key: inputs[key].value() for key in ("latitude", "longitude", "reserve", "extraction_capacity",
                                                    "extraction_cost", "processing_yield")},
        }
        try:
            if self.selected_deposit_id:
                self.state.update_deposit(self.selected_deposit_id, values)
            else:
                self.state.add_deposit(values)
        except ValueError as error:
            self.status.emit(str(error), True)
            return
        self._reset_deposit_form()

    def _delete_selected_deposit(self):
        # 목록을 누르면 render_deposits가 목록을 다시 그려 currentItem이 사라지므로 선택 id로 지운다.
        deposit_id = self.selected_deposit_id
        if deposit_id is None:
            return
        self.state.delete_deposit(deposit_id)
        if self.selected_deposit_id == deposit_id:
            self._reset_deposit_form()
        else:
            self.render_deposits()

    def _on_resource_changed(self, text):
        category = RESOURCE_PRESETS.get(text.strip())
        if category:
            self.deposit_inputs["category"].setCurrentIndex(self.deposit_inputs["category"].findData(category))

    # ---------- 지도 클릭 ----------

    def _on_map_click(self, latitude, longitude):
        self.location_lat.setValue(round(latitude, 4))
        self.location_lon.setValue(round(longitude, 4))
        self.deposit_inputs["latitude"].setValue(round(latitude, 4))
        self.deposit_inputs["longitude"].setValue(round(longitude, 4))
