"""
We implement here a simple MVO optimiser as described in the MOSEK Portfolio Optimisation Cookbook.
"""

from typing import Optional

import cvxpy as cp
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from examples.data.stocks import fetch_price_frame

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


def get_expected_returns(returns: pd.DataFrame) -> np.ndarray:
    """
    Get expected returns as the mean of the historical returns.

    Parameters
    ----------
    returns : pandas.DataFrame
        Historical returns for each asset.

    Returns
    -------
    numpy.ndarray
        Expected returns for each asset.
    """
    return returns.mean().values


def get_covariance_matrix(returns: pd.DataFrame) -> np.ndarray:
    """
    Get the covariance matrix of the returns.

    Parameters
    ----------
    returns : pandas.DataFrame
        Historical returns for each asset.

    Returns
    -------
    numpy.ndarray
        Covariance matrix of the returns.
    """
    return returns.cov().values


def get_returns_frame(
    symbols: list[str], start_date: str, end_date: Optional[str] = None
) -> pd.DataFrame:
    """
    Fetch and return a DataFrame of returns for the specified symbols and date range.

    Parameters
    ----------
    symbols : list[str]
        List of asset symbols to fetch returns for.
    start_date : str
        Start date for fetching returns (inclusive).
    end_date : Optional[str], default=None
        End date for fetching returns (exclusive). If None, fetches up to the latest available data.

    Returns
    -------
    pandas.DataFrame
        DataFrame of returns for the specified symbols and date range.
    """
    price_frame = fetch_price_frame(
        symbols=symbols,
        start_date=start_date,
        adjusted=True,
    )

    returns = price_frame.pct_change().dropna()
    return returns


def get_optimal_weights_1(returns: pd.DataFrame, gamma: float) -> np.ndarray:
    """
    Get optimal weights for the MVO problem.

    Parameters
    ----------
    returns : pandas.DataFrame
        Historical returns for each asset.
    gamma : float
        Upper limit for the standard deviation of the portfolio.

    Returns
    -------
    numpy.ndarray
        Optimal weights for each asset.
    """
    N = returns.shape[1]

    # expected returns
    m = get_expected_returns(returns)

    # covariance matrix
    S = get_covariance_matrix(returns)

    # optimisation problem
    x = cp.Variable(N)
    objective = cp.Maximize(m @ x)
    constraints = [cp.quad_form(x, S) <= gamma**2, cp.sum(x) == 1, x >= 0]

    problem = cp.Problem(objective, constraints)
    problem.solve()

    return x.value


def get_optimal_weights_2(returns: pd.DataFrame, gamma: float) -> np.ndarray:
    """
    Get optimal weights for the MVO problem using a different formulation.

    Parameters
    ----------
    returns : pandas.DataFrame
        Historical returns for each asset.
    gamma : float
        Upper limit for the standard deviation of the portfolio.

    Returns
    -------
    numpy.ndarray
        Optimal weights for each asset.
    """
    N = returns.shape[1]

    # expected returns
    m = get_expected_returns(returns)

    # covariance matrix
    S = get_covariance_matrix(returns)
    G = np.linalg.cholesky(S)

    # optimisation problem
    x = cp.Variable(N)
    objective = cp.Maximize(m @ x)
    constraints = [cp.sum(x) == 1, cp.norm(G @ x, 2) <= gamma, x >= 0]

    problem = cp.Problem(objective, constraints)
    problem.solve()

    return x.value


def efficient_frontier(
    returns: pd.DataFrame,
) -> list[np.ndarray]:
    """
    Compute the efficient frontier for a range of gamma values.

    Parameters
    ----------
    returns : pandas.DataFrame
        Historical returns for each asset.

    Returns
    -------
    list[numpy.ndarray]
        List of optimal weights corresponding to each gamma value.
    """
    N = returns.shape[1]

    # expected returns
    m = get_expected_returns(returns)

    # covariance matrix
    S = get_covariance_matrix(returns)
    G = np.linalg.cholesky(S)

    delta_grid = np.logspace(-1, stop=1.5, num=10)

    risks = []
    rets = []
    weights = []

    for delta in delta_grid:
        x = cp.Variable(N)
        s = cp.Variable(nonneg=True)

        objective = cp.Maximize(m @ x - delta * s)
        constraints = [cp.sum(x) == 1, x >= 0, cp.norm(G @ x, 2) <= s]

        problem = cp.Problem(objective, constraints)
        problem.solve()

        x_opt = x.value
        ret = m @ x_opt
        risk = np.sqrt((G @ x_opt).T @ (G @ x_opt))
        risks.append(risk)
        rets.append(ret)
        weights.append(x_opt)

    frontier = pd.DataFrame(weights, columns=returns.columns)
    frontier["risk"] = risks
    frontier["ret"] = rets
    frontier = frontier.sort_values("risk").reset_index(drop=True)
    # Order layers by their weight in the minimum-risk portfolio
    sorted_cols = frontier.loc[0, returns.columns].sort_values(ascending=False).index
    risk_plot = frontier["risk"].to_numpy()
    ret_plot = frontier["ret"].to_numpy()
    weights_plot = frontier.loc[:, sorted_cols]

    # plot efficinet frontier
    fig_frontier, ax = plt.subplots()
    ax.plot(risks, rets, marker="o")
    ax.set_xlabel("Risk (Standard Deviation)")
    ax.set_ylabel("Expected Return")
    ax.set_title("Efficient Frontier")
    ax.grid(linestyle=":")

    # plot weights, sorted by weight size
    greys = plt.cm.Greys(np.linspace(0.9, 0.3, len(sorted_cols)))
    fig_weights, ax = plt.subplots(figsize=(10, 7))
    ax.stackplot(
        risk_plot,
        *[weights_plot[col].to_numpy() for col in weights_plot.columns],
        labels=weights_plot.columns,
        colors=greys,
        linewidth=0,
        alpha=0.8,
    )
    ax.set_xlabel("portfolio risk (std. dev.)")
    ax.set_ylabel("x")
    ax.set_ylim(0.0, 1.0)
    ax.grid(linestyle=":")
    ax.legend(loc="lower right", framealpha=0.9)

    return fig_frontier, fig_weights


if __name__ == "__main__":
    returns = get_returns_frame(
        symbols=TOP_EQUITY_SYMBOLS,
        start_date=START_DATE,
    )

    fig = efficient_frontier(returns)
