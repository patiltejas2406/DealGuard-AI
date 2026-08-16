"""Deterministic 3-Statement Relationships & Accounting Validation Rules."""

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, List, Optional


def to_decimal(val: Any) -> Optional[Decimal]:
    """Convert number or string to Decimal safely without floating point inaccuracies."""
    if val is None:
        return None
    try:
        if isinstance(val, (int, float)):
            return Decimal(str(val))
        clean_str = str(val).strip().replace(",", "").replace("$", "").replace("€", "").replace("£", "")
        if clean_str.startswith("(") and clean_str.endswith(")"):
            clean_str = "-" + clean_str[1:-1]
        if clean_str in ["", "-", "N/A", "null", "None"]:
            return None
        return Decimal(clean_str)
    except (InvalidOperation, ValueError):
        return None


def to_float(val: Optional[Decimal], round_digits: int = 2) -> Optional[float]:
    """Convert Decimal back to float for JSON serialization."""
    if val is None:
        return None
    return float(val.quantize(Decimal(f"1e-{round_digits}"), rounding=ROUND_HALF_UP))


class StatementCalculationEngine:
    """Computes deterministic 3-statement relationships and validates accounting identities."""

    @staticmethod
    def calculate_income_statement(raw_items: Dict[str, Any]) -> Dict[str, Any]:
        """
        Derive Gross Profit, EBITDA, EBIT, EBT, and Net Income from raw line items.
        Maintains missing values explicitly rather than guessing.
        """
        d = {k.lower(): to_decimal(v) for k, v in raw_items.items()}

        revenue = d.get("revenue")
        cogs = d.get("cogs")
        opex = d.get("operating_expenses") or d.get("opex")
        dna = d.get("depreciation_amortization") or d.get("dna") or d.get("d_and_a")
        interest = d.get("interest_expense") or d.get("interest")
        taxes = d.get("taxes") or d.get("tax_expense")

        # 1. Gross Profit = Revenue - COGS
        gross_profit = d.get("gross_profit")
        if gross_profit is None and revenue is not None and cogs is not None:
            gross_profit = revenue - cogs

        # 2. Operating Income / EBIT = Gross Profit - OpEx (or Revenue - COGS - OpEx)
        ebit = d.get("ebit") or d.get("operating_income")
        if ebit is None and gross_profit is not None and opex is not None:
            ebit = gross_profit - opex

        # 3. EBITDA = EBIT + D&A (or Gross Profit - OpEx + D&A)
        ebitda = d.get("ebitda")
        if ebitda is None and ebit is not None and dna is not None:
            ebitda = ebit + dna

        # 4. EBT = EBIT - Interest
        ebt = d.get("ebt")
        if ebt is None and ebit is not None and interest is not None:
            ebt = ebit - interest

        # 5. Net Income = EBT - Taxes (or EBIT - Interest - Taxes)
        net_income = d.get("net_income")
        if net_income is None and ebt is not None and taxes is not None:
            net_income = ebt - taxes
        elif net_income is None and ebit is not None and interest is not None and taxes is not None:
            net_income = ebit - interest - taxes

        return {
            "revenue": to_float(revenue),
            "cogs": to_float(cogs),
            "gross_profit": to_float(gross_profit),
            "operating_expenses": to_float(opex),
            "ebitda": to_float(ebitda),
            "depreciation_amortization": to_float(dna),
            "ebit": to_float(ebit),
            "interest_expense": to_float(interest),
            "taxes": to_float(taxes),
            "net_income": to_float(net_income),
        }

    @staticmethod
    def calculate_balance_sheet(raw_items: Dict[str, Any]) -> Dict[str, Any]:
        """
        Derive Total Current Assets, Total Assets, Total Current Liabilities,
        Total Liabilities, and check balance sheet equation.
        """
        d = {k.lower(): to_decimal(v) for k, v in raw_items.items()}

        cash = d.get("cash") or d.get("cash_and_equivalents")
        ar = d.get("accounts_receivable") or d.get("ar")
        inventory = d.get("inventory")
        other_ca = d.get("other_current_assets")

        ppe = d.get("ppe") or d.get("property_plant_equipment")
        intangibles = d.get("intangible_assets") or d.get("goodwill")
        other_nca = d.get("other_non_current_assets")

        ap = d.get("accounts_payable") or d.get("ap")
        accrued = d.get("accrued_liabilities") or d.get("accrued_expenses")
        short_term_debt = d.get("short_term_debt") or d.get("current_debt")
        other_cl = d.get("other_current_liabilities")

        long_term_debt = d.get("long_term_debt") or d.get("debt")
        other_ncl = d.get("other_non_current_liabilities")

        equity = d.get("equity") or d.get("total_equity") or d.get("shareholders_equity")

        # Total Current Assets
        total_ca = d.get("total_current_assets")
        if total_ca is None and any(x is not None for x in [cash, ar, inventory, other_ca]):
            total_ca = (cash or Decimal(0)) + (ar or Decimal(0)) + (inventory or Decimal(0)) + (other_ca or Decimal(0))

        # Total Assets
        total_assets = d.get("total_assets")
        if total_assets is None and total_ca is not None:
            total_assets = total_ca + (ppe or Decimal(0)) + (intangibles or Decimal(0)) + (other_nca or Decimal(0))

        # Total Current Liabilities
        total_cl = d.get("total_current_liabilities")
        if total_cl is None and any(x is not None for x in [ap, accrued, short_term_debt, other_cl]):
            total_cl = (ap or Decimal(0)) + (accrued or Decimal(0)) + (short_term_debt or Decimal(0)) + (other_cl or Decimal(0))

        # Total Liabilities
        total_liab = d.get("total_liabilities")
        if total_liab is None and total_cl is not None:
            total_liab = total_cl + (long_term_debt or Decimal(0)) + (other_ncl or Decimal(0))

        # Total Liabilities + Equity
        total_liab_equity = None
        if total_liab is not None and equity is not None:
            total_liab_equity = total_liab + equity

        # Balance check: Assets == Liabilities + Equity
        is_balanced = None
        balance_discrepancy = None
        if total_assets is not None and total_liab_equity is not None:
            diff = total_assets - total_liab_equity
            is_balanced = abs(diff) < Decimal("0.01")
            balance_discrepancy = to_float(diff)

        return {
            "cash_and_equivalents": to_float(cash),
            "accounts_receivable": to_float(ar),
            "inventory": to_float(inventory),
            "other_current_assets": to_float(other_ca),
            "total_current_assets": to_float(total_ca),
            "property_plant_equipment": to_float(ppe),
            "intangible_assets": to_float(intangibles),
            "other_non_current_assets": to_float(other_nca),
            "total_assets": to_float(total_assets),
            "accounts_payable": to_float(ap),
            "accrued_liabilities": to_float(accrued),
            "short_term_debt": to_float(short_term_debt),
            "other_current_liabilities": to_float(other_cl),
            "total_current_liabilities": to_float(total_cl),
            "long_term_debt": to_float(long_term_debt),
            "other_non_current_liabilities": to_float(other_ncl),
            "total_liabilities": to_float(total_liab),
            "total_equity": to_float(equity),
            "total_liabilities_and_equity": to_float(total_liab_equity),
            "is_balanced": is_balanced,
            "balance_discrepancy": balance_discrepancy,
        }

    @staticmethod
    def calculate_cash_flow(raw_items: Dict[str, Any]) -> Dict[str, Any]:
        """Derive CFO, CFI, CFF, and Net Change in Cash."""
        d = {k.lower(): to_decimal(v) for k, v in raw_items.items()}

        net_income = d.get("net_income")
        dna = d.get("depreciation_amortization") or d.get("dna")
        wc_change = d.get("working_capital_change") or d.get("delta_wc")
        other_operating = d.get("other_operating_activities")

        cfo = d.get("cfo") or d.get("cash_flow_from_operations")
        if cfo is None and net_income is not None:
            cfo = net_income + (dna or Decimal(0)) - (wc_change or Decimal(0)) + (other_operating or Decimal(0))

        capex = d.get("capex") or d.get("capital_expenditures")
        acquisitions = d.get("acquisitions")
        other_investing = d.get("other_investing_activities")

        cfi = d.get("cfi") or d.get("cash_flow_from_investing")
        if cfi is None and capex is not None:
            # Note: CapEx is cash outflow (negative)
            cfi = -(abs(capex)) - (abs(acquisitions) if acquisitions else Decimal(0)) + (other_investing or Decimal(0))

        debt_issued = d.get("debt_issued") or d.get("debt_financing")
        debt_repaid = d.get("debt_repaid")
        equity_issued = d.get("equity_issued")
        dividends = d.get("dividends_paid") or d.get("dividends")

        cff = d.get("cff") or d.get("cash_flow_from_financing")
        if cff is None and any(x is not None for x in [debt_issued, debt_repaid, equity_issued, dividends]):
            cff = (debt_issued or Decimal(0)) - (abs(debt_repaid) if debt_repaid else Decimal(0)) + (equity_issued or Decimal(0)) - (abs(dividends) if dividends else Decimal(0))

        net_change_cash = d.get("net_change_in_cash")
        if net_change_cash is None and cfo is not None and cfi is not None and cff is not None:
            net_change_cash = cfo + cfi + cff

        return {
            "net_income": to_float(net_income),
            "depreciation_amortization": to_float(dna),
            "working_capital_change": to_float(wc_change),
            "cash_flow_from_operations": to_float(cfo),
            "capital_expenditures": to_float(capex),
            "cash_flow_from_investing": to_float(cfi),
            "cash_flow_from_financing": to_float(cff),
            "net_change_in_cash": to_float(net_change_cash),
        }
