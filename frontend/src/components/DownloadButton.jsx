function DownloadButton({ onClick, disabled }) {
    return (
        <button
            className="btn btn-success"
            onClick={onClick}
            disabled={disabled}
        >
            <span>📥</span>
            <span>Download Excel for Tally</span>
        </button>
    )
}

export default DownloadButton
