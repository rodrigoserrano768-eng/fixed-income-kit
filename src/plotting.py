"""Visuals: (a) the yield curve with a bond's own yield marked on it,
(b) price-vs-yield curvature vs. the linear duration approximation -
this second one is the point of the project: it's what "convexity" means,
drawn instead of just computed.
"""
from __future__ import annotations

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.bond_math import Bond, price_from_yield, modified_duration


def plot_curve_with_bond(
    curve: pd.DataFrame, bond_maturity_years: float, bond_yield: float, bond_name: str, ax: plt.Axes | None = None
) -> plt.Axes:
    if ax is None:
        _, ax = plt.subplots(figsize=(9, 6))
    curve_sorted = curve.sort_values("maturity_years")
    ax.plot(curve_sorted["maturity_years"], curve_sorted["rate"] * 100, marker="o", label="ECB AAA euro area spot curve")
    ax.scatter(
        [bond_maturity_years], [bond_yield * 100], color="crimson", zorder=5, s=90,
        label=f"{bond_name}\n(market yield)",
    )
    ax.set_xlabel("Maturity (years)")
    ax.set_ylabel("Rate (%)")
    ax.set_title("Euro area AAA spot curve, with bond marked")
    ax.legend()
    ax.grid(alpha=0.3)
    return ax


def plot_price_yield_convexity(
    bond: Bond, center_yield: float, yield_range: float = 0.03, n_points: int = 200, ax: plt.Axes | None = None
) -> plt.Axes:
    """The convexity picture: exact price-vs-yield curve (curved) vs. the
    straight-line tangent a duration-only hedge assumes. The gap between
    them, especially for large yield moves, IS convexity.
    """
    if ax is None:
        _, ax = plt.subplots(figsize=(9, 6))

    yields = np.linspace(center_yield - yield_range, center_yield + yield_range, n_points)
    exact_prices = np.array([price_from_yield(bond, y) for y in yields])

    center_price = price_from_yield(bond, center_yield)
    d_mod = modified_duration(bond, center_yield)
    # Linear (duration-only) tangent line: price ≈ P0 * (1 - D_mod * dy)
    linear_prices = center_price * (1 - d_mod * (yields - center_yield))

    ax.plot(yields * 100, exact_prices, label="Exact price (full repricing)", linewidth=2)
    ax.plot(yields * 100, linear_prices, label="Linear approximation (duration only)", linestyle="--")
    ax.scatter([center_yield * 100], [center_price], color="black", zorder=5, label="Current yield/price")
    ax.set_xlabel("Yield (%)")
    ax.set_ylabel("Price")
    ax.set_title("Price vs. yield: exact curve vs. duration-only linear approximation")
    ax.legend()
    ax.grid(alpha=0.3)
    return ax
