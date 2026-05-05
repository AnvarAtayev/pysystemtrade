"""
Example showing Panama adjustment using the shipped GOLD futures data.
"""

import pandas as pd

from syscore.fileutils import resolve_path_and_filename_for_package
from syscore.pandas.pdutils import pd_readcsv
from sysobjects.adjusted_prices import futuresAdjustedPrices
from sysobjects.multiple_prices import futuresMultiplePrices

INSTRUMENT_CODE = "GOLD"


def load_multiple_prices(instrument_code: str) -> futuresMultiplePrices:
    """
    Load multiple prices for an instrument from the example dataset.

    Parameters
    ----------
    instrument_code : str
        Instrument to load, for example ``"GOLD"``.

    Returns
    -------
    futuresMultiplePrices
        Multiple-price series for ``instrument_code``.
    """
    filename = resolve_path_and_filename_for_package(
        "data.futures.multiple_prices_csv", f"{instrument_code}.csv"
    )
    multiple_prices_data = pd_readcsv(filename, date_index_name="DATETIME")

    return futuresMultiplePrices(multiple_prices_data)


def load_adjusted_prices(instrument_code: str) -> futuresAdjustedPrices:
    """
    Load stored adjusted prices for an instrument from the example dataset.

    Parameters
    ----------
    instrument_code : str
        Instrument to load, for example ``"GOLD"``.

    Returns
    -------
    futuresAdjustedPrices
        Stored adjusted-price series for ``instrument_code``.
    """
    filename = resolve_path_and_filename_for_package(
        "data.futures.adjusted_prices_csv", f"{instrument_code}.csv"
    )
    adjusted_prices_data = pd_readcsv(filename, date_index_name="DATETIME")
    adjusted_prices_data.columns = ["price"]
    adjusted_prices_data = adjusted_prices_data.groupby(level=0).last()
    adjusted_prices = pd.Series(adjusted_prices_data.iloc[:, 0])

    return futuresAdjustedPrices(adjusted_prices)


def main() -> None:
    """
    Show how stored GOLD adjusted prices are created from multiple prices.

    The script loads the shipped ``GOLD`` CSV files, recomputes the adjusted
    series from the multiple prices, then prints a small window around the
    latest roll so the Panama adjustment is visible in real data.
    """
    multiple_prices = load_multiple_prices(INSTRUMENT_CODE)
    stored_adjusted_prices = load_adjusted_prices(INSTRUMENT_CODE)
    recomputed_adjusted_prices = futuresAdjustedPrices.stitch_multiple_prices(
        multiple_prices
    )

    multiple_prices[['CARRY', 'PRICE', 'FORWARD']].loc['2023':].plot()
    recomputed_adjusted_prices.rename('ADJ').loc['2023':].plot()
