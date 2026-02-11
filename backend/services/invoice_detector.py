"""
Invoice Type Detection Service
Identifies whether an invoice is CloudXP, RJIL, or JTL based on header patterns
"""

import re
import logging

logger = logging.getLogger("invoice_extractor")


def detect_invoice_type(text: str) -> str:
    """
    Detect the type of invoice based on text content.

    Args:
        text: Extracted text from PDF

    Returns:
        Invoice type: 'cloudxp', 'rjil', 'jtl', or 'unknown'
    """
    text_upper = text.upper()

    # Check for CloudXP format (Jio logo + TAX INVOICE (ORIGINAL))
    # CloudXP invoices have "TAX INVOICE (ORIGINAL)" near the top
    # and specific fields like "Account Number:", "Invoice Number:"
    if "TAX INVOICE (ORIGINAL)" in text_upper and "ACCOUNT NUMBER" in text_upper:
        return "cloudxp"

    # Check for RJIL format
    # Has "Reliance Jio Infocomm Limited" and "ORIGINAL FOR RECIPIENT"
    if "RELIANCE JIO INFOCOMM LIMITED" in text_upper and "ORIGINAL FOR RECIPIENT" in text_upper:
        return "rjil"

    # Check for JTL format
    # Has "Jio Things Limited" without the above markers
    if "JIO THINGS LIMITED" in text_upper:
        return "jtl"

    # Return unknown instead of silently defaulting
    logger.warning("Could not detect invoice type from text content")
    return "unknown"
