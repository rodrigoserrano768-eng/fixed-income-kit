"""Acceptance test: price_from_yield against 3 real sovereign bonds, their
quoted market yield, and their quoted market price, captured from a public
source (see tests/fixtures/control_bonds.py for the exact source and date).

Tolerance: 2.0 price points (~2% on these ~90-98 priced bonds). This is wide
on purpose - see README "known limitations" for why: the model assumes the
next cashflow lands exactly 1/freq years from the valuation date, not on the
bond's actual coupon date, which drifts the result by roughly a point on a
~7-year bond. That's a day-count simplification, declared, not an attempt
to hide a bug behind a loose tolerance.
"""
import pytest

from src.bond_math import Bond, price_from_yield
from tests.fixtures.control_bonds import CONTROL_BONDS, years_to_maturity

PRICE_TOLERANCE = 2.0


@pytest.mark.parametrize("spec", CONTROL_BONDS, ids=[b["name"] for b in CONTROL_BONDS])
def test_price_from_market_yield_matches_market_price(spec):
    bond = Bond(
        face=spec["face"],
        coupon_rate=spec["coupon_rate"],
        years_to_maturity=years_to_maturity(spec),
        freq=spec["freq"],
    )
    calc_price = price_from_yield(bond, spec["market_yield"])
    diff = abs(calc_price - spec["market_price"])
    assert diff < PRICE_TOLERANCE, (
        f"{spec['name']}: calculated={calc_price:.3f} market={spec['market_price']} "
        f"diff={diff:.3f} exceeds {PRICE_TOLERANCE} tolerance (source: {spec['source']})"
    )
