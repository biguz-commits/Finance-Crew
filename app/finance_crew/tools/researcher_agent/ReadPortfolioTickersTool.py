from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field
import pandas as pd
import json
import os

class ReadPortfolioInput(BaseModel):
    """Input schema for reading a portfolio CSV."""
    ticker_column: str = Field("ticker", description="Name of the column that contains tickers.")

class ReadPortfolioTickersTool(BaseTool):
    name: str = "read_portfolio_tickers"
    description: str = (
        "Read a portfolio CSV and extract the unique tickers. "
        "The CSV must contain at least a 'ticker' column (configurable via ticker_column). "
        "Returns a JSON string: { 'tickers': [..], 'row_count': N }."
    )
    args_schema: Type[BaseModel] = ReadPortfolioInput

    def _run(self, dataset_path: str = "/Users/tommasobiganzoli/Desktop/finance_crew/app/data/portfolio.csv",
             ticker_column: str = "ticker") -> str:
        try:
            if not os.path.exists(dataset_path):
                return json.dumps({"ok": False, "error": f"File not found: {dataset_path}"})
            df = pd.read_csv(dataset_path)
            if ticker_column not in df.columns:
                return json.dumps({"ok": False, "error": f"Missing column '{ticker_column}' in CSV."})
            tickers = sorted([str(t).strip() for t in df[ticker_column].dropna().unique()])
            return json.dumps({"ok": True, "tickers": tickers, "row_count": int(len(df))})
        except Exception as e:
            return json.dumps({"ok": False, "error": f"{type(e).__name__}: {e}"})
