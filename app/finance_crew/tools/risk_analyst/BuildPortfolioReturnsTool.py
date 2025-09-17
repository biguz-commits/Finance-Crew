from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import json

class BuildPortfolioReturnsInput(BaseModel):
    """Input schema to compute portfolio daily returns from prices and weights."""
    prices_json: str = Field(..., description="JSON with 'index' and 'data' (ticker->price list).")
    weights_json: str = Field(..., description="JSON dict {ticker: weight} that sums approx to 1.0.")

class BuildPortfolioReturnsTool(BaseTool):
    name: str = "build_portfolio_returns"
    description: str = (
        "Compute daily portfolio returns from historical prices and current weights. "
        "Returns JSON with 'index', 'portfolio_returns', and 'portfolio_curve' (cumprod)."
    )
    args_schema: Type[BaseModel] = BuildPortfolioReturnsInput

    def _run(self, prices_json: str, weights_json: str) -> str:
        try:
            obj = json.loads(prices_json)
            if not obj.get("ok", False):
                return json.dumps({"ok": False, "error": obj.get("error", "prices_json not ok")})
            dates = obj.get("index", [])
            data = obj.get("data", {})
            weights = json.loads(weights_json)

            tickers = [t for t in data.keys() if t in weights and weights[t] is not None]
            if not tickers:
                return json.dumps({"ok": False, "error": "No overlapping tickers between prices and weights."})

            per_ticker_returns = {}
            n = None
            for t in tickers:
                series = [None if v is None else float(v) for v in data[t]]
                rets = []
                for i in range(1, len(series)):
                    p0, p1 = series[i-1], series[i]
                    if p0 is None or p1 is None or p0 == 0:
                        rets.append(None)
                    else:
                        rets.append((p1 - p0) / p0)
                per_ticker_returns[t] = rets
                n = len(rets)

            wsum = sum(float(weights[t]) for t in tickers)
            if not (0.98 <= wsum <= 1.02):
                weights = {t: float(weights[t]) / wsum for t in tickers}
            else:
                weights = {t: float(weights[t]) for t in tickers}

            port_rets = []
            for i in range(n):
                valid = True
                acc = 0.0
                for t in tickers:
                    r = per_ticker_returns[t][i]
                    if r is None:
                        valid = False
                        break
                    acc += weights[t] * r
                port_rets.append(acc if valid else None)
            port_rets = [0.0 if r is None else float(r) for r in port_rets]

            curve = []
            level = 1.0
            for r in port_rets:
                level *= (1.0 + r)
                curve.append(level)

            return json.dumps({
                "ok": True,
                "index": dates[1:],
                "portfolio_returns": [round(float(x), 10) for x in port_rets],
                "portfolio_curve": [round(float(x), 10) for x in curve]
            })
        except Exception as e:
            return json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"})
