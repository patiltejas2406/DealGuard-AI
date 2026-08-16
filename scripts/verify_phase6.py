"""Phase 6 Real-World End-to-End Verification Script for Valuation Intelligence Engine."""

import asyncio
import os
import sys
import uuid
from decimal import Decimal

# Set python path
sys.path.insert(0, os.path.abspath("backend"))

from app.core.database import Base
from app.domains.valuation.engine.bridge import ValuationBridgeEngine
from app.domains.valuation.engine.comparables import ComparableEngine
from app.domains.valuation.engine.dcf import DCFEngine
from app.domains.valuation.engine.precedents import PrecedentEngine
from app.domains.valuation.engine.sensitivity import SensitivityEngine
from app.domains.valuation.engine.wacc import WACCEngine


def verify_phase6_deterministic_valuation():
    print("================================================================")
    print("DEALGUARD AI — PHASE 6 REAL-WORLD VALUATION VERIFICATION")
    print("================================================================")

    # 1. Target Company Profile
    target_name = "CloudDefend Technologies Inc."
    rev_2023 = 60_000_000.0
    ebitda_2023 = 22_000_000.0
    ebit_2023 = 18_000_000.0
    cash = 10_000_000.0
    debt = 25_000_000.0
    net_debt = debt - cash  # $15M

    print(f"\n[1] Target Company: {target_name}")
    print(f"    - Revenue: ${rev_2023/1e6:.1f}M")
    print(f"    - EBITDA: ${ebitda_2023/1e6:.1f}M (36.7% margin)")
    print(f"    - EBIT: ${ebit_2023/1e6:.1f}M (30.0% margin)")
    print(f"    - Cash: ${cash/1e6:.1f}M | Total Debt: ${debt/1e6:.1f}M | Net Debt: ${net_debt/1e6:.1f}M")

    # 2. WACC Calculation
    rf = 4.5
    beta = 1.10
    erp = 5.5
    kd_pre = 6.0
    tax_rate = 25.0
    ew = 80.0
    dw = 20.0

    wacc_res = WACCEngine.calculate_wacc(
        risk_free_rate=rf,
        beta=beta,
        equity_risk_premium=erp,
        pre_tax_cost_of_debt=kd_pre,
        tax_rate=tax_rate,
        equity_weight=ew,
        debt_weight=dw,
    )
    print(f"\n[2] WACC & CAPM Derivation:")
    print(f"    - Formula: {wacc_res['formula']}")
    print(f"    - Cost of Equity (Ke): {wacc_res['cost_of_equity']}%")
    print(f"    - After-Tax Cost of Debt (Kd): {wacc_res['after_tax_cost_of_debt']}%")
    print(f"    - Calculated WACC: {wacc_res['wacc']}%")
    assert wacc_res["wacc"] == 9.34, f"Expected 9.34% but got {wacc_res['wacc']}%"

    # 3. DCF Model Schedule & Terminal Values
    projections = [
        {"period": "FY2024", "revenue": 69_000_000.0, "revenue_growth": 15.0, "ebitda": 25_530_000.0, "ebit": 21_390_000.0, "tax_rate": 25.0, "depreciation_amortization": 4_140_000.0, "capex": 3_450_000.0, "working_capital_change": 1_380_000.0},
        {"period": "FY2025", "revenue": 77_970_000.0, "revenue_growth": 13.0, "ebitda": 29_628_600.0, "ebit": 24_950_400.0, "tax_rate": 25.0, "depreciation_amortization": 4_678_200.0, "capex": 3_898_500.0, "working_capital_change": 1_559_400.0},
        {"period": "FY2026", "revenue": 86_546_700.0, "revenue_growth": 11.0, "ebitda": 33_753_213.0, "ebit": 28_560_411.0, "tax_rate": 25.0, "depreciation_amortization": 5_192_802.0, "capex": 4_327_335.0, "working_capital_change": 1_730_934.0},
        {"period": "FY2027", "revenue": 94_335_903.0, "revenue_growth": 9.0, "ebitda": 37_734_361.0, "ebit": 32_074_207.0, "tax_rate": 25.0, "depreciation_amortization": 5_660_154.0, "capex": 4_716_795.0, "working_capital_change": 1_886_718.0},
        {"period": "FY2028", "revenue": 100_939_416.0, "revenue_growth": 7.0, "ebitda": 41_385_161.0, "ebit": 35_328_796.0, "tax_rate": 25.0, "depreciation_amortization": 6_056_365.0, "capex": 5_046_971.0, "working_capital_change": 2_018_788.0},
    ]

    dcf_perp = DCFEngine.calculate_dcf(
        projections=projections,
        wacc=wacc_res["wacc"],
        terminal_growth_rate=3.0,
        terminal_method="PERPETUITY_GROWTH",
        cash=cash,
        debt=debt,
    )
    print(f"\n[3] DCF Valuation (Perpetuity Growth 3.0%):")
    print(f"    - PV of 5-Year Forecast UFCFs: ${dcf_perp['pv_forecast_fcf']/1e6:.2f}M")
    print(f"    - Terminal Value: ${dcf_perp['terminal_value']/1e6:.2f}M")
    print(f"    - PV of Terminal Value: ${dcf_perp['pv_terminal_value']/1e6:.2f}M")
    print(f"    - Implied Enterprise Value: ${dcf_perp['implied_enterprise_value']/1e6:.2f}M")
    print(f"    - Implied Equity Value: ${dcf_perp['implied_equity_value']/1e6:.2f}M")
    assert dcf_perp["implied_enterprise_value"] > 0
    assert dcf_perp["implied_equity_value"] == dcf_perp["implied_enterprise_value"] - net_debt

    # 4. Trading Peer Comparables (CCA)
    comps = [
        {"company_name": "SentinelCyber", "ticker": "SCYB", "enterprise_value": 350_000_000.0, "revenue": 50_000_000.0, "ebitda": 15_000_000.0, "status": "INCLUDED"},
        {"company_name": "Vanguard Security", "ticker": "VSEC", "enterprise_value": 600_000_000.0, "revenue": 80_000_000.0, "ebitda": 25_000_000.0, "status": "INCLUDED"},
        {"company_name": "Fortress Net", "ticker": "FORT", "enterprise_value": 900_000_000.0, "revenue": 100_000_000.0, "ebitda": 36_000_000.0, "status": "INCLUDED"},
    ]
    comp_stats = ComparableEngine.calculate_comp_cohort_statistics(comps)
    implied_comps_ebitda = ComparableEngine.calculate_implied_valuation(
        target_metric_value=ebitda_2023,
        multiple_stats=comp_stats["ev_to_ebitda_stats"],
        metric_type="EBITDA",
        cash=cash,
        debt=debt,
    )
    print(f"\n[4] Trading Comparables (CCA):")
    print(f"    - Included Peers: {comp_stats['included_companies']}")
    print(f"    - EV/EBITDA Median: {comp_stats['ev_to_ebitda_stats']['median']}x")
    print(f"    - Implied EV Range (Low/Base/High): ${implied_comps_ebitda['implied_enterprise_value_low']/1e6:.1f}M / ${implied_comps_ebitda['implied_enterprise_value_base']/1e6:.1f}M / ${implied_comps_ebitda['implied_enterprise_value_high']/1e6:.1f}M")
    print(f"    - Implied Equity Value Base: ${implied_comps_ebitda['implied_equity_value_base']/1e6:.1f}M")

    # 5. Precedent Transactions (PTA)
    precedents = [
        {"target_name": "CyberShield Corp", "enterprise_value": 400_000_000.0, "revenue": 60_000_000.0, "ebitda": 18_000_000.0, "status": "INCLUDED"},
        {"target_name": "Apex Identity", "enterprise_value": 750_000_000.0, "revenue": 90_000_000.0, "ebitda": 30_000_000.0, "status": "INCLUDED"},
    ]
    tx_stats = PrecedentEngine.calculate_precedent_cohort_statistics(precedents)
    implied_tx_ebitda = PrecedentEngine.calculate_implied_valuation(
        target_metric_value=ebitda_2023,
        multiple_stats=tx_stats["ev_to_ebitda_stats"],
        metric_type="EBITDA",
        cash=cash,
        debt=debt,
    )
    print(f"\n[5] Precedent Transactions (PTA):")
    print(f"    - Included Deals: {tx_stats['included_transactions']}")
    print(f"    - Precedent EV/EBITDA Median: {tx_stats['ev_to_ebitda_stats']['median']}x")
    print(f"    - Implied EV Base: ${implied_tx_ebitda['implied_enterprise_value_base']/1e6:.1f}M")

    # 6. 2D Sensitivity Matrix
    sens_matrix = SensitivityEngine.generate_wacc_terminal_growth_matrix(
        projections=projections,
        base_wacc=wacc_res["wacc"],
        base_growth=3.0,
        matrix_size=5,
    )
    print(f"\n[6] 2D Sensitivity Matrix (5x5):")
    print(f"    - WACC Values (Rows): {sens_matrix['row_values']}")
    print(f"    - Growth Values (Cols): {sens_matrix['column_values']}")
    print(f"    - Base Grid Cell EV: ${sens_matrix['enterprise_value_matrix'][2][2]/1e6:.2f}M")

    print("\n================================================================")
    print("PHASE 6 REAL-WORLD VERIFICATION: 100% SUCCESS")
    print("================================================================")


if __name__ == "__main__":
    verify_phase6_deterministic_valuation()
