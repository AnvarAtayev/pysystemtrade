from typing import List, Union

from syslogging.adapter import DynamicAttributeLogger
from syscore.constants import named_object

import pandas as pd

from sysdata.futures.adjusted_prices import futuresAdjustedPricesData
from sysobjects.adjusted_prices import futuresAdjustedPrices
from syscore.fileutils import (
    resolve_path_and_filename_for_package,
    files_with_extension_in_pathname,
)
from syscore.pandas.pdutils import pd_readcsv
from syscore.constants import arg_not_supplied
from syslogging.logger import get_logger

ADJUSTED_PRICES_DIRECTORY = "data.futures.adjusted_prices_csv"
DATE_INDEX_NAME = "DATETIME"


class csvFuturesAdjustedPricesData(futuresAdjustedPricesData):
    """
    CSV backend for reading and writing back-adjusted futures prices.

    Each instrument is stored as a single CSV file with columns
    ``DATETIME`` and ``price``, located under ``datapath``. Defaults to
    ``data/futures/adjusted_prices_csv/``.

    Parameters
    ----------
    datapath : str, optional
        Dot-separated package path to the CSV directory.
        Defaults to ``"data.futures.adjusted_prices_csv"``.
    log : logger, optional
        Logger instance.
    """

    def __init__(
        self,
        datapath: Union[str, named_object] = arg_not_supplied,
        log: DynamicAttributeLogger = get_logger("csvFuturesContractPriceData"),
    ) -> None:
        super().__init__(log=log)

        if datapath is arg_not_supplied:
            datapath = ADJUSTED_PRICES_DIRECTORY

        self._datapath: str = datapath

    def __repr__(self) -> str:
        return "csvFuturesAdjustedPricesData accessing %s" % self._datapath

    @property
    def datapath(self) -> str:
        """
        Dot-separated package path to the CSV directory.

        Returns
        -------
        str
        """
        return self._datapath

    def get_list_of_instruments(self) -> List[str]:
        """
        Scan the CSV directory for available instruments.

        Returns
        -------
        list
            Instrument codes derived from filenames (without ``.csv``).
        """
        return files_with_extension_in_pathname(self.datapath, ".csv")

    def _get_adjusted_prices_without_checking(
        self, instrument_code: str
    ) -> futuresAdjustedPrices:
        """
        Read adjusted prices from a CSV file.

        Reads ``<instrument_code>.csv`` via ``pd_readcsv``, deduplicates
        timestamps by keeping the last value per datetime, and wraps the
        result as a ``futuresAdjustedPrices`` series.

        Parameters
        ----------
        instrument_code : str
            Instrument identifier, e.g. ``"EDOLLAR"``.

        Returns
        -------
        futuresAdjustedPrices
            Time series of adjusted prices. Returns an empty series if
            the file cannot be found.
        """
        filename = self._filename_given_instrument_code(instrument_code)

        try:
            instrpricedata = pd_readcsv(filename)
        except OSError:
            self.log.warning("Can't find adjusted price file %s" % filename)
            return futuresAdjustedPrices.create_empty()

        instrpricedata.columns = ["price"]
        instrpricedata = instrpricedata.groupby(level=0).last()
        instrpricedata = pd.Series(instrpricedata.iloc[:, 0])

        instrpricedata = futuresAdjustedPrices(instrpricedata)

        return instrpricedata

    def _delete_adjusted_prices_without_any_warning_be_careful(
        self, instrument_code: str
    ) -> None:
        raise NotImplementedError(
            "You can't delete adjusted prices stored as a csv - Add to overwrite existing or delete file manually"
        )

    def _add_adjusted_prices_without_checking_for_existing_entry(
        self, instrument_code: str, adjusted_price_data: futuresAdjustedPrices
    ) -> None:
        """
        Write adjusted prices to a CSV file.

        Converts the series to a single-column DataFrame with header
        ``price`` and writes to ``<instrument_code>.csv`` with a
        ``DATETIME`` index label.

        Parameters
        ----------
        instrument_code : str
            Instrument identifier.
        adjusted_price_data : futuresAdjustedPrices
            Time series of adjusted prices to write.
        """
        # Ensures the file will be written with a column header
        adjusted_price_data_as_dataframe = pd.DataFrame(adjusted_price_data)
        adjusted_price_data_as_dataframe.columns = ["price"]

        filename = self._filename_given_instrument_code(instrument_code)
        adjusted_price_data_as_dataframe.to_csv(filename, index_label=DATE_INDEX_NAME)

    def _filename_given_instrument_code(self, instrument_code: str) -> str:
        """
        Resolve the full filesystem path for an instrument's CSV file.

        Parameters
        ----------
        instrument_code : str
            Instrument identifier.

        Returns
        -------
        str
            Absolute path to the CSV file.
        """
        return resolve_path_and_filename_for_package(
            self.datapath, "%s.csv" % (instrument_code)
        )
