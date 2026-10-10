"""Fixed-rate bond pricing, yield, duration, convexity, DV01.

Conventions, stated once here rather than scattered as magic numbers:
- Annual coupon frequency by default (freq=1); freq=2 for semiannual.
- Actual/Actual-ish simplification: cashflows are assumed to land exactly
  on 1/freq-year boundaries from the valuation date. A real bond has an
  odd first coupon period and a day-count convention (ACT/ACT, 30/360...).
  This project does not model that - see README "known limitations".
- Yield (y) is the bond's own yield-to-maturity, periodically compounded
  at `freq`, not a continuously compounded rate.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from scipy.optimize import brentq


@dataclass
class Bond:
    face: float          # face/par value, e.g. 100
    coupon_rate: float    # annual coupon rate, e.g. 0.035 for 3.5%
    years_to_maturity: float
    freq: int = 1         # coupon payments per year

    def cashflow_times(self) -> list[float]:
        # ceil, not round: a bond with 0.5 years left and annual coupons has
        # one coupon date still ahead, not zero. round(0.5) hits Python's
        # banker's rounding and silently returns 0 - caught by a test with
        # years_to_maturity=0.5, freq=1 exercising exactly this edge.
        n = math.ceil(round(self.years_to_maturity * self.freq, 6))
        if n <= 0:
            raise ValueError(f"years_to_maturity={self.years_to_maturity} too small for freq={self.freq}")
        return [i / self.freq for i in range(1, n + 1)]

    def cashflows(self) -> list[float]:
        coupon = self.face * self.coupon_rate / self.freq
        times = self.cashflow_times()
        cfs = [coupon] * len(times)
        cfs[-1] += self.face
        return cfs


def price_from_yield(bond: Bond, y: float) -> float:
    """Clean price given a periodic yield y (compounded `bond.freq` times/year)."""
    times = bond.cashflow_times()
    cfs = bond.cashflows()
    return sum(cf / (1 + y / bond.freq) ** (t * bond.freq) for cf, t in zip(cfs, times))


def yield_from_price(bond: Bond, price: float, lo: float = -0.5, hi: float = 2.0) -> float:
    """Invert price_from_yield for y via Brent's method.

    Raises ValueError if no yield in [lo, hi] reprices to `price` - this
    would mean the quoted price itself is outside what any sane yield
    produces (e.g. negative price, or price far above the sum of undiscounted
    cashflows).
    """
    undiscounted_sum = sum(bond.cashflows())
    if price <= 0 or price > undiscounted_sum:
        raise ValueError(
            f"price={price} is outside a sane range (0, {undiscounted_sum}] "
            f"(undiscounted sum of cashflows) - can't be a valid bond price"
        )

    def objective(y: float) -> float:
        return price_from_yield(bond, y) - price

    try:
        return brentq(objective, lo, hi, xtol=1e-10, maxiter=200)
    except ValueError as e:
        raise ValueError(f"yield_from_price failed to bracket a root in [{lo}, {hi}]: {e}") from e


def macaulay_duration(bond: Bond, y: float) -> float:
    """Weighted-average time to cashflow, weights = PV(cf) / price."""
    times = bond.cashflow_times()
    cfs = bond.cashflows()
    price = price_from_yield(bond, y)
    weighted = sum(t * cf / (1 + y / bond.freq) ** (t * bond.freq) for cf, t in zip(cfs, times))
    return weighted / price


def modified_duration(bond: Bond, y: float) -> float:
    """Macaulay duration adjusted for compounding frequency: D_mod = D_mac / (1 + y/freq)."""
    return macaulay_duration(bond, y) / (1 + y / bond.freq)


def convexity(bond: Bond, y: float) -> float:
    """Second-order price sensitivity, in the convention where
    price_change_pct ≈ -D_mod * dy + 0.5 * C * dy^2.
    """
    times = bond.cashflow_times()
    cfs = bond.cashflows()
    price = price_from_yield(bond, y)
    total = sum(
        cf * t * (t + 1 / bond.freq) / (1 + y / bond.freq) ** (t * bond.freq + 2)
        for cf, t in zip(cfs, times)
    )
    return total / price


def dv01(bond: Bond, y: float) -> float:
    """Dollar value of a 1bp (0.0001) parallel yield move, per 100 face.
    Computed by finite difference (full repricing), not the duration
    approximation - this is the thing DV01 is supposed to measure directly.
    """
    bump = 0.0001
    p_up = price_from_yield(bond, y + bump)
    p_down = price_from_yield(bond, y - bump)
    return (p_down - p_up) / 2


def price_change_duration_convexity_approx(bond: Bond, y: float, dy: float) -> float:
    """Second-order Taylor approximation of the price change for a yield
    move dy, using modified duration and convexity. For comparing against
    the exact repriced change - that comparison IS the convexity picture.
    """
    price = price_from_yield(bond, y)
    d_mod = modified_duration(bond, y)
    c = convexity(bond, y)
    pct_change = -d_mod * dy + 0.5 * c * dy**2
    return price * pct_change
