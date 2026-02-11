"""
Invoice Data Extraction Web Application - Backend
FastAPI application for extracting data from SMS service invoices
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import List
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
import tempfile
import os
import io

from models import InvoiceData, ErrorDetail, ProcessResponse, DebugResult, DebugResponse, HealthResponse, RootResponse
from logging_config import logger
from services.pdf_extractor import extract_text_from_pdf
from services.invoice_detector import detect_invoice_type
from services.excel_generator import generate_excel
from parsers.cloudxp_parser import CloudXPParser
from parsers.rjil_parser import RJILParser
from parsers.jtl_parser import JTLParser

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title="Invoice Data Extraction API",
    description="Extract data from CloudXP, RJIL, and JTL invoices for Tally import",
    version="1.1.0"
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Check if static folder exists (production build)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
HAS_STATIC = os.path.exists(STATIC_DIR) and os.path.isdir(STATIC_DIR)

# CORS: restrict origins in production, allow all in development
ALLOWED_ORIGINS = os.environ.get(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,http://localhost:3001,http://localhost:5173,http://127.0.0.1:3000,http://127.0.0.1:3001,http://127.0.0.1:5173"
).split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

# File validation constants
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB
PDF_MAGIC_BYTES = b"%PDF"

# Initialize parsers
parsers = {
    "cloudxp": CloudXPParser(),
    "rjil": RJILParser(),
    "jtl": JTLParser()
}


def validate_pdf(content: bytes, filename: str) -> None:
    """Validate that the uploaded file is a real PDF within size limits."""
    if len(content) > MAX_FILE_SIZE:
        raise ValueError(f"File exceeds maximum size of {MAX_FILE_SIZE // (1024 * 1024)}MB")
    if not content[:4].startswith(PDF_MAGIC_BYTES):
        raise ValueError("File is not a valid PDF (invalid magic bytes)")


@app.get("/", response_model=RootResponse)
async def root():
    return {"message": "Invoice Data Extraction API", "status": "running"}


@app.get("/health", response_model=HealthResponse)
async def health_check():
    return {"status": "healthy"}


@app.post("/api/process", response_model=ProcessResponse)
@limiter.limit("30/minute")
async def process_invoices(request: Request, files: List[UploadFile] = File(...)):
    """
    Process uploaded PDF invoices and return extracted data.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    logger.info("Processing %d file(s)", len(files))
    results = []
    errors = []

    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            logger.warning("Skipped non-PDF file: %s", file.filename)
            errors.append({"filename": file.filename, "error": "Not a PDF file"})
            continue

        try:
            content = await file.read()

            # Validate file content
            try:
                validate_pdf(content, file.filename)
            except ValueError as ve:
                logger.warning("Validation failed for %s: %s", file.filename, str(ve))
                errors.append({"filename": file.filename, "error": str(ve)})
                continue

            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            try:
                # Extract text from PDF
                text = extract_text_from_pdf(tmp_path)

                if not text.strip():
                    logger.warning("No text extracted from %s", file.filename)
                    errors.append({
                        "filename": file.filename,
                        "error": "Could not extract text from PDF"
                    })
                    continue

                # Detect invoice type
                invoice_type = detect_invoice_type(text)

                if invoice_type == "unknown":
                    logger.warning("Unknown invoice type for %s", file.filename)
                    errors.append({
                        "filename": file.filename,
                        "error": "Could not detect invoice type. Supported: CloudXP, RJIL, JTL"
                    })
                    continue

                # Parse invoice
                parser = parsers[invoice_type]
                data = parser.parse(text, file.filename)
                data["invoice_type"] = invoice_type
                data["filename"] = file.filename

                logger.info("Parsed %s as %s (Invoice: %s)", file.filename, invoice_type, data.get("invoice_no", "N/A"))
                results.append(data)

            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            logger.error("Error processing %s: %s", file.filename, str(e))
            errors.append({
                "filename": file.filename,
                "error": str(e)
            })

    logger.info("Processing complete: %d success, %d errors", len(results), len(errors))
    return {
        "success": True,
        "processed": len(results),
        "errors": len(errors),
        "data": results,
        "error_details": errors
    }


@app.post("/api/export")
@limiter.limit("20/minute")
async def export_to_excel(request: Request, files: List[UploadFile] = File(...)):
    """
    Process uploaded PDF invoices and return Excel file for Tally import.
    """
    # First process all invoices
    process_result = await process_invoices(request, files)

    if not process_result["data"]:
        raise HTTPException(
            status_code=400,
            detail="No invoices could be processed. " +
                   str(process_result.get("error_details", []))
        )

    # Generate Excel file
    logger.info("Generating Excel with %d invoices", len(process_result["data"]))
    excel_buffer = generate_excel(process_result["data"])

    # Return as downloadable file
    return StreamingResponse(
        io.BytesIO(excel_buffer.getvalue()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=tally_import.xlsx"
        }
    )


@app.post("/api/export-csv")
@limiter.limit("20/minute")
async def export_to_csv(request: Request, files: List[UploadFile] = File(...)):
    """
    Process uploaded PDF invoices and return CSV file.
    """
    from services.csv_generator import generate_csv

    process_result = await process_invoices(request, files)

    if not process_result["data"]:
        raise HTTPException(
            status_code=400,
            detail="No invoices could be processed. " +
                   str(process_result.get("error_details", []))
        )

    logger.info("Generating CSV with %d invoices", len(process_result["data"]))
    csv_buffer = generate_csv(process_result["data"])

    return StreamingResponse(
        io.BytesIO(csv_buffer.getvalue()),
        media_type="text/csv",
        headers={
            "Content-Disposition": "attachment; filename=tally_import.csv"
        }
    )


@app.post("/api/debug", response_model=DebugResponse)
async def debug_pdf(files: List[UploadFile] = File(...)):
    """
    Debug endpoint: Extract and return raw text from PDF.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")

    results = []

    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            continue

        try:
            content = await file.read()

            try:
                validate_pdf(content, file.filename)
            except ValueError as ve:
                results.append({"filename": file.filename, "error": str(ve)})
                continue

            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                tmp.write(content)
                tmp_path = tmp.name

            try:
                text = extract_text_from_pdf(tmp_path)
                invoice_type = detect_invoice_type(text)
                results.append({
                    "filename": file.filename,
                    "invoice_type": invoice_type,
                    "raw_text": text
                })
            finally:
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)

        except Exception as e:
            results.append({
                "filename": file.filename,
                "error": str(e)
            })

    return {"results": results}


# Mount static files and serve frontend in production
if HAS_STATIC:
    # Mount static assets (js, css, etc.)
    app.mount("/assets", StaticFiles(directory=os.path.join(STATIC_DIR, "assets")), name="assets")

    # Serve index.html for the root path
    @app.get("/", response_class=HTMLResponse)
    async def serve_frontend():
        index_path = os.path.join(STATIC_DIR, "index.html")
        if os.path.exists(index_path):
            with open(index_path, "r") as f:
                return HTMLResponse(content=f.read())
        return HTMLResponse(content="Frontend not found", status_code=404)

    # Catch-all for SPA routing (except /api paths)
    @app.get("/{path:path}")
    async def catch_all(path: str):
        # Skip API routes
        if path.startswith("api/") or path == "health" or path == "docs" or path == "openapi.json":
            return {"error": "Not found"}

        # Try to serve static file first
        static_file = os.path.join(STATIC_DIR, path)
        if os.path.exists(static_file) and os.path.isfile(static_file):
            return FileResponse(static_file)

        # Fall back to index.html for SPA routing
        index_path = os.path.join(STATIC_DIR, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)

        return {"error": "Not found"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
