"""
Invoice Data Extraction Web Application - Backend
FastAPI application for extracting data from SMS service invoices
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from typing import List
import tempfile
import os
import io

from services.pdf_extractor import extract_text_from_pdf
from services.invoice_detector import detect_invoice_type
from services.excel_generator import generate_excel
from parsers.cloudxp_parser import CloudXPParser
from parsers.rjil_parser import RJILParser
from parsers.jtl_parser import JTLParser

app = FastAPI(
    title="Invoice Data Extraction API",
    description="Extract data from CloudXP, RJIL, and JTL invoices for Tally import",
    version="1.0.0"
)

# Check if static folder exists (production build)
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
HAS_STATIC = os.path.exists(STATIC_DIR) and os.path.isdir(STATIC_DIR)

# Configure CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize parsers
parsers = {
    "cloudxp": CloudXPParser(),
    "rjil": RJILParser(),
    "jtl": JTLParser()
}


@app.get("/")
async def root():
    return {"message": "Invoice Data Extraction API", "status": "running"}


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.post("/api/process")
async def process_invoices(files: List[UploadFile] = File(...)):
    """
    Process uploaded PDF invoices and return extracted data.
    """
    if not files:
        raise HTTPException(status_code=400, detail="No files uploaded")
    
    results = []
    errors = []
    
    for file in files:
        if not file.filename.lower().endswith('.pdf'):
            errors.append({
                "filename": file.filename,
                "error": "Not a PDF file"
            })
            continue
        
        try:
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                content = await file.read()
                tmp.write(content)
                tmp_path = tmp.name
            
            try:
                # Extract text from PDF
                text = extract_text_from_pdf(tmp_path)
                
                if not text.strip():
                    errors.append({
                        "filename": file.filename,
                        "error": "Could not extract text from PDF"
                    })
                    continue
                
                # Detect invoice type
                invoice_type = detect_invoice_type(text)
                
                if invoice_type not in parsers:
                    errors.append({
                        "filename": file.filename,
                        "error": f"Unknown invoice type: {invoice_type}"
                    })
                    continue
                
                # Parse invoice
                parser = parsers[invoice_type]
                data = parser.parse(text, file.filename)
                data["invoice_type"] = invoice_type
                data["filename"] = file.filename
                
                results.append(data)
                
            finally:
                # Clean up temp file
                if os.path.exists(tmp_path):
                    os.unlink(tmp_path)
                    
        except Exception as e:
            errors.append({
                "filename": file.filename,
                "error": str(e)
            })
    
    return {
        "success": True,
        "processed": len(results),
        "errors": len(errors),
        "data": results,
        "error_details": errors
    }


@app.post("/api/export")
async def export_to_excel(files: List[UploadFile] = File(...)):
    """
    Process uploaded PDF invoices and return Excel file for Tally import.
    """
    # First process all invoices
    process_result = await process_invoices(files)
    
    if not process_result["data"]:
        raise HTTPException(
            status_code=400, 
            detail="No invoices could be processed. " + 
                   str(process_result.get("error_details", []))
        )
    
    # Generate Excel file
    excel_buffer = generate_excel(process_result["data"])
    
    # Return as downloadable file
    return StreamingResponse(
        io.BytesIO(excel_buffer.getvalue()),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": "attachment; filename=tally_import.xlsx"
        }
    )


@app.post("/api/debug")
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
            with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp:
                content = await file.read()
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
