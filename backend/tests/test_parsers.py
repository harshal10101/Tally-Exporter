"""
Unit tests for invoice parsers.
Tests each parser with realistic sample text to verify regex extraction.
"""

import pytest
from parsers.cloudxp_parser import CloudXPParser
from parsers.rjil_parser import RJILParser
from parsers.jtl_parser import JTLParser


# --- Sample text fixtures ---

CLOUDXP_SAMPLE_TEXT = """
TAX INVOICE (ORIGINAL)

Account Number: 123456789
Invoice Number: CXP2025001234
Invoice Date: 15.11.2025
GST Registration Number: 27AABCN1234Q1ZM

Billed To: NSE CLEARING LIMITED
Address: C1 Block, Mumbai

PO Number: ASL/ 5500546061 PO Date: 10.08.2025
Invoice Period: 01-Nov-2025 to 30-Nov-2025

Delivered Segment Charges
1 SMS Service 998599 98,81,102.00 0.090000 8,89,299.18

Submitted Segment DLT
2 SMS Service 998599 1,23,94,994.00 0.020000 2,47,899.88
Charges

Total Amount: 11,37,199.06

CGST @9% 1,02,347.92
SGST @9% 1,02,347.92

Grand Total (Including Tax): 13,41,894.90

Remarks: Bulk SMS Service - PROMOTIONAL
"""

RJIL_SAMPLE_TEXT = """
ORIGINAL FOR RECIPIENT Tax Invoice
Reliance Jio Infocomm Limited

Invoice no. 987654321
Invoice date 25.10.2025
GSTIN 27AAGCR1234E1ZR

Recipient NSE CLEARING LIMITED, C1 BLOCK G, MUMBAI

PO No. 2526NSCCLIT94
PO Date. 01.10.2025
Invoice period 01.10.2025-31.10.2025

BULK SMS 998599 5,00,000 EA 0.15 75,000.00

Total Amount Excluding Taxes 75,000.00

CGST 9.00% 6,750.00
SGST 9.00% 6,750.00

Grand Total (Including GST) 88,500.00

Remarks: Bulk SMS Service - TRANSACTIONAL
"""

JTL_SAMPLE_TEXT = """
Jio Things Limited
TAX INVOICE

Invoice No. JTL2025004567
Date: 20.12.2025
GSTIN 27AABCJ5678P1Z5

Recipient No    8140817
Recipient       BHARATIYA JANATA PARTY

ORN: 77001234
Invoice Period: 01.12.2025-31.12.2025

SMS # SCRUBBING 998599 50,000.00 0.020000 1,000.00

BSS SERVICE CHARGE 998599 2,50,000.00 0.080000 20,000.00

Total Taxable value 21,000.00

CGST @9% 1,890.00
SGST @9% 1,890.00

Total ( Value is inclusive of Tax ) 24,780.00

Remarks: Bulk SMS Service - TRANSACTIONAL
"""


# --- CloudXP Parser Tests ---

class TestCloudXPParser:
    def setup_method(self):
        self.parser = CloudXPParser()

    def test_invoice_number(self):
        result = self.parser.parse(CLOUDXP_SAMPLE_TEXT, "test.pdf")
        assert result["invoice_no"] == "CXP2025001234"

    def test_invoice_date(self):
        result = self.parser.parse(CLOUDXP_SAMPLE_TEXT, "test.pdf")
        assert result["invoice_date"] == "15/11/2025"

    def test_gst_registration(self):
        result = self.parser.parse(CLOUDXP_SAMPLE_TEXT, "test.pdf")
        assert result["gst_registration"] == "27AABCN1234Q1ZM"

    def test_gst_state(self):
        result = self.parser.parse(CLOUDXP_SAMPLE_TEXT, "test.pdf")
        assert result["gst_state"] == "Maharashtra"

    def test_party_customer(self):
        result = self.parser.parse(CLOUDXP_SAMPLE_TEXT, "test.pdf")
        assert result["party_customer"] == "NSE CLEARING LIMITED"

    def test_order_no(self):
        result = self.parser.parse(CLOUDXP_SAMPLE_TEXT, "test.pdf")
        assert "5500546061" in result["order_no"]

    def test_order_date(self):
        result = self.parser.parse(CLOUDXP_SAMPLE_TEXT, "test.pdf")
        assert result["order_date"] == "10/08/2025"

    def test_invoice_period(self):
        result = self.parser.parse(CLOUDXP_SAMPLE_TEXT, "test.pdf")
        assert result["invoice_period_from"] == "01/11/2025"
        assert result["invoice_period_to"] == "30/11/2025"

    def test_billing_frequency_monthly(self):
        result = self.parser.parse(CLOUDXP_SAMPLE_TEXT, "test.pdf")
        assert result["billing_frequency"] == "Monthly"

    def test_delivered_qty(self):
        result = self.parser.parse(CLOUDXP_SAMPLE_TEXT, "test.pdf")
        assert result["delivered_qty"] == "9881102"

    def test_delivered_rate(self):
        result = self.parser.parse(CLOUDXP_SAMPLE_TEXT, "test.pdf")
        assert result["delivered_rate"] == "0.090000"

    def test_submitted_qty(self):
        result = self.parser.parse(CLOUDXP_SAMPLE_TEXT, "test.pdf")
        assert result["submitted_qty"] == "12394994"

    def test_submitted_rate(self):
        result = self.parser.parse(CLOUDXP_SAMPLE_TEXT, "test.pdf")
        assert result["submitted_rate"] == "0.020000"

    def test_amount(self):
        result = self.parser.parse(CLOUDXP_SAMPLE_TEXT, "test.pdf")
        assert result["amount"] == "1137199.06"

    def test_cgst(self):
        result = self.parser.parse(CLOUDXP_SAMPLE_TEXT, "test.pdf")
        assert result["cgst"] == "102347.92"

    def test_sgst(self):
        result = self.parser.parse(CLOUDXP_SAMPLE_TEXT, "test.pdf")
        assert result["sgst"] == "102347.92"

    def test_total_amount(self):
        result = self.parser.parse(CLOUDXP_SAMPLE_TEXT, "test.pdf")
        assert result["total_amount"] == "1341894.90"

    def test_tds_applicable(self):
        result = self.parser.parse(CLOUDXP_SAMPLE_TEXT, "test.pdf")
        assert result["tds_applicable"] == "Yes"

    def test_gst_tds_applicable(self):
        result = self.parser.parse(CLOUDXP_SAMPLE_TEXT, "test.pdf")
        assert result["gst_tds_applicable"] == "No"

    def test_ledger_name(self):
        result = self.parser.parse(CLOUDXP_SAMPLE_TEXT, "test.pdf")
        assert "Bulk SMS Charges" in result["ledger_name"]
        assert "Nov-25" in result["ledger_name"]

    def test_empty_text(self):
        result = self.parser.parse("", "empty.pdf")
        assert result["invoice_no"] == ""
        assert result["amount"] == ""


# --- RJIL Parser Tests ---

class TestRJILParser:
    def setup_method(self):
        self.parser = RJILParser()

    def test_invoice_number(self):
        result = self.parser.parse(RJIL_SAMPLE_TEXT, "test.pdf")
        assert result["invoice_no"] == "987654321"

    def test_invoice_date(self):
        result = self.parser.parse(RJIL_SAMPLE_TEXT, "test.pdf")
        assert result["invoice_date"] == "25/10/2025"

    def test_gst_registration(self):
        result = self.parser.parse(RJIL_SAMPLE_TEXT, "test.pdf")
        assert result["gst_registration"] == "27AAGCR1234E1ZR"

    def test_gst_state(self):
        result = self.parser.parse(RJIL_SAMPLE_TEXT, "test.pdf")
        assert result["gst_state"] == "Maharashtra"

    def test_party_customer(self):
        result = self.parser.parse(RJIL_SAMPLE_TEXT, "test.pdf")
        assert "NSE CLEARING LIMITED" in result["party_customer"]

    def test_order_no(self):
        result = self.parser.parse(RJIL_SAMPLE_TEXT, "test.pdf")
        assert result["order_no"] == "2526NSCCLIT94"

    def test_order_date(self):
        result = self.parser.parse(RJIL_SAMPLE_TEXT, "test.pdf")
        assert result["order_date"] == "01/10/2025"

    def test_invoice_period(self):
        result = self.parser.parse(RJIL_SAMPLE_TEXT, "test.pdf")
        assert result["invoice_period_from"] == "01/10/2025"
        assert result["invoice_period_to"] == "31/10/2025"

    def test_billing_frequency(self):
        result = self.parser.parse(RJIL_SAMPLE_TEXT, "test.pdf")
        assert result["billing_frequency"] == "Monthly"

    def test_delivered_qty(self):
        result = self.parser.parse(RJIL_SAMPLE_TEXT, "test.pdf")
        assert result["delivered_qty"] == "500000"

    def test_amount(self):
        result = self.parser.parse(RJIL_SAMPLE_TEXT, "test.pdf")
        assert result["amount"] == "75000.00"

    def test_cgst(self):
        result = self.parser.parse(RJIL_SAMPLE_TEXT, "test.pdf")
        assert result["cgst"] == "6750.00"

    def test_sgst(self):
        result = self.parser.parse(RJIL_SAMPLE_TEXT, "test.pdf")
        assert result["sgst"] == "6750.00"

    def test_total_amount(self):
        result = self.parser.parse(RJIL_SAMPLE_TEXT, "test.pdf")
        assert result["total_amount"] == "88500.00"

    def test_submitted_qty_empty_for_rjil(self):
        """RJIL only has bulk SMS, no separate submitted qty."""
        result = self.parser.parse(RJIL_SAMPLE_TEXT, "test.pdf")
        assert result["submitted_qty"] == ""

    def test_empty_text(self):
        result = self.parser.parse("", "empty.pdf")
        assert result["invoice_no"] == ""


# --- JTL Parser Tests ---

class TestJTLParser:
    def setup_method(self):
        self.parser = JTLParser()

    def test_invoice_number(self):
        result = self.parser.parse(JTL_SAMPLE_TEXT, "test.pdf")
        assert result["invoice_no"] == "JTL2025004567"

    def test_invoice_date(self):
        result = self.parser.parse(JTL_SAMPLE_TEXT, "test.pdf")
        assert result["invoice_date"] == "20/12/2025"

    def test_gst_registration(self):
        result = self.parser.parse(JTL_SAMPLE_TEXT, "test.pdf")
        assert result["gst_registration"] == "27AABCJ5678P1Z5"

    def test_gst_state(self):
        result = self.parser.parse(JTL_SAMPLE_TEXT, "test.pdf")
        assert result["gst_state"] == "Maharashtra"

    def test_party_customer(self):
        result = self.parser.parse(JTL_SAMPLE_TEXT, "test.pdf")
        assert "BHARATIYA JANATA PARTY" in result["party_customer"]

    def test_order_no(self):
        result = self.parser.parse(JTL_SAMPLE_TEXT, "test.pdf")
        assert result["order_no"] == "77001234"

    def test_order_date_empty_for_jtl(self):
        """JTL invoices don't have Order Date."""
        result = self.parser.parse(JTL_SAMPLE_TEXT, "test.pdf")
        assert result["order_date"] == ""

    def test_invoice_period(self):
        result = self.parser.parse(JTL_SAMPLE_TEXT, "test.pdf")
        assert result["invoice_period_from"] == "01/12/2025"
        assert result["invoice_period_to"] == "31/12/2025"

    def test_billing_frequency(self):
        result = self.parser.parse(JTL_SAMPLE_TEXT, "test.pdf")
        assert result["billing_frequency"] == "Monthly"

    def test_submitted_qty_from_dlt(self):
        result = self.parser.parse(JTL_SAMPLE_TEXT, "test.pdf")
        assert result["submitted_qty"] == "50000"

    def test_delivered_qty_from_bss(self):
        result = self.parser.parse(JTL_SAMPLE_TEXT, "test.pdf")
        assert result["delivered_qty"] == "250000"

    def test_amount(self):
        result = self.parser.parse(JTL_SAMPLE_TEXT, "test.pdf")
        assert result["amount"] == "21000.00"

    def test_cgst(self):
        result = self.parser.parse(JTL_SAMPLE_TEXT, "test.pdf")
        assert result["cgst"] == "1890.00"

    def test_sgst(self):
        result = self.parser.parse(JTL_SAMPLE_TEXT, "test.pdf")
        assert result["sgst"] == "1890.00"

    def test_total_amount(self):
        result = self.parser.parse(JTL_SAMPLE_TEXT, "test.pdf")
        assert result["total_amount"] == "24780.00"

    def test_ledger_name(self):
        result = self.parser.parse(JTL_SAMPLE_TEXT, "test.pdf")
        assert "Bulk SMS Charges" in result["ledger_name"]
        assert "Dec-25" in result["ledger_name"]

    def test_empty_text(self):
        result = self.parser.parse("", "empty.pdf")
        assert result["invoice_no"] == ""
