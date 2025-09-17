from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import json
import math
from scipy.stats import norm

class PortfolioRiskMetricsInput(BaseModel):
    """Input schema for portfolio risk metrics."""
    portfolio_returns_json: str = Field(..., description="JSON with 'index' and 'portfolio_returns' from build_portfolio_returns.")
    annualize_var: bool = Field(True, description="If true, also return annualized VaR via sqrt(252) scaling.")
    var_conf: float = Field(0.95, description="Confidence level for parametric VaR (default 0.95).")

class PortfolioRiskMetricsTool(BaseTool):
    name: str = "compute_portfolio_risk_metrics"
    description: str = (
        "Compute portfolio annualized volatility, max drawdown (from curve), and parametric VaR at given confidence. "
        "Returns JSON with ann_vol, max_drawdown, var_daily, var_annual (if requested)."
    )
    args_schema: Type[BaseModel] = PortfolioRiskMetricsInput

    def _run(self, portfolio_returns_json: str, annualize_var: bool = True, var_conf: float = 0.95) -> str:
        try:
            obj = json.loads(portfolio_returns_json)
            if not obj.get("ok", False):
                return json.dumps({"ok": False, "error": obj.get("error", "portfolio_returns_json not ok")})
            rets = [float(x) for x in obj.get("portfolio_returns", [])]
            curve = obj.get("portfolio_curve", [])

            if not rets:
                return json.dumps({"ok": False, "error": "Empty returns series."})

            mu = sum(rets)/len(rets)
            var = sum((r - mu)**2 for r in rets)/(len(rets)-1) if len(rets) > 1 else 0.0
            std = math.sqrt(var)
            ann_vol = std*math.sqrt(252.0)

            if not curve:
                lvl = 1.0
                curve = []
                for r in rets:
                    lvl *= (1.0 + r)
                    curve.append(lvl)

            peak = -1e18
            mdd = 0.0
            for v in curve:
                if v > peak:
                    peak = v
                dd = (v/peak) - 1.0
                if dd < mdd:
                    mdd = dd

            try:
                z = abs(norm.ppf(1 - var_conf))
            except Exception:
                z = 1.65 if abs(var_conf - 0.95) < 1e-6 else 1.65
            var_daily = mu - z*std
            var_annual = var_daily*math.sqrt(252.0) if annualize_var else None

            return json.dumps({
                "ok": True,
                "metrics": {
                    "ann_vol": round(ann_vol, 6),
                    "max_drawdown": round(float(mdd), 6),
                    "var95_daily": round(var_daily, 6) if abs(var_conf-0.95) < 1e-6 else round(var_daily, 6),
                    "var_annual": round(var_annual, 6) if var_annual is not None else None,
                    "conf_level": var_conf
                }
            })
        except Exception as e:
            return json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"})
