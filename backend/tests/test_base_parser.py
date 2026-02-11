"""
Unit tests for base parser utility methods.
"""

import pytest
from parsers.cloudxp_parser import CloudXPParser


class TestBaseParserMethods:
    """Test base parser utility methods through CloudXPParser instance."""

    def setup_method(self):
        self.parser = CloudXPParser()

    # --- format_date tests ---

    def test_format_date_dot_separator(self):
        assert self.parser.format_date("15.11.2025") == "15/11/2025"

    def test_format_date_dash_separator(self):
        assert self.parser.format_date("15-11-2025") == "15/11/2025"

    def test_format_date_slash_separator(self):
        assert self.parser.format_date("15/11/2025") == "15/11/2025"

    def test_format_date_month_abbr(self):
        assert self.parser.format_date("15-Nov-2025") == "15/11/2025"

    def test_format_date_month_full(self):
        assert self.parser.format_date("15-November-2025") == "15/11/2025"

    def test_format_date_iso(self):
        assert self.parser.format_date("2025-11-15") == "15/11/2025"

    def test_format_date_none(self):
        assert self.parser.format_date(None) == ""

    def test_format_date_empty(self):
        assert self.parser.format_date("") == ""

    # --- clean_amount tests ---

    def test_clean_amount_with_commas(self):
        assert self.parser.clean_amount("1,23,456.78") == "123456.78"

    def test_clean_amount_no_commas(self):
        assert self.parser.clean_amount("123456.78") == "123456.78"

    def test_clean_amount_none(self):
        assert self.parser.clean_amount(None) == ""

    # --- calculate_billing_frequency tests ---

    def test_billing_monthly(self):
        assert self.parser.calculate_billing_frequency("01/11/2025", "30/11/2025") == "Monthly"

    def test_billing_quarterly(self):
        assert self.parser.calculate_billing_frequency("01/10/2025", "31/12/2025") == "Quarterly"

    def test_billing_half_yearly(self):
        assert self.parser.calculate_billing_frequency("01/07/2025", "31/12/2025") == "Half-Yearly"

    def test_billing_yearly(self):
        assert self.parser.calculate_billing_frequency("01/01/2025", "31/12/2025") == "Yearly"

    def test_billing_empty_dates(self):
        assert self.parser.calculate_billing_frequency("", "") == ""

    # --- generate_ledger_name tests ---

    def test_ledger_name_monthly(self):
        result = self.parser.generate_ledger_name("01/11/2025", "30/11/2025")
        assert result == "Bulk SMS Charges - Nov-25 to Nov-25"

    def test_ledger_name_quarterly(self):
        result = self.parser.generate_ledger_name("01/10/2025", "31/12/2025")
        assert result == "Bulk SMS Charges - Oct-25 to Dec-25"

    def test_ledger_name_empty(self):
        result = self.parser.generate_ledger_name("", "")
        assert result == "Bulk SMS Charges"

    # --- get_state_from_gst tests ---

    def test_state_maharashtra(self):
        assert self.parser.get_state_from_gst("27AABCN1234Q1ZM") == "Maharashtra"

    def test_state_delhi(self):
        assert self.parser.get_state_from_gst("07AABCD1234E1ZP") == "Delhi"

    def test_state_karnataka(self):
        assert self.parser.get_state_from_gst("29XYZPQ5678R1ZA") == "Karnataka"

    def test_state_invalid_gst(self):
        assert self.parser.get_state_from_gst("") == ""

    def test_state_none_gst(self):
        assert self.parser.get_state_from_gst(None) == ""

    # --- extract_field tests ---

    def test_extract_field_match(self):
        text = "Invoice Number: ABC123"
        result = self.parser.extract_field(text, r"Invoice\s*Number\s*:?\s*([A-Z0-9]+)")
        assert result == "ABC123"

    def test_extract_field_no_match(self):
        text = "Some other text"
        result = self.parser.extract_field(text, r"Invoice\s*Number\s*:?\s*([A-Z0-9]+)")
        assert result is None
