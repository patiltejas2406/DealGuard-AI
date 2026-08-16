"""Unit Tests for Financial Line-Item Normalization & String Parsing."""

import pytest
from app.domains.financials.extractor import FinancialNormalizer


def test_line_item_label_normalization():
    """Verify standard accounting synonyms map to canonical keys."""
    assert FinancialNormalizer.normalize_label("Total Revenues") == "revenue"
    assert FinancialNormalizer.normalize_label("Gross Sales") == "revenue"
    assert FinancialNormalizer.normalize_label("Cost of Goods Sold") == "cogs"
    assert FinancialNormalizer.normalize_label("Selling, General & Administrative") == "operating_expenses"
    assert FinancialNormalizer.normalize_label("Consolidated EBITDA") == "ebitda"
    assert FinancialNormalizer.normalize_label("Cash and Cash Equivalents") == "cash_and_equivalents"
    assert FinancialNormalizer.normalize_label("Trade Receivables") == "accounts_receivable"
    assert FinancialNormalizer.normalize_label("Property, Plant & Equipment") == "property_plant_equipment"
    assert FinancialNormalizer.normalize_label("Stockholders' Equity") == "total_equity"


def test_parse_financial_number_formats():
    """Verify parsing handles negative parentheses, commas, currencies, and scale units."""
    # Standard integers and floats
    assert FinancialNormalizer.parse_financial_number(45000000) == 45000000.0
    assert FinancialNormalizer.parse_financial_number("45,200,000") == 45200000.0

    # Currency signs
    assert FinancialNormalizer.parse_financial_number("$ 12,850.50") == 12850.50
    assert FinancialNormalizer.parse_financial_number("€ 8,200.00") == 8200.00

    # Parentheses for negative numbers
    assert FinancialNormalizer.parse_financial_number("(1,450,000)") == -1450000.0
    assert FinancialNormalizer.parse_financial_number("($ 350.25)") == -350.25

    # Scale units (Millions / Thousands)
    assert FinancialNormalizer.parse_financial_number("45.2M") == 45200000.0
    assert FinancialNormalizer.parse_financial_number("850K") == 850000.0
    assert FinancialNormalizer.parse_financial_number("1.4 bn") == 1400000000.0

    # Empty and dashes
    assert FinancialNormalizer.parse_financial_number("-") is None
    assert FinancialNormalizer.parse_financial_number("N/A") is None
    assert FinancialNormalizer.parse_financial_number("") is None


def test_extract_statement_from_table():
    """Verify extracting a full income statement from a raw table matrix."""
    table = [
        ["Total Revenue", "$ 45.2 M"],
        ["Cost of Goods Sold", "$ 10.4 M"],
        ["Operating Expenses", "$ 25.7 M"],
        ["Depreciation & Amortization", "$ 1.8 M"],
    ]
    stmt = FinancialNormalizer.extract_statement_from_table(table, statement_type="INCOME_STATEMENT")
    assert stmt["revenue"] == 45200000.0
    assert stmt["cogs"] == 10400000.0
    assert stmt["gross_profit"] == 34800000.0
    assert stmt["ebit"] == 9100000.0
    assert stmt["ebitda"] == 10900000.0
