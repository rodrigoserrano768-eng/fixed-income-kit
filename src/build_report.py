"""CLI entry point: fetch the live ECB curve, price the 3 control bonds
against it, and render both required plots. Run with:
    python -m src.build_report
"""
from __future__ import annotations

from src.bond_math import Bond
from src.curve import fetch_curve
from src.plotting import plot_curve_with_bond, plot_price_yield_convexity
from tests.fixtures.control_bonds import CONTROL_BONDS, years_to_maturity


def main() -> int:
    curve = fetch_curve()
    curve.to_csv("outputs/ecb_curve_live.csv", index=False)
    print(f"Fetched ECB curve: {len(curve)} nodes, observed {curve['obs_date'].iloc[0]}")

    # Curve plot: mark the longest-dated control bond (the Italian BTP) on
    # the curve, since it best shows a bond pricing wide of the AAA curve -
    # Italy isn't AAA-rated, so its yield sits visibly above the curve.
    # That gap is a real, meaningful feature of the plot, not noise.
    btp = next(b for b in CONTROL_BONDS if "BTP" in b["name"])
    ax = plot_curve_with_bond(
        curve, bond_maturity_years=years_to_maturity(btp), bond_yield=btp["market_yield"], bond_name=btp["name"]
    )
    ax.figure.tight_layout()
    ax.figure.savefig("outputs/curve_with_bond.png", dpi=150)
    print("Saved outputs/curve_with_bond.png")

    # Convexity plot: the Bund, because it has the longest tenor among the
    # three and shows the curvature most clearly over a +/-300bp range.
    bund = next(b for b in CONTROL_BONDS if "Bund" in b["name"])
    bond = Bond(face=bund["face"], coupon_rate=bund["coupon_rate"], years_to_maturity=years_to_maturity(bund), freq=bund["freq"])
    ax2 = plot_price_yield_convexity(bond, center_yield=bund["market_yield"])
    ax2.figure.tight_layout()
    ax2.figure.savefig("outputs/price_yield_convexity.png", dpi=150)
    print("Saved outputs/price_yield_convexity.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
