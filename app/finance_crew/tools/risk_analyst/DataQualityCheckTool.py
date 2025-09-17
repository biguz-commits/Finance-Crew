from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import json

class DataQualityCheckInput(BaseModel):
    """Validate weights sum and basic data completeness."""
    prices_json: str = Field(..., description="JSON with 'index' and 'data' (ticker->price list).")
    weights_json: str = Field(..., description="JSON dict {ticker: weight}.")
    tolerance: float = Field(0.02, description="Allowed deviation for weights sum around 1.0.")

class DataQualityCheckTool(BaseTool):
    name: str = "validate_portfolio_data_quality"
    description: str = (
        "Validate that portfolio weights sum ~ 1.0 and report missing data counts per ticker. "
        "Returns JSON with 'issues' (list of strings) and simple stats."
    )
    args_schema: Type[BaseModel] = DataQualityCheckInput

    def _run(self, prices_json: str, weights_json: str, tolerance: float = 0.02) -> str:
        try:
            obj = json.loads(prices_json)
            w = json.loads(weights_json)

            issues = []
            wsum = sum(float(x) for x in w.values())
            if not (1.0 - tolerance <= wsum <= 1.0 + tolerance):
                issues.append(f"Weights sum out of bounds: {wsum:.6f}")

            data = obj.get("data", {})
            missing = {}
            for t, series in data.items():
                mc = sum(1 for v in series if v is None)
                missing[t] = mc
                if mc > 0:
                    issues.append(f"{t}: {mc} missing price points")

            return json.dumps({
                "ok": True,
                "weights_sum": round(float(wsum), 6),
                "missing_points": missing,
                "issues": issues
            })
        except Exception as e:
            return json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"})
