"""
Example showing how to fetch Yahoo Finance prices for 10 large-cap equities.

The script uses the project's ``yahooStockPrices`` wrapper so the output is a
single wide ``pandas.DataFrame`` of daily prices indexed by date.
"""

from typing import Dict, List

import pandas as pd

from sysdata.yahoo.stock_prices import yahooStockPrices

TOP_EQUITY_SYMBOLS = [
    "AAPL",
    "MSFT",
    "NVDA",
    "AMZN",
    "GOOGL",
    "META",
    "BRK-B",
    "AVGO",
    "LLY",
    "TSLA",
]
START_DATE = "2015-01-01"


def fetch_price_frame(
    symbols: List[str], start_date: str, adjusted: bool = True
) -> pd.DataFrame:
    """
    Download daily prices for multiple Yahoo Finance stock symbols.

    Parameters
    ----------
    symbols : List[str]
        Yahoo Finance ticker symbols to fetch.
    start_date : str
        Inclusive start date passed to Yahoo Finance.
    adjusted : bool, default=True
        If ``True``, prefer adjusted close prices where available.

    Returns
    -------
    pandas.DataFrame
        Daily price frame indexed by date with one column per symbol.
    """
    downloader = yahooStockPrices()
    prices_by_symbol: Dict[str, pd.Series] = {}

    for symbol in symbols:
        prices_by_symbol[symbol] = downloader.get_daily_prices(
            symbol=symbol,
            start_date=start_date,
            adjusted=adjusted,
        )

    return pd.DataFrame(prices_by_symbol).sort_index()


def main() -> None:
    """
    Fetch and display daily prices for 10 representative mega-cap equities.
    """
    price_frame = fetch_price_frame(
        symbols=TOP_EQUITY_SYMBOLS,
        start_date=START_DATE,
        adjusted=True,
    )

    returns = price_frame.pct_change().dropna()