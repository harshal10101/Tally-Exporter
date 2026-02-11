"""
Pydantic models for API request/response validation
"""

from pydantic import BaseModel
from typing import List, Optional


class InvoiceData(BaseModel):
    """Validated invoice data returned from parsing."""
    invoice_no: str = ""
    invoice_date: str = ""
    gst_registration: str = ""
    gst_state: str = ""
    party_customer: str = ""
    order_no: str = ""
    order_date: str = ""
    invoice_period_from: str = ""
    invoice_period_to: str = ""
    billing_frequency: str = ""
    tds_applicable: str = "Yes"
    gst_tds_applicable: str = "No"
    ledger_name: str = ""
    submitted_qty: str = ""
    submitted_rate: str = ""
    dlt_qty: str = ""
    delivered_qty: str = ""
    delivered_rate: str = ""
    amount: str = ""
    cgst: str = ""
    sgst: str = ""
    total_amount: str = ""
    remarks: str = ""
    invoice_type: str = ""
    filename: str = ""
    product: str = "SMS"


class ErrorDetail(BaseModel):
    """Details about a processing error."""
    filename: str
    error: str


class ProcessResponse(BaseModel):
    """Response from the /api/process endpoint."""
    success: bool
    processed: int
    errors: int
    data: List[InvoiceData]
    error_details: List[ErrorDetail]


class DebugResult(BaseModel):
    """Debug result for a single PDF."""
    filename: str
    invoice_type: Optional[str] = None
    raw_text: Optional[str] = None
    error: Optional[str] = None


class DebugResponse(BaseModel):
    """Response from the /api/debug endpoint."""
    results: List[DebugResult]


class HealthResponse(BaseModel):
    """Health check response."""
    status: str


class RootResponse(BaseModel):
    """Root endpoint response."""
    message: str
    status: str
