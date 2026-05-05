from copy import copy
from typing import List, Tuple, Type, TypeVar

import numpy as np
import pandas as pd

from syscore.pandas.full_merge_with_replacement import full_merge_of_existing_series
from sysobjects.dict_of_named_futures_per_contract_prices import (
    contract_name_from_column_name,
    futuresNamedContractFinalPricesWithContractID,
    price_name,
)
from sysobjects.multiple_prices import futuresMultiplePrices

FuturesAdjustedPrices = TypeVar("FuturesAdjustedPrices", bound="futuresAdjustedPrices")


class futuresAdjustedPrices(pd.Series):
    """Adjusted futures prices stored as a pandas series."""

    def __init__(self, price_data: pd.Series) -> None:
        """
        Create adjusted prices from a pandas series.

        Parameters
        ----------
        price_data : pd.Series
            Adjusted price series indexed by timestamp.
        """
        price_data.index.name = "index"  # arctic compatible
        super().__init__(price_data)

    @classmethod
    def create_empty(cls: Type[FuturesAdjustedPrices]) -> FuturesAdjustedPrices:
        """
        Return an empty adjusted-price series.

        Returns
        -------
        futuresAdjustedPrices
            Empty series with ``float64`` dtype.
        """

        futures_contract_prices = cls(pd.Series(dtype="float64"))

        return futures_contract_prices

    @classmethod
    def stitch_multiple_prices(
        cls: Type[FuturesAdjustedPrices],
        multiple_prices: futuresMultiplePrices,
        forward_fill: bool = False,
    ) -> FuturesAdjustedPrices:
        """
        Stitch multiple-price data into a continuous adjusted series.

        Parameters
        ----------
        multiple_prices : futuresMultiplePrices
            Multiple-price data to stitch.
        forward_fill : bool, default False
            If ``True``, forward-fill prices and forward values before stitching.

        Returns
        -------
        futuresAdjustedPrices
            Continuous adjusted price series produced with Panama stitching.

        """
        adjusted_prices = _panama_stitch(multiple_prices, forward_fill)
        return cls(adjusted_prices)

    def update_with_multiple_prices_no_roll(
        self, updated_multiple_prices: futuresMultiplePrices
    ) -> "futuresAdjustedPrices":
        """
        Update adjusted prices when the front contract has not rolled.

        Parameters
        ----------
        updated_multiple_prices : futuresMultiplePrices
            Latest multiple-price data to merge into the adjusted series.

        Returns
        -------
        futuresAdjustedPrices
            Updated adjusted prices. Returns an empty adjusted-price series if a
            roll is detected.
        """

        updated_adj = _update_adjusted_prices_from_multiple_no_roll(
            self, updated_multiple_prices
        )

        return updated_adj


# TODO: Add multiple adjustment methods
# TODO: Speed up current adjustment logic
def _panama_stitch(
    multiple_prices_input: futuresMultiplePrices, forward_fill: bool = False
) -> pd.Series:
    """
    Stitch adjusted prices with the Panama method.

    Parameters
    ----------
    multiple_prices_input : futuresMultiplePrices
        Multiple-price data ordered by timestamp.
    forward_fill : bool, default False
        If ``True``, forward-fill prices and forward values before stitching.

    Returns
    -------
    pd.Series
        Adjusted prices indexed like ``multiple_prices_input``.
    """
    multiple_prices = copy(multiple_prices_input)
    if forward_fill:
        multiple_prices.ffill(inplace=True)

    if multiple_prices.empty:
        raise Exception("Can't stitch an empty multiple prices object")

    previous_row = multiple_prices.iloc[0, :]
    adjusted_prices_values = [previous_row.PRICE]

    for dateindex in multiple_prices.index[1:]:
        current_row = multiple_prices.loc[dateindex, :]

        if current_row.PRICE_CONTRACT == previous_row.PRICE_CONTRACT:
            # no roll has occurred
            # we just append the price
            adjusted_prices_values.append(current_row.PRICE)
        else:
            # A roll has occurred
            adjusted_prices_values = _roll_in_panama(
                adjusted_prices_values, previous_row, current_row
            )

        previous_row = current_row

    # it's ok to return a DataFrame since the calling object will change the
    # type
    adjusted_prices = pd.Series(adjusted_prices_values, index=multiple_prices.index)

    return adjusted_prices


def _roll_in_panama(
    adjusted_prices_values: List[float],
    previous_row: pd.Series,
    current_row: pd.Series,
) -> List[float]:
    """
    Apply a Panama roll adjustment and append the new contract price.

    Parameters
    ----------
    adjusted_prices_values : list[float]
        Adjusted prices accumulated so far.
    previous_row : pd.Series
        Final row before the roll.
    current_row : pd.Series
        First row after the roll.

    Returns
    -------
    list[float]
        Updated adjusted prices including the roll adjustment.
    """
    # This is the sort of code you will need to change to adjust the roll logic
    # The roll differential is from the previous_row
    roll_differential = previous_row.FORWARD - previous_row.PRICE
    if np.isnan(roll_differential):
        raise Exception(
            "On this day %s which should be a roll date we don't have prices for both %s and %s contracts"
            % (
                str(current_row.name),
                previous_row.PRICE_CONTRACT,
                previous_row.FORWARD_CONTRACT,
            )
        )

    # We add the roll differential to all previous prices
    adjusted_prices_values = [
        adj_price + roll_differential for adj_price in adjusted_prices_values
    ]

    # note this includes the price for the previous row, which will now be equal to the forward price
    # We now add todays price. This will be for the new contract

    adjusted_prices_values.append(current_row.PRICE)

    return adjusted_prices_values


no_update_roll_has_occurred: futuresAdjustedPrices = (
    futuresAdjustedPrices.create_empty()
)


def _update_adjusted_prices_from_multiple_no_roll(
    existing_adjusted_prices: futuresAdjustedPrices,
    updated_multiple_prices: futuresMultiplePrices,
) -> futuresAdjustedPrices:
    """
    Update adjusted prices using new multiple-price data without a roll.

    Parameters
    ----------
    existing_adjusted_prices : futuresAdjustedPrices
        Existing adjusted-price history.
    updated_multiple_prices : futuresMultiplePrices
        Latest multiple-price data to merge.

    Returns
    -------
    futuresAdjustedPrices
        Updated adjusted prices. Returns an empty adjusted-price series if the
        input implies a roll.
    """
    new_multiple_price_data, last_contract_in_price_data = _calc_new_multiple_prices(
        existing_adjusted_prices, updated_multiple_prices
    )

    no_roll_has_occurred = new_multiple_price_data.check_all_contracts_equal_to(
        last_contract_in_price_data
    )

    if not no_roll_has_occurred:
        return no_update_roll_has_occurred

    new_adjusted_prices = new_multiple_price_data[price_name]
    new_adjusted_prices = new_adjusted_prices.dropna()

    merged_adjusted_prices = full_merge_of_existing_series(
        existing_adjusted_prices, new_adjusted_prices
    )
    merged_adjusted_prices = futuresAdjustedPrices(merged_adjusted_prices)

    return merged_adjusted_prices


def _calc_new_multiple_prices(
    existing_adjusted_prices: futuresAdjustedPrices,
    updated_multiple_prices: futuresMultiplePrices,
) -> Tuple[futuresNamedContractFinalPricesWithContractID, str]:
    """
    Extract new price rows and the latest known price contract.

    Parameters
    ----------
    existing_adjusted_prices : futuresAdjustedPrices
        Existing adjusted-price history.
    updated_multiple_prices : futuresMultiplePrices
        Latest multiple-price data.

    Returns
    -------
    tuple[futuresNamedContractFinalPricesWithContractID, str]
        Price rows after the last adjusted timestamp and the contract ID in use
        at that timestamp.
    """
    last_date_in_current_adj = existing_adjusted_prices.index[-1]
    multiple_prices_as_dict = updated_multiple_prices.as_dict()

    prices_in_multiple_prices = multiple_prices_as_dict[price_name]
    price_contract_column = contract_name_from_column_name(price_name)

    last_contract_in_price_data = prices_in_multiple_prices[price_contract_column][
        :last_date_in_current_adj
    ].iloc[-1]

    new_multiple_price_data = prices_in_multiple_prices.prices_after_date(
        last_date_in_current_adj
    )

    return new_multiple_price_data, last_contract_in_price_data
