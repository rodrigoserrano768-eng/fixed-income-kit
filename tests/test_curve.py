from pathlib import Path

import pandas as pd
import pytest

from src.curve import interpolate_rate, continuous_to_periodic

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def curve():
    return pd.read_csv(FIXTURES / "ecb_curve_2026-10-08.csv")


def test_interpolate_rate_at_published_node_matches_exactly(curve):
    rate = interpolate_rate(curve, 10.0)
    expected = curve.loc[curve["maturity_years"] == 10.0, "rate"].iloc[0]
    assert rate == pytest.approx(expected, abs=1e-10)


def test_interpolate_rate_between_nodes_is_between_their_rates(curve):
    r5 = curve.loc[curve["maturity_years"] == 5.0, "rate"].iloc[0]
    r7 = curve.loc[curve["maturity_years"] == 7.0, "rate"].iloc[0]
    r6 = interpolate_rate(curve, 6.0)
    assert min(r5, r7) <= r6 <= max(r5, r7)


def test_interpolate_rate_extrapolates_flat_below_shortest_maturity(curve):
    shortest_rate = curve.sort_values("maturity_years")["rate"].iloc[0]
    rate = interpolate_rate(curve, 0.01)
    assert rate == pytest.approx(shortest_rate, abs=1e-10)


def test_interpolate_rate_extrapolates_flat_above_longest_maturity(curve):
    longest_rate = curve.sort_values("maturity_years")["rate"].iloc[-1]
    rate = interpolate_rate(curve, 50.0)
    assert rate == pytest.approx(longest_rate, abs=1e-10)


def test_continuous_to_periodic_annual_is_higher_than_continuous_rate():
    # Converting a continuously-compounded rate to annual-compounding must
    # increase the number (fewer compounding periods need a higher stated
    # rate to produce the same growth) - a standard identity, good sanity check.
    cc_rate = 0.03
    periodic = continuous_to_periodic(cc_rate, freq=1)
    assert periodic > cc_rate


def test_continuous_to_periodic_round_trips_growth_factor():
    import math
    cc_rate = 0.035
    freq = 2
    periodic = continuous_to_periodic(cc_rate, freq)
    growth_continuous = math.exp(cc_rate * 1.0)
    growth_periodic = (1 + periodic / freq) ** freq
    assert growth_periodic == pytest.approx(growth_continuous, abs=1e-10)
