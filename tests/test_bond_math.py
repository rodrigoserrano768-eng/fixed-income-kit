import pytest

from src.bond_math import (
    Bond,
    price_from_yield,
    yield_from_price,
    macaulay_duration,
    modified_duration,
    convexity,
    dv01,
    price_change_duration_convexity_approx,
)


def test_par_bond_prices_at_par_when_yield_equals_coupon():
    # A bond whose coupon rate equals its yield always prices at par (100),
    # regardless of maturity - a standard textbook identity, good sanity check.
    bond = Bond(face=100, coupon_rate=0.04, years_to_maturity=10, freq=1)
    assert price_from_yield(bond, y=0.04) == pytest.approx(100.0, abs=1e-8)


def test_price_known_value_5y_annual_bond():
    # 5y, 5% annual coupon, face 100, priced at 6% yield.
    # Hand-computed: sum of 5/(1.06)^t for t=1..5 + 100/(1.06)^5 = 95.788...
    bond = Bond(face=100, coupon_rate=0.05, years_to_maturity=5, freq=1)
    price = price_from_yield(bond, y=0.06)
    assert price == pytest.approx(95.79, abs=0.01)


def test_yield_from_price_round_trips():
    bond = Bond(face=100, coupon_rate=0.045, years_to_maturity=7, freq=2)
    true_yield = 0.038
    price = price_from_yield(bond, true_yield)
    recovered = yield_from_price(bond, price)
    assert recovered == pytest.approx(true_yield, abs=1e-8)


def test_macaulay_duration_equals_maturity_for_zero_coupon():
    # A zero-coupon bond's Macaulay duration is exactly its maturity - all
    # weight is on the single cashflow at maturity. Model a zero as a bond
    # with coupon_rate=0.
    bond = Bond(face=100, coupon_rate=0.0, years_to_maturity=10, freq=1)
    d = macaulay_duration(bond, y=0.03)
    assert d == pytest.approx(10.0, abs=1e-8)


def test_modified_duration_less_than_macaulay_for_positive_yield():
    bond = Bond(face=100, coupon_rate=0.04, years_to_maturity=10, freq=2)
    y = 0.035
    assert modified_duration(bond, y) < macaulay_duration(bond, y)


def test_convexity_positive_for_vanilla_bond():
    bond = Bond(face=100, coupon_rate=0.04, years_to_maturity=10, freq=2)
    assert convexity(bond, y=0.035) > 0


def test_dv01_matches_duration_approx_for_small_move():
    # For a 1bp move, duration-only and full-reprice DV01 should agree closely -
    # this is the small-move regime where linear approximation is still good.
    bond = Bond(face=100, coupon_rate=0.04, years_to_maturity=10, freq=2)
    y = 0.035
    price = price_from_yield(bond, y)
    d_mod = modified_duration(bond, y)
    duration_only_dv01 = price * d_mod * 0.0001
    exact_dv01 = dv01(bond, y)
    assert exact_dv01 == pytest.approx(duration_only_dv01, rel=0.01)


def test_convexity_approx_beats_duration_only_for_large_yield_move():
    """This is the point of the project: for a large yield move, duration
    alone under/over-estimates the price change (it's a straight-line
    approximation to a curved function); adding the convexity term gets
    materially closer to the exact repriced value.
    """
    bond = Bond(face=100, coupon_rate=0.04, years_to_maturity=15, freq=2)
    y = 0.035
    dy = 0.02  # a large, 200bp move
    price = price_from_yield(bond, y)

    exact_new_price = price_from_yield(bond, y + dy)
    exact_change = exact_new_price - price

    d_mod = modified_duration(bond, y)
    duration_only_change = -price * d_mod * dy

    conv_approx_change = price_change_duration_convexity_approx(bond, y, dy)

    duration_only_error = abs(duration_only_change - exact_change)
    conv_approx_error = abs(conv_approx_change - exact_change)
    assert conv_approx_error < duration_only_error


def test_yield_from_price_raises_on_nonpositive_price():
    bond = Bond(face=100, coupon_rate=0.04, years_to_maturity=5, freq=1)
    with pytest.raises(ValueError, match="sane range"):
        yield_from_price(bond, price=0.0)


def test_yield_from_price_raises_on_price_above_undiscounted_sum():
    bond = Bond(face=100, coupon_rate=0.04, years_to_maturity=5, freq=1)
    too_high = sum(bond.cashflows()) + 1
    with pytest.raises(ValueError, match="sane range"):
        yield_from_price(bond, price=too_high)


def test_short_maturity_edge_case_single_cashflow():
    # Edge case: a bond with less than one coupon period left.
    bond = Bond(face=100, coupon_rate=0.03, years_to_maturity=0.5, freq=1)
    assert len(bond.cashflow_times()) == 1
    price = price_from_yield(bond, y=0.03)
    assert price > 0
