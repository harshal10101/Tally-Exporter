# Invoice Data Extractor for Tally

A web-based application to extract invoice data from CloudXP, RJIL, and JTL invoices and export to Excel for Tally import.

## 🚀 Quick Start with Docker

### Prerequisites
- Docker Desktop installed and running

### Deploy in One Command

```bash
cd Tally-Export
docker-compose up --build -d
```

### Access the Application
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000

### Stop the Application

```bash
docker-compose down
```

---

## 📋 Supported Invoice Types

| Type | Identifier | Coverage |
|------|------------|----------|
| **CloudXP** | Jio logo + "TAX INVOICE (ORIGINAL)" | 95% of invoices |
| **RJIL** | "Reliance Jio Infocomm Limited" | BULK SMS format |
| **JTL** | "Jio Things Limited" | DLT + BSS charges |

---

## 📊 Excel Export Format (24 Columns)

1. Sr. No.
2. Invoice Type (CloudXP / JTL / RJIL)
3. Product (default: SMS)
4. Invoice No
5. Invoice Date
6. GST Registration
7. GST State
8. Party/Customer
9. Order No
10. Order Date
11. Invoice Period From
12. Invoice Period To
13. Billing Frequency (auto-detected)
14. TDS Applicable (default: Yes)
15. GST TDS Applicable (default: No)
16. Ledger Name (format: "Bulk SMS Charges - *period*")
17. Submitted Qty
18. Submitted Rate
19. Delivered Qty
20. Delivered Rate
21. Amount
22. CGST
23. SGST
24. Total Amount (with Tax)

---

## 🔧 Development Setup

### Backend (Python)

```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend (React)

```bash
cd frontend
npm install
npm run dev
```

---

## 📁 Project Structure

```
Tally-Export/
├── docker-compose.yml
├── README.md
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   ├── services/
│   │   ├── pdf_extractor.py
│   │   ├── invoice_detector.py
│   │   └── excel_generator.py
│   └── parsers/
│       ├── base_parser.py
│       ├── cloudxp_parser.py
│       ├── rjil_parser.py
│       └── jtl_parser.py
└── frontend/
    ├── Dockerfile
    ├── nginx.conf
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── main.jsx
        ├── index.css
        ├── App.jsx
        └── components/
            ├── FileUpload.jsx
            ├── ResultsTable.jsx
            └── DownloadButton.jsx
```

---

## 🎯 Usage

1. Open http://localhost:3000 in your browser
2. Drag & drop PDF invoices or click to browse
3. Click "Extract Data" to process invoices
4. Review the extracted data in the table
5. Click "Download Excel for Tally" to get the import file

---

## 👨‍💻 Author

Created by **Harshal S. Badgujar**
