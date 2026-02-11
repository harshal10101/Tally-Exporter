"""
CSV Generator Service
Generates Tally-compatible CSV file with 24 columns
"""

import io
import csv
from typing import List, Dict


# Same columns as the Excel generator
TALLY_COLUMNS = [
    "Sr. No.",
    "Invoice Type",
    "Product",
    "Invoice No",
    "Invoice Date",
    "GST Registration",
    "GST State",
    "Party/Customer",
    "Order No",
    "Order Date",
    "Invoice Period From",
    "Invoice Period To",
    "Billing Frequency",
    "TDS Applicable",
    "GST TDS Applicable",
    "Ledger Name",
    "Submitted Qty",
    "Submitted Rate",
    "Delivered Qty",
    "Delivered Rate",
    "Amount",
    "CGST",
    "SGST",
    "Total Amount (with Tax)"
]


def generate_csv(data: List[Dict]) -> io.BytesIO:
    """
    Generate CSV file with extracted invoice data in Tally format.

    Args:
        data: List of extracted invoice data dictionaries

    Returns:
        BytesIO buffer containing the CSV file
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Write header
    writer.writerow(TALLY_COLUMNS)

    # Write data rows
    for row_idx, invoice in enumerate(data, 1):
        invoice_type = invoice.get("invoice_type", "").upper()

        row_data = [
            row_idx,
            invoice_type,
            invoice.get("product", "SMS"),
            invoice.get("invoice_no", ""),
            invoice.get("invoice_date", ""),
            invoice.get("gst_registration", ""),
            invoice.get("gst_state", ""),
            invoice.get("party_customer", ""),
            invoice.get("order_no", ""),
            invoice.get("order_date", ""),
            invoice.get("invoice_period_from", ""),
            invoice.get("invoice_period_to", ""),
            invoice.get("billing_frequency", ""),
            invoice.get("tds_applicable", "Yes"),
            invoice.get("gst_tds_applicable", "No"),
            invoice.get("ledger_name", ""),
            invoice.get("submitted_qty", ""),
            invoice.get("submitted_rate", ""),
            invoice.get("delivered_qty", ""),
            invoice.get("delivered_rate", ""),
            invoice.get("amount", ""),
            invoice.get("cgst", ""),
            invoice.get("sgst", ""),
            invoice.get("total_amount", "")
        ]

        writer.writerow(row_data)

    # Convert to bytes
    buffer = io.BytesIO()
    buffer.write(output.getvalue().encode("utf-8-sig"))  # BOM for Excel compatibility
    buffer.seek(0)

    return buffer
