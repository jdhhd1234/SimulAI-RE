import importlib
import inspect
import math

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from calc.webapi.model_registry import MODEL_REGISTRY

#uvicorn calc.webapi.base_api:app --reload
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5500", "http://localhost:5500"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/check")
def check():
    return {"message": "Python API 응답 성공!"}


def _load_entry(model_id: str):
    entry = MODEL_REGISTRY.get(model_id)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"Unknown model id: {model_id}")
    module = importlib.import_module(entry["module"])
    init_cls = getattr(module, entry["class"])
    if not hasattr(init_cls, entry["builder"]):
        raise HTTPException(status_code=500, detail=f"Registry builder '{entry['builder']}' not found for {model_id}")
    _validate_registry_signature(model_id, entry, init_cls)
    return entry, init_cls


def _constructor_keys(init_cls) -> list[str]:
    sig = inspect.signature(init_cls)
    return [name for name, p in sig.parameters.items() if name != "self" and p.kind in (p.POSITIONAL_OR_KEYWORD, p.KEYWORD_ONLY)]


def _validate_registry_signature(model_id: str, entry: dict, init_cls) -> None:
    signature_keys = _constructor_keys(init_cls)
    registry_keys = list(entry.get("inputs", {}).keys())
    missing = [key for key in signature_keys if key not in registry_keys]
    extra = [key for key in registry_keys if key not in signature_keys]
    if missing or extra:
        raise HTTPException(
            status_code=500,
            detail=f"Registry/signature mismatch for {model_id}: missing={missing}, extra={extra}",
        )


def _elements(model, group: str) -> list[str]:
    return list(getattr(model, group, {}).keys())


GROUP_TITLES = {
    "stocks": "저장량",
    "flows": "흐름",
    "converters": "변환값",
    "constants": "상수",
}

MAX_SIMULATION_SAMPLES = 10_000


def _charts(model, entry: dict) -> list[dict]:
    outputs = entry.get("outputs", {})
    charts = []
    for group in ("stocks", "flows", "converters", "constants"):
        series = [
            {"key": key, "label": outputs.get(key, {}).get("label", key), "color": outputs.get(key, {}).get("color")}
            for key in _elements(model, group)
        ]
        if series:
            charts.append({"id": group, "title": GROUP_TITLES[group], "series": series})
    return charts


def _schema_inputs(entry: dict, init_cls) -> list[dict]:
    return [{"name": key, "type": "number", **entry["inputs"][key]} for key in _constructor_keys(init_cls)]


def _validate_payload(entry: dict, init_cls, payload: dict) -> dict[str, float]:
    required = _constructor_keys(init_cls)
    missing = [k for k in required if k not in payload]
    unknown = [k for k in payload if k not in required]
    if missing or unknown:
        raise HTTPException(status_code=422, detail={"missing": missing, "unknown": unknown})
    values = {}
    for key in required:
        value = payload[key]
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
            raise HTTPException(status_code=422, detail=f"{key} must be a finite number")
        bounds = entry["inputs"][key]
        if "min" in bounds and value < bounds["min"]:
            raise HTTPException(status_code=422, detail=f"{key} must be >= {bounds['min']}")
        if "max" in bounds and value > bounds["max"]:
            raise HTTPException(status_code=422, detail=f"{key} must be <= {bounds['max']}")
        values[key] = float(value)
    return values


def _validate_model_time_range(model) -> None:
    def finite_time_value(key: str) -> float:
        value = getattr(model, key, None)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(value):
            raise HTTPException(status_code=422, detail=f"model {key} must be a finite number")
        return float(value)

    starttime = finite_time_value("starttime")
    stoptime = finite_time_value("stoptime")
    dt = finite_time_value("dt")
    if dt <= 0:
        raise HTTPException(status_code=422, detail="model dt must be greater than 0")
    if stoptime < starttime:
        raise HTTPException(status_code=422, detail="model stoptime must be greater than or equal to starttime")
    sample_count = math.floor((stoptime - starttime) / dt) + 1
    if sample_count > MAX_SIMULATION_SAMPLES:
        raise HTTPException(
            status_code=422,
            detail=f"model time range produces {sample_count} samples; maximum is {MAX_SIMULATION_SAMPLES}",
        )


def _json_value(value):
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value) if math.isfinite(value) else None
    return value


def _simulate(model) -> list[dict[str, float | None]]:
    equations = _elements(model, "stocks") + _elements(model, "flows") + _elements(model, "converters") + _elements(model, "constants")
    df = model.simulate(equations=equations)
    df = df.rename_axis("time").reset_index()
    return [{k: _json_value(v) for k, v in row.items()} for row in df.to_dict(orient="records")]


@app.get("/models")
def list_models():
    return {"models": [{"id": e["id"], "name": e["name"], "description": e.get("description", "")} for e in MODEL_REGISTRY.values()]}


@app.get("/models/{model_id}/schema")
def model_schema(model_id: str):
    entry, init_cls = _load_entry(model_id)
    defaults = {k: v["default"] for k, v in entry["inputs"].items()}
    defaults = _validate_payload(entry, init_cls, defaults)
    model = getattr(init_cls(**defaults), entry["builder"])()
    _validate_model_time_range(model)
    return {"id": entry["id"], "name": entry["name"], "description": entry.get("description", ""), "inputs": _schema_inputs(entry, init_cls), "charts": _charts(model, entry)}


@app.post("/models/{model_id}/simulate")
def simulate_model(model_id: str, data: dict):
    entry, init_cls = _load_entry(model_id)
    values = _validate_payload(entry, init_cls, data)
    model = getattr(init_cls(**values), entry["builder"])()
    _validate_model_time_range(model)
    return {"model": model.name, "starttime": model.starttime, "stoptime": model.stoptime, "dt": model.dt, "results": _simulate(model)}


@app.post("/main")
def main(data: dict):
    """Compatibility endpoint for the default registered model."""
    return simulate_model("company_model", data)
