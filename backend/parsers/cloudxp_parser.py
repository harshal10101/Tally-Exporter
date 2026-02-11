"""
CloudXP Invoice Parser
Parses invoices with Jio branding and "TAX INVOICE (ORIGINAL)" header
This handles 95% of invoices
"""

import re
from typing import Dict
from .base_parser import BaseParser


class CloudXPParser(BaseParser):
    """Parser for CloudXP format invoices (Jio branded)."""
    
    def parse(self, text: str, filename: str) -> Dict:
        """
        Parse CloudXP invoice and extract all required fields.
        
        Args:
            text: Extracted text from PDF
            filename: Original filename for reference
            
        Returns:
            Dictionary with all 21 Tally fields
        """
        # Extract Invoice Number
        invoice_no = self.extract_field(
            text, 
            r"Invoice\s*Number\s*:?\s*([A-Z0-9]+)"
        )
        
        # Extract Invoice Date
        invoice_date_raw = self.extract_field(
            text,
            r"Invoice\s*Date\s*:?\s*(\d{1,2}[-./]\w{3}[-./]\d{4}|\d{1,2}[-./]\d{1,2}[-./]\d{4})"
        )
        invoice_date = self.format_date(invoice_date_raw) if invoice_date_raw else ""
        
        # Extract GST Registration Number
        gst_registration = self.extract_field(
            text,
            r"GST\s*Registration\s*Number\s*:?\s*([A-Z0-9]+)"
        )
        
        # Extract GST State from GST number (first 2 digits)
        gst_state = self.get_state_from_gst(gst_registration)
        
        # Extract Billed To (Party/Customer)
        party_customer = self.extract_field(
            text,
            r"Billed\s*To\s*:?\s*([^\n]+)"
        )
        if party_customer:
            # Clean up - take only company name (first line)
            party_customer = party_customer.split("\n")[0].strip()
        
        # Extract PO Number (capture full PO including spaces and numbers like "ASL/ 5500546061")
        order_no = self.extract_field(
            text,
            r"PO\s*Number\s*:?\s*([A-Z0-9/\s]+?)(?:\s*PO\s*Date|\s*\n|$)"
        )
        if order_no:
            order_no = order_no.strip()
        
        # Extract PO Date
        order_date_raw = self.extract_field(
            text,
            r"PO\s*Date\s*:?\s*(\d{1,2}[-./]\w{3}[-./]\d{4}|\d{1,2}[-./]\d{1,2}[-./]\d{4})"
        )
        order_date = self.format_date(order_date_raw) if order_date_raw else ""
        
        # Extract Invoice Period
        invoice_period = self.extract_field(
            text,
            r"Invoice\s*Period\s*:?\s*(\d{1,2}[-./]\w{3,}[-./]\d{4}\s*(?:to|-)\s*\d{1,2}[-./]\w{3,}[-./]\d{4})"
        )
        period_from, period_to, billing_frequency = self.parse_invoice_period(invoice_period)
        
        # Generate Ledger Name with new format (Oct-25 to Dec-25)
        ledger_name = self.generate_ledger_name(period_from, period_to)
        
        # Extract quantities from Particulars table
        # CloudXP PDF text format (note: description is on one line, data on next):
        # Delivered Segment Charges
        # 1 SMS Service 998599 98,81,102.00 0.090000 8,89,299.18  (OR "Bulk SMS" instead of "SMS Service")
        # Submitted Segment DLT
        # 2 SMS Service 998599 1,23,94,994.00 0.020000 2,47,899.88
        # Charges
        
        # Delivered Segment Charges - match across newlines (handles both "SMS Service" and "Bulk SMS")
        delivered_match = re.search(
            r"Delivered\s+Segment\s+Charges?\s*\n\s*\d+\s+(?:SMS\s+Service|Bulk\s+SMS)\s+(\d+)\s+([\d,]+\.?\d*)\s+([\d.]+)\s+([\d,]+\.?\d*)",
            text,
            re.IGNORECASE
        )
        
        delivered_qty = ""
        delivered_rate = ""
        if delivered_match:
            # Group 1 = HSN, Group 2 = Quantity, Group 3 = Rate, Group 4 = Value
            delivered_qty = delivered_match.group(2).replace(",", "").split(".")[0]
            delivered_rate = delivered_match.group(3)
        
        # Submitted Segment DLT Charges - match across newlines (handles both "SMS Service" and "Bulk SMS")
        submitted_match = re.search(
            r"Submitted\s+Segment\s+DLT\s*\n\s*\d+\s+(?:SMS\s+Service|Bulk\s+SMS)\s+(\d+)\s+([\d,]+\.?\d*)\s+([\d.]+)\s+([\d,]+\.?\d*)",
            text,
            re.IGNORECASE
        )
        
        submitted_qty = ""
        submitted_rate = ""
        dlt_qty = ""
        if submitted_match:
            # Group 1 = HSN, Group 2 = Quantity, Group 3 = Rate, Group 4 = Value
            submitted_qty = submitted_match.group(2).replace(",", "").split(".")[0]
            submitted_rate = submitted_match.group(3)
            dlt_qty = submitted_qty  # DLT qty is same as submitted
        
        # Extract Total Amount (before tax)
        amount = self.extract_field(
            text,
            r"Total\s*Amount\s*:?\s*([\d,]+\.?\d*)"
        )
        if not amount:
            amount = self.extract_field(
                text,
                r"Total\s*Amount\s+[\d,]+\.?\d*\s+([\d,]+\.?\d*)"
            )
        amount = self.clean_amount(amount)
        
        # Extract CGST from Tax Breakup
        cgst = self.extract_field(
            text,
            r"CGST\s*@?\s*\d+%?\s+([\d,]+\.?\d*)"
        )
        cgst = self.clean_amount(cgst)
        
        # Extract SGST from Tax Breakup
        sgst = self.extract_field(
            text,
            r"SGST\s*@?\s*\d+%?\s+([\d,]+\.?\d*)"
        )
        sgst = self.clean_amount(sgst)
        
        # Extract Grand Total (with tax)
        total_amount = self.extract_field(
            text,
            r"Grand\s*Total\s*\(?\s*Including\s*Tax\s*\)?\s*:?\s*([\d,]+\.?\d*)"
        )
        total_amount = self.clean_amount(total_amount)
        
        # Extract Remarks and clean up
        remarks = self.extract_field(
            text,
            r"[Rr]emarks?\s*:?\s*([^\n]+)"
        )
        if remarks:
            # Remove "Bulk SMS Service -" prefix if present
            remarks = re.sub(r'^Bulk\s*SMS\s*Service\s*[-:]\s*', '', remarks, flags=re.IGNORECASE)
            remarks = remarks.strip().upper()
        
        return {
            "invoice_no": invoice_no or "",
            "invoice_date": invoice_date,
            "gst_registration": gst_registration or "",
            "gst_state": gst_state,
            "party_customer": party_customer or "",
            "order_no": order_no or "",
            "order_date": order_date,
            "invoice_period_from": period_from,
            "invoice_period_to": period_to,
            "billing_frequency": billing_frequency,
            "tds_applicable": "Yes",
            "gst_tds_applicable": "No",
            "ledger_name": ledger_name,
            "submitted_qty": submitted_qty,
            "submitted_rate": submitted_rate,
            "dlt_qty": dlt_qty,
            "delivered_qty": delivered_qty,
            "delivered_rate": delivered_rate,
            "amount": amount,
            "cgst": cgst,
            "sgst": sgst,
            "total_amount": total_amount,
            "remarks": remarks or ""
        }
