"""
Adjusted prices:

- back-adjustor
- just adjusted prices

"""

from sysdata.base_data import baseData
from sysobjects.adjusted_prices import futuresAdjustedPrices

USE_CHILD_CLASS_ERROR = "You need to use a child class of futuresAdjustedPricesData"


class futuresAdjustedPricesData(baseData):
    """
    Abstract base class for reading and writing back-adjusted futures prices.

    Subclass this for a specific storage backend (e.g. CSV, MongoDB, Parquet).
    Child classes must implement the following methods:

    - ``get_list_of_instruments``
    - ``_get_adjusted_prices_without_checking``
    - ``_add_adjusted_prices_without_checking_for_existing_entry``
    - ``_delete_adjusted_prices_without_any_warning_be_careful``
    """

    def __repr__(self):
        return USE_CHILD_CLASS_ERROR

    def keys(self):
        """
        Return list of available instrument codes.

        Returns
        -------
        list
            Instrument codes with stored adjusted prices.
        """
        return self.get_list_of_instruments()

    def get_adjusted_prices(self, instrument_code: str) -> futuresAdjustedPrices:
        """
        Retrieve back-adjusted price series for an instrument.

        Parameters
        ----------
        instrument_code : str
            Instrument identifier, e.g. ``"EDOLLAR"``.

        Returns
        -------
        futuresAdjustedPrices
            Time series of adjusted prices. Returns an empty series if
            the instrument is not found.
        """
        if self.is_code_in_data(instrument_code):
            adjusted_prices = self._get_adjusted_prices_without_checking(
                instrument_code
            )
        else:
            adjusted_prices = futuresAdjustedPrices.create_empty()

        return adjusted_prices

    def __getitem__(self, instrument_code: str) -> futuresAdjustedPrices:
        """
        Dict-style access to adjusted prices.

        Parameters
        ----------
        instrument_code : str
            Instrument identifier.

        Returns
        -------
        futuresAdjustedPrices
            Time series of adjusted prices.
        """
        return self.get_adjusted_prices(instrument_code)

    def delete_adjusted_prices(self, instrument_code: str, are_you_sure: bool = False):
        """
        Delete stored adjusted prices for an instrument.

        Parameters
        ----------
        instrument_code : str
            Instrument identifier.
        are_you_sure : bool, optional
            Safety flag that must be True to proceed with deletion.
        """
        if are_you_sure:
            if self.is_code_in_data(instrument_code):
                self._delete_adjusted_prices_without_any_warning_be_careful(
                    instrument_code
                )
                self.log.info(
                    "Deleted adjusted price data for %s" % instrument_code,
                    instrument_code=instrument_code,
                )

            else:
                # doesn't exist anyway
                self.log.warning(
                    "Tried to delete non existent adjusted prices for %s"
                    % instrument_code,
                    instrument_code=instrument_code,
                )
        else:
            self.log.error(
                "You need to call delete_adjusted_prices with a flag to be sure",
                instrument_code=instrument_code,
            )

    def is_code_in_data(self, instrument_code: str) -> bool:
        """
        Check whether adjusted prices exist for the given instrument.

        Parameters
        ----------
        instrument_code : str
            Instrument identifier.

        Returns
        -------
        bool
            True if data exists for the instrument.
        """
        if instrument_code in self.get_list_of_instruments():
            return True
        else:
            return False

    def add_adjusted_prices(
        self,
        instrument_code: str,
        adjusted_price_data: futuresAdjustedPrices,
        ignore_duplication: bool = False,
    ):
        """
        Write adjusted prices for an instrument.

        Parameters
        ----------
        instrument_code : str
            Instrument identifier.
        adjusted_price_data : futuresAdjustedPrices
            Time series of adjusted prices to store.
        ignore_duplication : bool, optional
            If True, silently overwrite when data already exists.
            If False (default), logs an error but still writes.
        """
        if self.is_code_in_data(instrument_code):
            if ignore_duplication:
                pass
            else:
                self.log.error(
                    "There is already %s in the data, you have to delete it first"
                    % instrument_code,
                    instrument_code=instrument_code,
                )

        self._add_adjusted_prices_without_checking_for_existing_entry(
            instrument_code, adjusted_price_data
        )

        self.log.info(
            "Added data for instrument %s" % instrument_code,
            instrument_code=instrument_code,
        )

    def _add_adjusted_prices_without_checking_for_existing_entry(
        self, instrument_code: str, adjusted_price_data: futuresAdjustedPrices
    ):
        raise NotImplementedError(USE_CHILD_CLASS_ERROR)

    def get_list_of_instruments(self) -> list:
        """
        Return all instrument codes with available adjusted price data.

        Returns
        -------
        list
            Instrument codes.

        Raises
        ------
        NotImplementedError
            Must be implemented by child classes.
        """
        raise NotImplementedError(USE_CHILD_CLASS_ERROR)

    def _delete_adjusted_prices_without_any_warning_be_careful(
        self, instrument_code: str
    ):
        raise NotImplementedError(USE_CHILD_CLASS_ERROR)

    def _get_adjusted_prices_without_checking(
        self, instrument_code: str
    ) -> futuresAdjustedPrices:
        raise NotImplementedError(USE_CHILD_CLASS_ERROR)
