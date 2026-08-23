import importlib.util
import json
import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

BPTK_AVAILABLE = importlib.util.find_spec("BPTK_Py") is not None

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from calc.webapi.base_api import app
from calc.webapi.model_registry import MODEL_REGISTRY

client = TestClient(app)


class AlternateInitValue:
    def __init__(self, tiny_seed):
        self.tiny_seed = tiny_seed

    def TinySystem(self):
        from BPTK_Py import Model

        model = Model(starttime=2.0, stoptime=3.0, dt=1.0, name="Alternate Tiny Model")
        stock = model.stock("tiny_stock")
        stock.initial_value = self.tiny_seed
        flow = model.flow("tiny_flow")
        flow.equation = 1.0
        stock.equation = flow
        return model


def default_payload():
    return {key: meta["default"] for key, meta in MODEL_REGISTRY["company_model"]["inputs"].items()}


@unittest.skipUnless(BPTK_AVAILABLE, "BPTK_Py is required for real model API tests")
class BaseApiTests(unittest.TestCase):
    def test_check_kept(self):
        response = client.post("/check")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["message"])

    def test_models_lists_company_model(self):
        response = client.get("/models")
        self.assertEqual(response.status_code, 200)
        models = response.json()["models"]
        self.assertTrue(any(model["id"] == "company_model" for model in models))

    def test_company_model_schema_matches_frontend_contract(self):
        response = client.get("/models/company_model/schema")
        self.assertEqual(response.status_code, 200)
        schema = response.json()

        self.assertEqual(schema["id"], "company_model")
        self.assertEqual([item["name"] for item in schema["inputs"]], list(default_payload().keys()))
        self.assertTrue(all("key" not in item for item in schema["inputs"]))

        self.assertIsInstance(schema["charts"], list)
        self.assertEqual(
            [(chart["id"], chart["title"]) for chart in schema["charts"]],
            [("stocks", "저장량"), ("flows", "흐름"), ("converters", "변환값")],
        )
        for chart in schema["charts"]:
            self.assertEqual(set(chart), {"id", "title", "series"})
            self.assertTrue(chart["series"])
            for series in chart["series"]:
                self.assertEqual(set(series), {"key", "label", "color"})

        by_id = {chart["id"]: chart for chart in schema["charts"]}
        self.assertIn("cash", [item["key"] for item in by_id["stocks"]["series"]])
        self.assertIn("factory_production", [item["key"] for item in by_id["flows"]["series"]])
        self.assertIn("profit", [item["key"] for item in by_id["converters"]["series"]])

    def test_company_model_simulation_returns_time_key(self):
        response = client.post("/models/company_model/simulate", json=default_payload())
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["model"], "Simple Economic Model")
        self.assertEqual(body["starttime"], 0.0)
        self.assertAlmostEqual(body["stoptime"], 5.0)
        self.assertAlmostEqual(body["dt"], 0.1)
        self.assertTrue(body["results"])
        self.assertTrue({"time", "cash", "debt", "profit"}.issubset(body["results"][0]))
        self.assertNotIn("t", body["results"][0])

    def test_simulation_rejects_missing_key(self):
        payload = default_payload()
        payload.pop("cash_init")
        response = client.post("/models/company_model/simulate", json=payload)
        self.assertEqual(response.status_code, 422)
        self.assertIn("cash_init", response.text)

    def test_simulation_rejects_unknown_key(self):
        payload = default_payload()
        payload["unknown"] = 1.0
        response = client.post("/models/company_model/simulate", json=payload)
        self.assertEqual(response.status_code, 422)
        self.assertIn("unknown", response.text)

    def test_simulation_rejects_nonfinite_value(self):
        payload = default_payload()
        payload["cash_init"] = float("nan")
        response = client.post(
            "/models/company_model/simulate",
            content=json.dumps(payload, allow_nan=True),
            headers={"content-type": "application/json"},
        )
        self.assertEqual(response.status_code, 422)
        self.assertIn("finite", response.text)

    def test_simulation_rejects_bounds(self):
        payload = default_payload()
        payload["deltatime"] = 0.0
        response = client.post("/models/company_model/simulate", json=payload)
        self.assertEqual(response.status_code, 422)
        self.assertIn("deltatime", response.text)

    def test_simulation_rejects_excessive_samples(self):
        payload = default_payload()
        payload["stoptime"] = 10001.0
        payload["deltatime"] = 1.0
        response = client.post("/models/company_model/simulate", json=payload)
        self.assertEqual(response.status_code, 422)
        self.assertIn("maximum is 10000", response.text)

    def test_alternate_constructor_and_builder_are_generic(self):
        entry = {
            "id": "alternate_tiny",
            "name": "Alternate Tiny",
            "description": "Uses a non-company constructor and builder.",
            "module": __name__,
            "class": "AlternateInitValue",
            "builder": "TinySystem",
            "inputs": {
                "tiny_seed": {
                    "label": "Tiny seed",
                    "default": 4.0,
                    "min": 0.0,
                    "step": 1.0,
                }
            },
            "outputs": {
                "tiny_stock": {"label": "Tiny stock", "color": "#000000"},
                "tiny_flow": {"label": "Tiny flow", "color": "#111111"},
            },
        }
        previous = MODEL_REGISTRY.get(entry["id"])
        MODEL_REGISTRY[entry["id"]] = entry
        try:
            models_response = client.get("/models")
            self.assertEqual(models_response.status_code, 200)
            self.assertTrue(any(model["id"] == entry["id"] for model in models_response.json()["models"]))

            schema_response = client.get("/models/alternate_tiny/schema")
            self.assertEqual(schema_response.status_code, 200)
            schema = schema_response.json()
            self.assertEqual([item["name"] for item in schema["inputs"]], ["tiny_seed"])
            self.assertIn("stocks", [chart["id"] for chart in schema["charts"]])

            simulate_response = client.post("/models/alternate_tiny/simulate", json={"tiny_seed": 4.0})
            self.assertEqual(simulate_response.status_code, 200)
            body = simulate_response.json()
            self.assertEqual(body["model"], "Alternate Tiny Model")
            self.assertEqual(body["starttime"], 2.0)
            self.assertEqual(body["stoptime"], 3.0)
            self.assertEqual(body["dt"], 1.0)
            self.assertTrue({"time", "tiny_stock", "tiny_flow"}.issubset(body["results"][0]))
        finally:
            if previous is None:
                MODEL_REGISTRY.pop(entry["id"], None)
            else:
                MODEL_REGISTRY[entry["id"]] = previous

    def test_unknown_model_404(self):
        response = client.get("/models/nope/schema")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
