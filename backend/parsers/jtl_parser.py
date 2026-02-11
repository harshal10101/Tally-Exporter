"""
JTL Invoice Parser
Parses Jio Things Limited invoices with "TAX INVOICE" header (no branding)
"""

import re
from typing import Dict
from .base_parser import BaseParser


class JTLParser(BaseParser):
    """Parser for JTL (Jio Things Limited) format invoices."""
    
    def parse(self, text: str, filename: str) -> Dict:
        """
        Parse JTL invoice and extract all required fields.
        
        Args:
            text: Extracted text from PDF
            filename: Original filename for reference
            
        Returns:
            Dictionary with all 21 Tally fields + remarks
        """
        # Extract Invoice Number
        invoice_no = self.extract_field(
            text,
            r"Invoice\s*No\.?\s*:?\s*([A-Z0-9]+)"
        )
        
        # Extract Invoice Date
        invoice_date_raw = self.extract_field(
            text,
            r"Date\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{4})"
        )
        invoice_date = self.format_date(invoice_date_raw) if invoice_date_raw else ""
        
        # Extract GSTIN (Supplier's)
        gst_registration = self.extract_field(
            text,
            r"GSTIN\s+([A-Z0-9]{15})"
        )
        
        # Extract GST State from GST number
        gst_state = self.get_state_from_gst(gst_registration)
        
        # Extract Recipient (Party/Customer) - Fixed pattern
        # JTL format has:
        # Recipient No    8140817
        # Recipient       BHARATIYA JANATA PARTY
        # So we need to match "Recipient" NOT followed by "No"
        party_customer = None
        
        # Look for "Recipient" followed by name (not "Recipient No")
        # Pattern: "Recipient" followed by whitespace and the company name
        recipient_match = re.search(
            r"Recipient\s+(?!No)([A-Z][A-Z0-9\s&\-\.]+?)(?:\s+Date|\s+\d{1,2}[./]|\s+Invoice|\s*\n|\s+6-A|$)",
            text,
            re.IGNORECASE | re.MULTILINE
        )
        if recipient_match:
            party_customer = recipient_match.group(1).strip()
        
        # Alternative: Parse line by line
        if not party_customer:
            lines = text.split('\n')
            for line in lines:
                # Match line that starts with "Recipient" but NOT "Recipient No"
                if re.match(r'^\s*Recipient\s+(?!No)', line, re.IGNORECASE):
                    # Extract the name part
                    match = re.search(r'Recipient\s+([A-Z][A-Z0-9\s&\-\.]+)', line, re.IGNORECASE)
                    if match:
                        party_customer = match.group(1).strip()
                        # Clean up - remove trailing address parts
                        if ',' in party_customer:
                            party_customer = party_customer.split(',')[0].strip()
                        break
        
        # Extract ORN (Order Reference Number) - JTL's PO equivalent
        order_no = self.extract_field(
            text,
            r"ORN\s*:?\s*(\d+)"
        )
        
        # JTL invoices don't have Order Date
        order_date = ""
        
        # Extract Invoice Period
        invoice_period = self.extract_field(
            text,
            r"Invoice\s*Period\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{4}\s*[-–]\s*\d{1,2}[./]\d{1,2}[./]\d{4})"
        )
        period_from, period_to, billing_frequency = self.parse_invoice_period(invoice_period)
        
        # Generate Ledger Name with new format
        ledger_name = self.generate_ledger_name(period_from, period_to)
        
        # Extract SMS # SCRUBBING/ DLT COUNT (Submitted Qty)
        dlt_match = re.search(
            r"(?:SMS\s*#?\s*SCRUBBING|DLT\s*COUNT)\s+(\d+)\s+([\d,]+\.?\d*)\s+([\d.]+)\s+([\d,]+\.?\d*)",
            text,
            re.IGNORECASE
        )
        
        submitted_qty = ""
        dlt_qty = ""
        
        if dlt_match:
            submitted_qty = dlt_match.group(2).replace(",", "").split(".")[0]
            dlt_qty = submitted_qty
        
        # Extract BSS SERVICE CHARGE (Delivered Qty)
        bss_match = re.search(
            r"BSS\s*SERVICE\s*CHARGE\s+(\d+)\s+([\d,]+\.?\d*)\s+([\d.]+)\s+([\d,]+\.?\d*)",
            text,
            re.IGNORECASE
        )
        
        delivered_qty = ""
        if bss_match:
            delivered_qty = bss_match.group(2).replace(",", "").split(".")[0]
        
        # Extract Total Taxable Value (Amount before tax)
        amount = self.extract_field(
            text,
            r"Total\s*Taxable\s*value\s*([\d,]+\.?\d*)"
        )
        amount = self.clean_amount(amount)
        
        # Extract CGST
        cgst = self.extract_field(
            text,
            r"CGST\s*@?\s*\d+\s*%?\s*([\d,]+\.?\d*)"
        )
        cgst = self.clean_amount(cgst)
        
        # Extract SGST
        sgst = self.extract_field(
            text,
            r"SGST\s*@?\s*\d+\s*%?\s*([\d,]+\.?\d*)"
        )
        sgst = self.clean_amount(sgst)
        
        # Extract Total (Value is inclusive of Tax)
        total_amount = self.extract_field(
            text,
            r"Total\s*\(\s*Value\s*is\s*inclusive\s*of\s*Tax\s*\)\s*([\d,]+\.?\d*)"
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
            "order_date": order_date,  # Blank for JTL
            "invoice_period_from": period_from,
            "invoice_period_to": period_to,
            "billing_frequency": billing_frequency,
            "tds_applicable": "Yes",
            "gst_tds_applicable": "No",
            "ledger_name": ledger_name,
            "submitted_qty": submitted_qty,
            "submitted_rate": "",
            "dlt_qty": dlt_qty,
            "delivered_qty": delivered_qty,
            "delivered_rate": "",
            "amount": amount,
            "cgst": cgst,
            "sgst": sgst,
            "total_amount": total_amount,
            "remarks": remarks or ""
        }
