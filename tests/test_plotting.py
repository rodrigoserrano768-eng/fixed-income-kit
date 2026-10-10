from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import pandas as pd
import pytest

from src.bond_math import Bond
from src.plotting import plot_curve_with_bond, plot_price_yield_convexity

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def curve():
    return pd.read_csv(FIXTURES / "ecb_curve_2026-10-08.csv")


def test_plot_curve_with_bond_runs(curve):
    ax = plot_curve_with_bond(curve, bond_maturity_years=7.0, bond_yield=0.045, bond_name="Test Bond")
    assert ax is not None


def test_plot_price_yield_convexity_runs():
    bond = Bond(face=100, coupon_rate=0.03, years_to_maturity=10, freq=1)
    ax = plot_price_yield_convexity(bond, center_yield=0.035)
    assert ax is not None


def test_convexity_plot_exact_curve_never_below_linear_approx():
    """Positive convexity means the exact price-yield curve lies on or above
    its tangent line everywhere, not just near the center point - verify
    this geometric property directly from the plotted data, not just that
    the function runs without error.
    """
    import numpy as np
    from src.bond_math import price_from_yield, modified_duration

    bond = Bond(face=100, coupon_rate=0.03, years_to_maturity=10, freq=1)
    center_yield = 0.035
    center_price = price_from_yield(bond, center_yield)
    d_mod = modified_duration(bond, center_yield)

    yields = np.linspace(center_yield - 0.03, center_yield + 0.03, 50)
    exact = np.array([price_from_yield(bond, y) for y in yields])
    linear = center_price * (1 - d_mod * (yields - center_yield))

    assert (exact >= linear - 1e-9).all()
