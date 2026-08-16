"""Financial Statement Table Extraction, Line-Item Normalization & Numerical Parsing."""

import re
from typing import Any, Dict, List, Optional
from app.domains.financials.engine.statements import StatementCalculationEngine


class FinancialNormalizer:
    """Normalizes unstructured financial rows, synonyms, and string representations into canonical schema."""

    SYNONYM_MAP = {
        # Income Statement
        "revenue": [
            "revenue", "revenues", "total revenue", "total revenues", "net revenue", "net sales",
            "gross sales", "turnover", "total sales", "operating revenue", "gross revenue"
        ],
        "cogs": [
            "cogs", "cost of goods sold", "cost of sales", "cost of revenue", "cost of services",
            "direct costs", "cost of product sales", "cost of operations"
        ],
        "gross_profit": [
            "gross profit", "gross margin", "gross income"
        ],
        "operating_expenses": [
            "operating expenses", "opex", "total opex", "sga", "sg&a", "selling, general and administrative",
            "selling, general & administrative", "selling general and administrative", "general & administrative",
            "general and administrative", "total operating expenses", "indirect costs"
        ],
        "ebitda": [
            "ebitda", "operating ebitda", "adjusted ebitda", "consolidated ebitda", "normalized ebitda"
        ],
        "depreciation_amortization": [
            "depreciation & amortization", "depreciation and amortization", "d&a", "dna", "depreciation", "amortization"
        ],
        "ebit": [
            "ebit", "operating profit", "operating income", "profit from operations"
        ],
        "interest_expense": [
            "interest expense", "interest", "net interest", "interest and other expense", "finance costs"
        ],
        "taxes": [
            "taxes", "income tax", "income tax expense", "tax provision", "provision for income taxes"
        ],
        "net_income": [
            "net income", "net profit", "net earnings", "profit for the period", "net income (loss)"
        ],

        # Balance Sheet
        "cash_and_equivalents": [
            "cash", "cash and cash equivalents", "cash & cash equivalents", "cash and bank balances", "cash and short-term investments"
        ],
        "accounts_receivable": [
            "accounts receivable", "trade receivables", "ar", "receivables", "trade and other receivables"
        ],
        "inventory": [
            "inventory", "inventories", "stock", "raw materials and finished goods"
        ],
        "other_current_assets": [
            "other current assets", "prepaid expenses", "prepaids", "other ca"
        ],
        "total_current_assets": [
            "total current assets", "total ca"
        ],
        "property_plant_equipment": [
            "property, plant and equipment", "property, plant & equipment", "pp&e", "ppe", "fixed assets"
        ],
        "intangible_assets": [
            "intangible assets", "goodwill", "goodwill and intangibles", "intellectual property"
        ],
        "other_non_current_assets": [
            "other non-current assets", "other assets", "other non current assets", "non-current assets"
        ],
        "total_assets": [
            "total assets"
        ],
        "accounts_payable": [
            "accounts payable", "trade payables", "ap", "payables", "trade and other payables"
        ],
        "accrued_liabilities": [
            "accrued liabilities", "accrued expenses", "accruals", "other accrued expenses"
        ],
        "short_term_debt": [
            "short-term debt", "short term debt", "current portion of long-term debt", "current debt"
        ],
        "other_current_liabilities": [
            "other current liabilities", "other cl"
        ],
        "total_current_liabilities": [
            "total current liabilities", "total cl"
        ],
        "long_term_debt": [
            "long-term debt", "long term debt", "total debt", "senior debt", "notes payable", "borrowings", "debt"
        ],
        "other_non_current_liabilities": [
            "other non-current liabilities", "other non current liabilities", "deferred revenue"
        ],
        "total_liabilities": [
            "total liabilities"
        ],
        "total_equity": [
            "equity", "total equity", "shareholders' equity", "stockholders' equity", "retained earnings", "members' equity", "total stockholders' equity"
        ],
    }

    @classmethod
    def normalize_label(cls, label: str) -> Optional[str]:
        """Map raw accounting string to canonical line item key."""
        clean = re.sub(r"[^\w\s&]", " ", label.lower()).strip()
        clean = re.sub(r"\s+", " ", clean)

        for canonical, synonyms in cls.SYNONYM_MAP.items():
            for syn in synonyms:
                syn_clean = re.sub(r"[^\w\s&]", " ", syn.lower()).strip()
                syn_clean = re.sub(r"\s+", " ", syn_clean)

                if clean == syn_clean:
                    return canonical
                if clean.replace("&", "and") == syn_clean.replace("&", "and"):
                    return canonical
                # Word-boundary exact phrase match
                pattern = r"^" + re.escape(syn_clean) + r"(\s|$)"
                if re.match(pattern, clean) or re.match(pattern, clean.replace("&", "and")):
                    return canonical
        return None


    @classmethod
    def parse_financial_number(cls, raw_val: Any, unit_multiplier: float = 1.0) -> Optional[float]:
        """
        Parse raw financial cell (e.g. '$ (1,520.50) M', '45.2M', '140,000') into normalized float.
        """
        if raw_val is None:
            return None
        if isinstance(raw_val, (int, float)):
            return float(raw_val) * unit_multiplier

        s = str(raw_val).strip()
        if not s or s in ["-", "—", "N/A", "null", "None", "."]:
            return None

        # Check for multiplier suffix (M, K, B, etc.)
        multiplier = unit_multiplier
        if re.search(r"(\d|\s)(m|million|millions|mn)($|\s|[^\w])", s, re.IGNORECASE):
            multiplier = 1_000_000.0
            s = re.sub(r"(m|million|millions|mn)", "", s, flags=re.IGNORECASE)
        elif re.search(r"(\d|\s)(k|thousand|thousands)($|\s|[^\w])", s, re.IGNORECASE):
            multiplier = 1_000.0
            s = re.sub(r"(k|thousand|thousands)", "", s, flags=re.IGNORECASE)
        elif re.search(r"(\d|\s)(b|billion|billions|bn)($|\s|[^\w])", s, re.IGNORECASE):
            multiplier = 1_000_000_000.0
            s = re.sub(r"(b|billion|billions|bn)", "", s, flags=re.IGNORECASE)

        # Check for negative in parentheses: (1,234.50) -> -1234.50
        is_negative = False
        if "(" in s and ")" in s:
            is_negative = True
            s = s.replace("(", "").replace(")", "")
        elif s.startswith("-"):
            is_negative = True
            s = s.lstrip("-")

        # Strip currency symbols, spaces, and formatting characters
        clean_num = re.sub(r"[^\d\.]", "", s)
        if not clean_num:
            return None

        try:
            val = float(clean_num)
            if is_negative:
                val = -val
            return val * multiplier
        except ValueError:
            return None

    @classmethod
    def extract_statement_from_table(
        cls,
        table_rows: List[List[Any]],
        statement_type: str = "INCOME_STATEMENT",
        unit_multiplier: float = 1.0,
    ) -> Dict[str, Any]:
        """
        Extract canonical financial line items from raw matrix rows.
        """
        line_items: Dict[str, Any] = {}

        for row in table_rows:
            if not row or len(row) < 2:
                continue

            label_cell = str(row[0]).strip()
            canonical_key = cls.normalize_label(label_cell)
            if not canonical_key:
                continue

            # Look for first numeric cell in row
            for cell in row[1:]:
                val = cls.parse_financial_number(cell, unit_multiplier=unit_multiplier)
                if val is not None:
                    line_items[canonical_key] = val
                    break

        # Run derived calculation engine
        if statement_type == "INCOME_STATEMENT":
            return StatementCalculationEngine.calculate_income_statement(line_items)
        elif statement_type == "BALANCE_SHEET":
            return StatementCalculationEngine.calculate_balance_sheet(line_items)
        elif statement_type == "CASH_FLOW":
            return StatementCalculationEngine.calculate_cash_flow(line_items)

        return line_items
