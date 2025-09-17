from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import json

class BetaCorrelationInput(BaseModel):
    """Compute per-ticker beta vs benchmark and portfolio beta."""
    prices_json: str = Field(..., description="JSON with 'index' and 'data' (ticker->price list).")
    weights_json: str = Field(..., description="JSON dict {ticker: weight}.")
    benchmark: str = Field(..., description="Benchmark ticker present in prices_json data.")

class BetaCorrelationTool(BaseTool):
    name: str = "compute_beta_and_correlations"
    description: str = (
        "Compute per-ticker beta vs benchmark and approximate portfolio beta via weighted average. "
        "Also returns correlation of each ticker vs benchmark."
    )
    args_schema: Type[BaseModel] = BetaCorrelationInput

    def _run(self, prices_json: str, weights_json: str, benchmark: str) -> str:
        try:
            obj = json.loads(prices_json)
            if not obj.get("ok", False):
                return json.dumps({"ok": False, "error": obj.get("error", "prices_json not ok")})
            data = obj.get("data", {})
            weights = json.loads(weights_json)

            if benchmark not in data:
                return json.dumps({"ok": False, "error": f"Benchmark '{benchmark}' not in prices data."})

            def series_to_returns(series):
                rets = []
                prev = None
                for v in series:
                    if v is None or prev is None or prev == 0:
                        prev = v
                        continue
                    rets.append((float(v)-float(prev))/float(prev))
                    prev = v
                return rets

            bench_rets = series_to_returns(data[benchmark])
            if len(bench_rets) < 3:
                return json.dumps({"ok": False, "error": "Not enough benchmark data to compute beta."})

            import statistics
            vb = statistics.pvariance(bench_rets)
            if vb == 0:
                return json.dumps({"ok": False, "error": "Zero variance on benchmark returns."})

            betas = {}
            cors = {}
            for t, series in data.items():
                if t == benchmark:
                    continue
                r = series_to_returns(series)
                n = min(len(r), len(bench_rets))
                if n < 3:
                    betas[t] = None
                    cors[t] = None
                    continue
                r = r[-n:]
                b = bench_rets[-n:]
                mu_r = statistics.mean(r)
                mu_b = statistics.mean(b)
                cov = sum((ri-mu_r)*(bi-mu_b) for ri, bi in zip(r, b))/n
                beta = cov/vb if vb != 0 else None
                try:
                    import math
                    vr = statistics.pvariance(r)
                    corr = cov / math.sqrt(vr*vb) if vr > 0 and vb > 0 else None
                except Exception:
                    corr = None
                betas[t] = None if beta is None else float(beta)
                cors[t] = None if corr is None else float(corr)

            bsum = 0.0
            wsum = 0.0
            for t, w in weights.items():
                if t in betas and betas[t] is not None:
                    bsum += float(w)*float(betas[t])
                    wsum += float(w)
            portfolio_beta = (bsum/wsum) if wsum > 0 else None

            return json.dumps({
                "ok": True,
                "betas": {t: (None if v is None else round(float(v), 6)) for t, v in betas.items()},
                "correlations_vs_benchmark": {t: (None if v is None else round(float(v), 6)) for t, v in cors.items()},
                "portfolio_beta": (None if portfolio_beta is None else round(float(portfolio_beta), 6)),
                "benchmark": benchmark
            })
        except Exception as e:
            return json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"})
