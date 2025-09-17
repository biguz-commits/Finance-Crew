from crewai.tools import BaseTool
from typing import Type, List
from pydantic import BaseModel, Field
import pandas as pd
import yfinance as yf
import json

class FetchPricesInput(BaseModel):
    """Input schema for fetching historical prices via yfinance."""
    tickers_json: str = Field(..., description="JSON array of tickers, e.g. '[\"AAPL\",\"MSFT\"]'.")
    period: str = Field("1y", description="yfinance period, e.g. '6mo', '1y', '2y'.")
    interval: str = Field("1d", description="yfinance interval, e.g. '1d', '1wk', '1mo'.")

class FetchYFinancePricesTool(BaseTool):
    name: str = "fetch_yfinance_prices"
    description: str = (
        "Download historical adjusted close prices with yfinance for the given tickers/period/interval. "
        "Returns JSON with 'index' (ISO dates) and 'data' (dict[ticker]->list of prices)."
    )
    args_schema: Type[BaseModel] = FetchPricesInput

    def _run(self, tickers_json: str, period: str = "1y", interval: str = "1d") -> str:
        try:
            tickers = json.loads(tickers_json)
            if not isinstance(tickers, list) or not all(isinstance(t, str) for t in tickers):
                return json.dumps({"ok": False, "error": "tickers_json must be a JSON array of strings."})

            data = yf.download(
                tickers, period=period, interval=interval,
                auto_adjust=True, progress=False, group_by="ticker"
            )
            if "Close" in data:
                prices = data["Close"].copy()
            else:
                prices = data["Adj Close"].to_frame(name=tickers[0]) if "Adj Close" in data\
                    else data["Close"].to_frame(name=tickers[0])

            if isinstance(prices.columns, pd.MultiIndex):
                prices.columns = [c[0] for c in prices.columns]

            prices = prices.dropna(how="all")
            prices = prices.sort_index()

            payload = {
                "ok": True,
                "index": [i.strftime("%Y-%m-%d") for i in prices.index],
                "data": {col: [None if pd.isna(v) else float(v) for v in prices[col].tolist()] for col in prices.columns}
            }
            return json.dumps(payload)
        except Exception as e:
            return json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"})
