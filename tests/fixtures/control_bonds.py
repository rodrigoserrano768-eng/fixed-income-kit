"""Three control bonds with market data captured from a public source, used
to verify bond_math.py against real quoted prices/yields.

Source: investing.com rates & bonds pages, fetched 2026-10-10, quote
timestamped "closed 09/10" (2026-10-09) on each page:
  - https://www.investing.com/rates-bonds/germany-10-year-bond-yield
  - https://www.investing.com/rates-bonds/france-10-year-bond-yield
  - https://www.investing.com/rates-bonds/italy-10-year-bond-yield

years_to_maturity is computed ACT/365.25 from the quote date (2026-10-09)
to the stated maturity date - see README for why this doesn't line up
exactly with the real coupon schedule.
"""
from datetime import date

VALUATION_DATE = date(2026, 10, 9)

CONTROL_BONDS = [
    {
        "name": "German Bund 3.00% 15/08/2033",
        "face": 100.0,
        "coupon_rate": 0.0300,
        "maturity_date": date(2033, 8, 15),
        "freq": 1,
        "market_yield": 0.03486,
        "market_price": 95.999,
        "source": "https://www.investing.com/rates-bonds/germany-10-year-bond-yield",
    },
    {
        "name": "French OAT 3.70% 25/11/2033",
        "face": 100.0,
        "coupon_rate": 0.0370,
        "maturity_date": date(2033, 11, 25),
        "freq": 1,
        "market_yield": 0.04858,
        "market_price": 90.885,
        "source": "https://www.investing.com/rates-bonds/france-10-year-bond-yield",
    },
    {
        "name": "Italian BTP 3.80% 01/03/2034",
        "face": 100.0,
        "coupon_rate": 0.0380,
        "maturity_date": date(2034, 3, 1),
        "freq": 1,
        "market_yield": 0.04588,
        "market_price": 94.20,
        "source": "https://www.investing.com/rates-bonds/italy-10-year-bond-yield",
    },
]


def years_to_maturity(bond_spec: dict) -> float:
    return (bond_spec["maturity_date"] - VALUATION_DATE).days / 365.25
