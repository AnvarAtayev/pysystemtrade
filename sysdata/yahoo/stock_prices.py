import datetime
from typing import Any, Union

import pandas as pd
import yfinance as yf

from syscore.constants import arg_not_supplied

DateLike = Union[str, datetime.date, datetime.datetime, pd.Timestamp]


class yahooStockPrices:
    """
    Yahoo Finance stock price downloader.

    Notes
    -----
    This is a thin wrapper around ``yfinance`` intended for research and
    prototyping. It normalises the returned daily history into a single
    ``pandas.Series`` so downstream code does not need to know about Yahoo's
    column conventions.
    """

    def get_daily_prices(
        self,
        symbol: str,
        start_date: DateLike,
        end_date: Any = arg_not_supplied,
        adjusted: bool = True,
    ) -> pd.Series:
        """
        Fetch daily stock prices for a single Yahoo Finance symbol.

        Parameters
        ----------
        symbol : str
            Yahoo Finance ticker symbol, for example ``"AAPL"``.
        start_date : str or datetime.date or datetime.datetime or pandas.Timestamp
            Inclusive start date for the download.
        end_date : object, default=arg_not_supplied
            Exclusive end date for the download. If not supplied, Yahoo Finance
            returns data up to the latest available trading session.
        adjusted : bool, default=True
            If ``True``, prefer the adjusted close series when Yahoo Finance
            supplies it. If adjusted close is unavailable, the method falls back
            to the close series.

        Returns
        -------
        pandas.Series
            Daily price series indexed by timestamp, sorted in ascending order
            and named after ``symbol``.

        Raises
        ------
        ImportError
            Raised if ``yfinance`` is not installed.
        ValueError
            Raised if Yahoo Finance returns no rows or if no usable price column
            is present in the response.
        """
        ticker = yf.Ticker(symbol)
        history = ticker.history(
            start=self._coerce_date_to_string(start_date),
            end=(
                None
                if end_date is arg_not_supplied
                else self._coerce_date_to_string(end_date)
            ),
            interval="1d",
            auto_adjust=False,
            actions=False,
        )

        return self._normalise_downloaded_prices(
            symbol=symbol, history=history, adjusted=adjusted
        )

    def _normalise_downloaded_prices(
        self, symbol: str, history: pd.DataFrame, adjusted: bool
    ) -> pd.Series:
        if history.empty:
            raise ValueError("No Yahoo Finance price data returned for %s" % symbol)

        history = history.sort_index()
        history.index = self._normalise_datetime_index(history.index)
        price_column = self._get_price_column(history=history, adjusted=adjusted)

        prices = pd.Series(history[price_column]).dropna()
        prices.name = symbol

        if len(prices) == 0:
            raise ValueError(
                "Yahoo Finance returned only missing prices for %s" % symbol
            )

        return prices

    def _get_price_column(self, history: pd.DataFrame, adjusted: bool) -> str:
        if adjusted and "Adj Close" in history.columns:
            return "Adj Close"

        if "Close" in history.columns:
            return "Close"

        if "Adj Close" in history.columns:
            return "Adj Close"

        raise ValueError(
            "Yahoo Finance data did not include Close or Adj Close columns"
        )

    def _coerce_date_to_string(self, date_like: DateLike) -> str:
        return pd.Timestamp(date_like).strftime("%Y-%m-%d")

    def _normalise_datetime_index(self, index_like) -> pd.DatetimeIndex:
        datetime_index = pd.DatetimeIndex(index_like)
        if datetime_index.tz is not None:
            datetime_index = datetime_index.tz_localize(None)

        return datetime_index
