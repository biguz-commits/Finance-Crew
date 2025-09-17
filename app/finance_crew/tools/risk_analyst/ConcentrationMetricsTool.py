from crewai.tools import BaseTool
from typing import Type, List, Tuple
from pydantic import BaseModel, Field
import json

class ConcentrationMetricsInput(BaseModel):
    """Compute concentration metrics from weights."""
    weights_json: str = Field(..., description="JSON dict {ticker: weight}.")
    top_k: int = Field(5, description="How many top positions to return.")

class ConcentrationMetricsTool(BaseTool):
    name: str = "compute_concentration_metrics"
    description: str = (
        "Compute concentration metrics (Top-K weights and HHI). "
        "Returns JSON with top_k list [[ticker, weight], ...] and hhi."
    )
    args_schema: Type[BaseModel] = ConcentrationMetricsInput

    def _run(self, weights_json: str, top_k: int = 5) -> str:
        try:
            w = json.loads(weights_json)
            items = sorted(((t, float(x)) for t, x in w.items()), key=lambda x: x[1], reverse=True)
            top = items[:max(1, top_k)]
            hhi = sum(x[1]**2 for x in items)

            return json.dumps({
                "ok": True,
                "top_k": [[t, round(v, 6)] for t, v in top],
                "hhi": round(float(hhi), 6)
            })
        except Exception as e:
            return json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"})
