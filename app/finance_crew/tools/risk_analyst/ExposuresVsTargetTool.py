from crewai.tools import BaseTool
from typing import Type, Dict
from pydantic import BaseModel, Field
import json

class ExposuresVsTargetInput(BaseModel):
    """Compute asset-class exposures and deltas vs target."""
    weights_json: str = Field(..., description="JSON dict {ticker: weight}.")
    asset_map_json: str = Field(..., description="JSON dict {ticker: asset_class} (e.g., equity/bond/cash).")
    target_weights_json: str = Field(..., description="JSON dict {ticker: target_weight} summing ~1.")

class ExposuresVsTargetTool(BaseTool):
    name: str = "compute_exposures_vs_target"
    description: str = (
        "Aggregate current weights by asset class and compare to target weights (also aggregated). "
        "Returns JSON with current_exposures, target_exposures, and deltas."
    )
    args_schema: Type[BaseModel] = ExposuresVsTargetInput

    def _run(self, weights_json: str, asset_map_json: str, target_weights_json: str) -> str:
        try:
            w = json.loads(weights_json)
            amap = json.loads(asset_map_json)
            tw = json.loads(target_weights_json)

            cur_agg = {}
            tgt_agg = {}
            for t, weight in w.items():
                cls = amap.get(t, "unknown")
                cur_agg[cls] = cur_agg.get(cls, 0.0) + float(weight)
            for t, weight in tw.items():
                cls = amap.get(t, "unknown")
                tgt_agg[cls] = tgt_agg.get(cls, 0.0) + float(weight)

            keys = set(cur_agg.keys()) | set(tgt_agg.keys())
            deltas = {k: float(cur_agg.get(k, 0.0) - tgt_agg.get(k, 0.0)) for k in keys}

            return json.dumps({
                "ok": True,
                "current_exposures": {k: round(float(cur_agg.get(k, 0.0)), 6) for k in keys},
                "target_exposures": {k: round(float(tgt_agg.get(k, 0.0)), 6) for k in keys},
                "deltas": {k: round(v, 6) for k in deltas}
            })
        except Exception as e:
            return json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"})
