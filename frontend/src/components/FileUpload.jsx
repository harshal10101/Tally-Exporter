import { useCallback, useRef, useState } from 'react'

function FileUpload({ files, onFilesSelected, onRemoveFile, disabled }) {
    const [isDragOver, setIsDragOver] = useState(false)
    const fileInputRef = useRef(null)

    const handleDragOver = useCallback((e) => {
        e.preventDefault()
        e.stopPropagation()
        if (!disabled) {
            setIsDragOver(true)
        }
    }, [disabled])

    const handleDragLeave = useCallback((e) => {
        e.preventDefault()
        e.stopPropagation()
        setIsDragOver(false)
    }, [])

    const handleDrop = useCallback((e) => {
        e.preventDefault()
        e.stopPropagation()
        setIsDragOver(false)

        if (disabled) return

        const droppedFiles = Array.from(e.dataTransfer.files).filter(
            file => file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
        )

        if (droppedFiles.length > 0) {
            onFilesSelected(droppedFiles)
        }
    }, [disabled, onFilesSelected])

    const handleClick = useCallback(() => {
        if (!disabled) {
            fileInputRef.current?.click()
        }
    }, [disabled])

    const handleFileChange = useCallback((e) => {
        const selectedFiles = Array.from(e.target.files).filter(
            file => file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
        )

        if (selectedFiles.length > 0) {
            onFilesSelected(selectedFiles)
        }

        // Reset input so same file can be selected again
        e.target.value = ''
    }, [onFilesSelected])

    const formatFileSize = (bytes) => {
        if (bytes === 0) return '0 Bytes'
        const k = 1024
        const sizes = ['Bytes', 'KB', 'MB', 'GB']
        const i = Math.floor(Math.log(bytes) / Math.log(k))
        return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
    }

    return (
        <div>
            <div
                className={`upload-zone ${isDragOver ? 'drag-over' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={handleClick}
                style={{ opacity: disabled ? 0.6 : 1, pointerEvents: disabled ? 'none' : 'auto' }}
            >
                <input
                    ref={fileInputRef}
                    type="file"
                    accept=".pdf,application/pdf"
                    multiple
                    onChange={handleFileChange}
                    style={{ display: 'none' }}
                />

                <div className="upload-zone-content">
                    <div className="upload-icon">📁</div>
                    <h2>Upload Invoice PDFs</h2>
                    <p>Drag & drop your invoice files here, or click to browse</p>
                    <div className="upload-hint">
                        <span className="hint-badge">CloudXP Invoices</span>
                        <span className="hint-badge">RJIL Invoices</span>
                        <span className="hint-badge">JTL Invoices</span>
                    </div>
                </div>
            </div>

            {files.length > 0 && (
                <div className="file-list">
                    {files.map((file, index) => (
                        <div key={`${file.name}-${index}`} className="file-item">
                            <div className="file-info">
                                <div className="file-icon">PDF</div>
                                <div>
                                    <div className="file-name">{file.name}</div>
                                    <div className="file-size">{formatFileSize(file.size)}</div>
                                </div>
                            </div>
                            <button
                                className="file-remove"
                                onClick={(e) => {
                                    e.stopPropagation()
                                    onRemoveFile(index)
                                }}
                                title="Remove file"
                                disabled={disabled}
                            >
                                ✕
                            </button>
                        </div>
                    ))}
                </div>
            )}
        </div>
    )
}

export default FileUpload
