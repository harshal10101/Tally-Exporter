function DownloadButton({ onDownloadExcel, onDownloadCsv, disabled }) {
    return (
        <div className="download-buttons">
            <button
                className="btn btn-success"
                onClick={onDownloadExcel}
                disabled={disabled}
            >
                <span>📥</span>
                <span>Download Excel</span>
            </button>
            <button
                className="btn btn-secondary"
                onClick={onDownloadCsv}
                disabled={disabled}
            >
                <span>📄</span>
                <span>Download CSV</span>
            </button>
        </div>
    )
}

export default DownloadButton
