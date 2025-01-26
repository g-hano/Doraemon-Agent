from pydantic import BaseModel, Field
from langchain_core.tools import BaseTool

class YahooFinanceFetcherSchema(BaseModel):
    ticker_symbol: str = Field(description='str value for ticker_symbol')

from langchain_core.tools import BaseTool
from typing import Type

class YahooFinanceFetcherTool(BaseTool):
    name: str = "YahooFinanceFetcher"
    description: str = '''Fetches the latest price information for a given stock or cryptocurrency on Yahoo Finance.'''
    args_schema: Type[BaseModel] = YahooFinanceFetcherSchema
    verbose: bool = True

    def _run(self, ticker_symbol: str) -> any:
        import yfinance as yf; ticker_data = yf.Ticker(ticker_symbol); return ticker_data.info['price']
