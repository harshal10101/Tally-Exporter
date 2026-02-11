"""
RJIL Invoice Parser
Parses Reliance Jio Infocomm Limited invoices with "ORIGINAL FOR RECIPIENT Tax Invoice" header
"""

import re
from typing import Dict
from .base_parser import BaseParser


class RJILParser(BaseParser):
    """Parser for RJIL format invoices."""
    
    def parse(self, text: str, filename: str) -> Dict:
        """
        Parse RJIL invoice and extract all required fields.
        
        Args:
            text: Extracted text from PDF
            filename: Original filename for reference
            
        Returns:
            Dictionary with all 21 Tally fields
        """
        # Extract Invoice Number
        invoice_no = self.extract_field(
            text,
            r"Invoice\s*no\.?\s*:?\s*(\d+)"
        )
        
        # Extract Invoice Date
        invoice_date_raw = self.extract_field(
            text,
            r"Invoice\s*date\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{4})"
        )
        invoice_date = self.format_date(invoice_date_raw) if invoice_date_raw else ""
        
        # Extract GSTIN (Supplier's GST)
        gst_registration = self.extract_field(
            text,
            r"GSTIN\s+([A-Z0-9]{15})"
        )
        
        # Extract GST State from GST number
        gst_state = self.get_state_from_gst(gst_registration)
        
        # Extract Recipient (Party/Customer)
        # RJIL format has: "Recipient NSE CLEARING LIMITED, C1 BLOCK G,..."
        # But header has: "ORIGINAL FOR RECIPIENT Tax Invoice" - must skip this!
        party_customer = None
        
        # Method: Parse line by line to find "Recipient" that is NOT part of header
        lines = text.split('\n')
        for line in lines:
            line_stripped = line.strip()
            # Skip header lines containing "FOR RECIPIENT" or "Tax Invoice"
            if "FOR RECIPIENT" in line_stripped.upper():
                continue
            if "TAX INVOICE" in line_stripped.upper() and "RECIPIENT" in line_stripped.upper():
                continue
            
            # Look for line starting with "Recipient" followed by company name
            if line_stripped.startswith("Recipient"):
                # Extract the text after "Recipient"
                match = re.search(r"Recipient\s+([A-Z][A-Z0-9\s]+)", line_stripped, re.IGNORECASE)
                if match:
                    name = match.group(1).strip()
                    # Skip if it's "Tax Invoice"
                    if name.upper() not in ["TAX INVOICE", "TAX", "INVOICE"]:
                        # Stop at comma if present
                        if ',' in name:
                            name = name.split(',')[0].strip()
                        party_customer = name
                        break
        
        # Fallback: Try to find company name ending with LIMITED/LTD
        if not party_customer:
            recipient_match = re.search(
                r"Recipient\s+([A-Z][A-Z0-9\s]+(?:LIMITED|LTD))",
                text,
                re.IGNORECASE
            )
            if recipient_match:
                name = recipient_match.group(1).strip()
                if name.upper() not in ["TAX INVOICE", "TAX", "INVOICE"]:
                    party_customer = name
        
        # Extract PO Number (format: "PO No. 2526NSCCLIT94" or "PO No . 2526NSCCLIT94")
        order_no = self.extract_field(
            text,
            r"PO\s*No\s*\.?\s*:?\s*([A-Z0-9]+)"
        )
        
        # Extract PO Date
        order_date_raw = self.extract_field(
            text,
            r"PO\s*Date\.?\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{4})"
        )
        order_date = self.format_date(order_date_raw) if order_date_raw else ""
        
        # Extract Invoice Period
        invoice_period = self.extract_field(
            text,
            r"Invoice\s*period\s*:?\s*(\d{1,2}[./]\d{1,2}[./]\d{4}\s*[-–]\s*\d{1,2}[./]\d{1,2}[./]\d{4})"
        )
        period_from, period_to, billing_frequency = self.parse_invoice_period(invoice_period)
        
        # Generate Ledger Name with new format
        ledger_name = self.generate_ledger_name(period_from, period_to)
        
        # Extract BULK SMS quantity (RJIL only has BULK SMS, no separate DLT/Submitted)
        bulk_sms_match = re.search(
            r"BULK\s*SMS\s+(\d+)\s+([\d,]+)\s+EA\s+([\d.]+)\s+([\d,]+\.?\d*)",
            text,
            re.IGNORECASE
        )
        
        delivered_qty = ""
        submitted_qty = ""
        dlt_qty = ""
        
        if bulk_sms_match:
            delivered_qty = bulk_sms_match.group(2).replace(",", "")
        
        # Extract Total Amount Excluding Taxes
        amount = self.extract_field(
            text,
            r"Total\s*Amount\s*Excluding\s*Taxes\s*([\d,]+\.?\d*)"
        )
        amount = self.clean_amount(amount)
        
        # Extract CGST from Tax Payable section
        cgst = self.extract_field(
            text,
            r"CGST\s+[\d.]+\s*%?\s*([\d,]+\.?\d*)"
        )
        cgst = self.clean_amount(cgst)
        
        # Extract SGST from Tax Payable section
        sgst = self.extract_field(
            text,
            r"SGST\s+[\d.]+\s*%?\s*([\d,]+\.?\d*)"
        )
        sgst = self.clean_amount(sgst)
        
        # Extract Grand Total (Including GST)
        total_amount = self.extract_field(
            text,
            r"Grand\s*Total\s*\(?\s*Including\s*GST\s*\)?\s*([\d,]+\.?\d*)"
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
