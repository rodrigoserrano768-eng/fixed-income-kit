"""Fetch the ECB euro area AAA government bond yield curve (public, no key).

Source: ECB Statistical Data Warehouse (SDW), dataset YC (Euro area yield
curves), Svensson model spot rates, continuous compounding, AAA-rated
issuers. This is a par/spot curve derived by the ECB from AAA sovereign
bonds - not a swap/€STR curve. See README for why.
"""
from __future__ import annotations

import math

import pandas as pd
import requests

ECB_BASE = "https://data-api.ecb.europa.eu/service/data/YC"

# Maturities the ECB publishes spot rates for under this series.
MATURITY_CODES = {
    0.25: "SR_3M", 0.5: "SR_6M", 1: "SR_1Y", 2: "SR_2Y", 3: "SR_3Y",
    5: "SR_5Y", 7: "SR_7Y", 10: "SR_10Y", 15: "SR_15Y", 20: "SR_20Y", 30: "SR_30Y",
}


def fetch_spot_rate(maturity_code: str) -> tuple[str, float]:
    """Fetch the latest AAA euro area spot rate for one maturity code.
    Returns (observation_date, rate) where rate is continuously-compounded,
    as a decimal (e.g. 0.0288 for 2.88%).
    """
    url = f"{ECB_BASE}/B.U2.EUR.4F.G_N_A.SV_C_YM.{maturity_code}"
    resp = requests.get(url, params={"lastNObservations": 1, "format": "csvdata"}, timeout=20)
    resp.raise_for_status()
    df = pd.read_csv(pd.io.common.StringIO(resp.text))
    if df.empty:
        raise ValueError(f"ECB SDW returned no observations for {maturity_code}")
    row = df.iloc[-1]
    return str(row["TIME_PERIOD"]), float(row["OBS_VALUE"]) / 100.0


def fetch_curve() -> pd.DataFrame:
    """Fetch the full set of maturities in MATURITY_CODES. Returns a
    DataFrame with columns [maturity_years, rate, obs_date]. If one maturity
    fails to fetch, raises - a partial curve silently missing a tenor is
    worse than a visible failure here, since every downstream calc assumes
    the curve is complete at these nodes.
    """
    rows = []
    for maturity_years, code in sorted(MATURITY_CODES.items()):
        obs_date, rate = fetch_spot_rate(code)
        rows.append({"maturity_years": maturity_years, "rate": rate, "obs_date": obs_date})
    return pd.DataFrame(rows)


def interpolate_rate(curve: pd.DataFrame, maturity_years: float) -> float:
    """Linear interpolation on the curve's own (maturity, rate) nodes.
    Extrapolates flat beyond the curve's min/max published maturity rather
    than raising, since bonds used downstream can fall slightly outside
    the ECB's published node range (e.g. 0.6y) and a hard failure there
    would be worse than a flat-extrapolated estimate, clearly labeled.
    """
    curve = curve.sort_values("maturity_years")
    if maturity_years <= curve["maturity_years"].iloc[0]:
        return float(curve["rate"].iloc[0])
    if maturity_years >= curve["maturity_years"].iloc[-1]:
        return float(curve["rate"].iloc[-1])
    return float(
        pd.Series(curve["rate"].values, index=curve["maturity_years"].values)
        .reindex(sorted(set(curve["maturity_years"]) | {maturity_years}))
        .interpolate(method="index")
        .loc[maturity_years]
    )


def continuous_to_periodic(rate_cc: float, freq: int) -> float:
    """Convert a continuously-compounded rate to the periodic-compounding
    convention bond_math.py uses (compounded `freq` times/year)."""
    return freq * (math.exp(rate_cc / freq) - 1)
