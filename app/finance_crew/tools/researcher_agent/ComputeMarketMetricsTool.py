from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import json
import math

class ComputeMetricsInput(BaseModel):
    """Input schema for computing market metrics."""
    prices_json: str = Field(..., description="JSON with 'index' and 'data' (as returned by fetch_yfinance_prices).")


class ComputeMarketMetricsTool(BaseTool):
    name: str = "compute_market_metrics"
    description: str = (
        "Compute last price, mean daily return, and annualized volatility (std*sqrt(252)) "
        "from historical prices JSON. Returns JSON: {ticker: {last_price, mean_ret, ann_vol}}."
    )
    args_schema: Type[BaseModel] = ComputeMetricsInput

    def _run(self, prices_json: str) -> str:
        try:
            obj = json.loads(prices_json)
            if not obj.get("ok", False):
                return json.dumps({"ok": False, "error": obj.get("error", "prices_json not ok")})
            index = obj.get("index", [])
            data = obj.get("data", {})
            if not index or not isinstance(data, dict):
                return json.dumps({"ok": False, "error": "Invalid prices_json structure."})
            result = {}
            trading_days = 252.0

            for ticker, series in data.items():
                prices = [float(x) for x in series if x is not None]
                if len(prices) < 2:
                    result[ticker] = {"last_price": (prices[-1] if prices else None),
                                      "mean_ret": None, "ann_vol": None}
                    continue

                last_price = prices[-1]
                rets = []
                for i in range(1, len(prices)):
                    p0, p1 = prices[i-1], prices[i]
                    if p0 and p0 > 0:
                        rets.append((p1 - p0) / p0)
                if len(rets) == 0:
                    result[ticker] = {"last_price": last_price, "mean_ret": None, "ann_vol": None}
                    continue

                mean_ret = sum(rets) / len(rets)
                mu = mean_ret
                var = sum((r - mu) ** 2 for r in rets) / (len(rets) - 1) if len(rets) > 1 else 0.0
                std = math.sqrt(var)
                ann_vol = std * math.sqrt(trading_days)

                result[ticker] = {
                    "last_price": round(last_price, 6),
                    "mean_ret": round(mean_ret, 8),
                    "ann_vol": round(ann_vol, 6),
                }

            return json.dumps({"ok": True, "metrics": result})
        except Exception as e:
            return json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"})
