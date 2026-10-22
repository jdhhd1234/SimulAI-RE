import json
import unittest
from unittest.mock import patch

from PySide6.QtWidgets import QApplication

from FrontEnd.qtapp.common import STYLE_SHEET
from FrontEnd.qtapp.debug_window import DebugWindow
from FrontEnd.qtapp.lua_page import LuaPage
from FrontEnd.qtapp.state import LuaRunError
from LuaPy.lua_bridge import LuaBridge


class DebugWindowTest(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])
        cls.app.setStyleSheet(STYLE_SHEET)

    def setUp(self):
        self.bridge = LuaBridge(0, 2, 1, "debug_test")
        self.bridge.lua.execute("""
            api.make_consumer_groups(3, 300, 0, 3)
            api.make_company("buyer")
            api.set_company("buyer", 500, {
                {name = "iron", price = 100},
                {name = "free", price = 0},
                {name = "invalid", price = -10}
            })
            api.make_converter("indicator", function(t) return 10 + t * 2 end)
        """)
        self.bridge.consumers[0].income = 100.0
        self.bridge.consumers[2].income = 500.0
        self.result = self.bridge.series()
        self.result.update(console=[], sectors=[], company_ids=[])
        self.window = DebugWindow()

    def tearDown(self):
        self.window.close()

    def test_decision_snapshots(self):
        json.dumps(self.result)
        groups = self.result["consumers"][0]["groups"]
        self.assertEqual([g["state"] for g in groups], ["saving", "normal", "spending"])
        self.assertEqual(groups[0]["decision"]["income"], 100)
        self.assertEqual(groups[0]["decision"]["fixcost"], 300)
        self.assertEqual(groups[0]["decision"]["previous_state"], "normal")
        self.assertEqual(self.result["consumers"][1]["groups"][0]["decision"]["previous_state"], "saving")
        company = self.result["companies"][0]["companies"][0]
        self.assertEqual(company["decisions"][0]["quantity"], 5)
        self.assertEqual(company["decisions"][1]["action"], "skip")
        self.assertEqual(company["decisions"][2]["action"], "skip")
        self.assertEqual(company["cash"], 500)
        self.bridge.companies["buyer"].decisions[0]["quantity"] = 999
        self.assertEqual(company["decisions"][0]["quantity"], 5)

    def test_browse_without_running_agents(self):
        with patch.object(self.bridge.consumers[0], "act", side_effect=AssertionError("rerun")):
            self.window.set_result(self.result, "test.lua")
            self.window.sample.setValue(1)
            self.assertEqual(self.window.indicator_table.item(0, 1).text(), "12")
            self.assertEqual(self.window.indicator_table.item(0, 3).text(), "2")
            self.assertEqual(self.window.agent_table.rowCount(), 6)
            self.assertEqual(self.window.agent_table.item(0, 5).text(), "소득 < 고정비")
            self.assertIn("실제 구매", self.window.agent_table.item(3, 6).text())
            self.window.show()
            self.window.close()
            self.window.show()
            self.window.sample.setValue(2)
        self.window.set_result({"time": [0], "series": {}}, "empty.lua")
        self.assertEqual(self.window.agent_table.rowCount(), 0)
        self.assertIn("ABM", self.window.time_label.text())
        self.window.set_result({"time": [], "series": {}}, "empty.lua")
        self.assertFalse(self.window.sample.isEnabled())
        self.assertEqual(self.window.indicator_table.rowCount(), 0)

    def test_lua_page_success_and_failure(self):
        result = self.result

        class State:
            def lua_files(self):
                return ["test.lua"]

            def lua_source(self, name):
                return "-- test"

            def run_lua(self, *args):
                return result

        state = State()
        page = LuaPage(state)
        try:
            page.run_lua()
            self.assertIs(page.debug_window.result, result)
            page.debug_button.click()
            self.assertTrue(page.debug_window.isVisible())
            with patch.object(state, "run_lua", side_effect=LuaRunError("failed", [])):
                page.run_lua()
            self.assertIn("실행 실패", page.debug_window.summary.text())
            self.assertIs(page.debug_window.result, result)
            self.assertTrue(page.run_button.isEnabled())
        finally:
            page.debug_window.close()
            page.close()


if __name__ == "__main__":
    unittest.main()
