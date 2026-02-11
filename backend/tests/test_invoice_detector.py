"""
Unit tests for invoice type detection.
"""

import pytest
from services.invoice_detector import detect_invoice_type


class TestInvoiceDetector:
    def test_detect_cloudxp(self):
        text = "TAX INVOICE (ORIGINAL)\nAccount Number: 12345"
        assert detect_invoice_type(text) == "cloudxp"

    def test_detect_rjil(self):
        text = "Reliance Jio Infocomm Limited\nORIGINAL FOR RECIPIENT Tax Invoice"
        assert detect_invoice_type(text) == "rjil"

    def test_detect_jtl(self):
        text = "Jio Things Limited\nTAX INVOICE"
        assert detect_invoice_type(text) == "jtl"

    def test_detect_unknown(self):
        text = "Some random document content"
        assert detect_invoice_type(text) == "unknown"

    def test_detect_case_insensitive(self):
        text = "tax invoice (original)\naccount number: 12345"
        assert detect_invoice_type(text) == "cloudxp"

    def test_detect_empty_text(self):
        assert detect_invoice_type("") == "unknown"

    def test_cloudxp_needs_both_markers(self):
        """CloudXP requires both TAX INVOICE (ORIGINAL) and ACCOUNT NUMBER."""
        text = "TAX INVOICE (ORIGINAL)\nSome other content"
        assert detect_invoice_type(text) != "cloudxp"

    def test_rjil_needs_both_markers(self):
        """RJIL requires both company name and ORIGINAL FOR RECIPIENT."""
        text = "Reliance Jio Infocomm Limited\nSome other content"
        assert detect_invoice_type(text) != "rjil"
