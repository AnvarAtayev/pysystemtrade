import sys
from types import SimpleNamespace

import pandas as pd
import pytest

from sysdata.yahoo.stock_prices import yahooStockPrices


class _AdjustedTicker:
    def __init__(self, symbol: str):
        self.symbol = symbol

    def history(
        self,
        start: str,
        end=None,
        interval: str = "1d",
        auto_adjust: bool = False,
        actions: bool = False,
    ) -> pd.DataFrame:
        return pd.DataFrame(
            {
                "Close": [101.0, 102.0],
                "Adj Close": [100.5, 101.5],
            },
            index=pd.DatetimeIndex(
                ["2024-01-02 00:00:00", "2024-01-03 00:00:00"], tz="US/Eastern"
            ),
        )


class _CloseOnlyTicker:
    def __init__(self, symbol: str):
        self.symbol = symbol

    def history(
        self,
        start: str,
        end=None,
        interval: str = "1d",
        auto_adjust: bool = False,
        actions: bool = False,
    ) -> pd.DataFrame:
        return pd.DataFrame(
            {"Close": [200.0, 201.0]},
            index=pd.DatetimeIndex(["2024-01-04", "2024-01-05"]),
        )


def test_get_daily_prices_prefers_adjusted_prices(monkeypatch):
    monkeypatch.setitem(
        sys.modules, "yfinance", SimpleNamespace(Ticker=_AdjustedTicker)
    )

    prices = yahooStockPrices().get_daily_prices(
        symbol="AAPL", start_date="2024-01-01"
    )

    assert prices.name == "AAPL"
    assert prices.index.tz is None
    assert prices.to_list() == [100.5, 101.5]


def test_get_daily_prices_falls_back_to_close(monkeypatch):
    monkeypatch.setitem(
        sys.modules, "yfinance", SimpleNamespace(Ticker=_CloseOnlyTicker)
    )

    prices = yahooStockPrices().get_daily_prices(
        symbol="MSFT", start_date="2024-01-01", adjusted=True
    )

    assert prices.name == "MSFT"
    assert prices.to_list() == [200.0, 201.0]


def test_get_daily_prices_raises_for_missing_yfinance(monkeypatch):
    monkeypatch.delitem(sys.modules, "yfinance", raising=False)

    with pytest.raises(ImportError):
        yahooStockPrices().get_daily_prices(symbol="AAPL", start_date="2024-01-01")
