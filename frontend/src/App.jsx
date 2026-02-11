import { useState, useCallback } from 'react'
import FileUpload from './components/FileUpload'
import ResultsTable from './components/ResultsTable'
import DownloadButton from './components/DownloadButton'

// API base URL - use relative for production (proxied), absolute for development
const API_BASE = import.meta.env.PROD ? '' : 'http://localhost:8000'

function App() {
    const [files, setFiles] = useState([])
    const [results, setResults] = useState(null)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [processedFiles, setProcessedFiles] = useState([])

    const handleFilesSelected = useCallback((newFiles) => {
        setFiles(prev => [...prev, ...newFiles])
        setError(null)
    }, [])

    const handleRemoveFile = useCallback((index) => {
        setFiles(prev => prev.filter((_, i) => i !== index))
    }, [])

    const handleClearAll = useCallback(() => {
        setFiles([])
        setResults(null)
        setError(null)
        setProcessedFiles([])
    }, [])

    const handleProcess = async () => {
        if (files.length === 0) {
            setError('Please select at least one PDF file')
            return
        }

        setLoading(true)
        setError(null)

        try {
            const formData = new FormData()
            files.forEach(file => {
                formData.append('files', file)
            })

            const response = await fetch(`${API_BASE}/api/process`, {
                method: 'POST',
                body: formData
            })

            if (!response.ok) {
                throw new Error(`Processing failed: ${response.statusText}`)
            }

            const data = await response.json()

            if (data.errors > 0 && data.processed === 0) {
                throw new Error(data.error_details.map(e => `${e.filename}: ${e.error}`).join(', '))
            }

            setResults(data)
            setProcessedFiles(files.map(f => f.name))
        } catch (err) {
            setError(err.message || 'An error occurred while processing invoices')
            setResults(null)
        } finally {
            setLoading(false)
        }
    }

    const downloadFile = async (endpoint, filename) => {
        if (files.length === 0) {
            setError('No files to export')
            return
        }

        setLoading(true)
        setError(null)

        try {
            const formData = new FormData()
            files.forEach(file => {
                formData.append('files', file)
            })

            const response = await fetch(`${API_BASE}${endpoint}`, {
                method: 'POST',
                body: formData
            })

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}))
                throw new Error(errorData.detail || `Export failed: ${response.statusText}`)
            }

            const blob = await response.blob()
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = filename
            document.body.appendChild(a)
            a.click()
            window.URL.revokeObjectURL(url)
            document.body.removeChild(a)
        } catch (err) {
            setError(err.message || 'An error occurred while exporting')
        } finally {
            setLoading(false)
        }
    }

    const handleDownloadExcel = () => {
        const date = new Date().toISOString().split('T')[0]
        downloadFile('/api/export', `tally_import_${date}.xlsx`)
    }

    const handleDownloadCsv = () => {
        const date = new Date().toISOString().split('T')[0]
        downloadFile('/api/export-csv', `tally_import_${date}.csv`)
    }

    return (
        <div className="app">
            <header className="header">
                <div className="container header-content">
                    <div className="logo">
                        <div className="logo-icon">📄</div>
                        <div className="logo-text">
                            <h1>Invoice Data Extractor</h1>
                            <p>CloudXP • RJIL • JTL → Tally Export</p>
                        </div>
                    </div>
                    <span className="header-badge">v1.1</span>
                </div>
            </header>

            <main className="main">
                <div className="container">
                    {/* Upload Section */}
                    <section className="upload-section">
                        <FileUpload
                            files={files}
                            onFilesSelected={handleFilesSelected}
                            onRemoveFile={handleRemoveFile}
                            disabled={loading}
                        />

                        {files.length > 0 && (
                            <div className="action-buttons">
                                <button
                                    className="btn btn-primary"
                                    onClick={handleProcess}
                                    disabled={loading}
                                >
                                    {loading ? '⏳ Processing...' : '🔍 Extract Data'}
                                </button>
                                <button
                                    className="btn btn-secondary"
                                    onClick={handleClearAll}
                                    disabled={loading}
                                >
                                    🗑️ Clear All
                                </button>
                            </div>
                        )}
                    </section>

                    {/* Error Message */}
                    {error && (
                        <div className="error-message">
                            <span>⚠️</span>
                            <span>{error}</span>
                        </div>
                    )}

                    {/* Loading State */}
                    {loading && (
                        <div className="status-message loading">
                            <div className="spinner"></div>
                            <p>Processing invoices...</p>
                        </div>
                    )}

                    {/* Results Section */}
                    {results && results.data && results.data.length > 0 && (
                        <section className="results-section">
                            <div className="section-header">
                                <div className="section-title">
                                    <h2>📊 Extracted Data</h2>
                                    <span className="count-badge">
                                        {results.processed} invoice{results.processed !== 1 ? 's' : ''}
                                    </span>
                                </div>
                                <DownloadButton
                                    onDownloadExcel={handleDownloadExcel}
                                    onDownloadCsv={handleDownloadCsv}
                                    disabled={loading}
                                />
                            </div>

                            {results.errors > 0 && (
                                <div className="error-message" style={{ marginBottom: '1rem' }}>
                                    <span>⚠️</span>
                                    <span>
                                        {results.errors} file(s) had errors: {' '}
                                        {results.error_details.map(e => e.filename).join(', ')}
                                    </span>
                                </div>
                            )}

                            <ResultsTable data={results.data} />
                        </section>
                    )}

                    {/* Success but no data */}
                    {results && results.data && results.data.length === 0 && (
                        <div className="success-message">
                            <span>ℹ️</span>
                            <span>No invoice data could be extracted. Please check if the PDFs are valid invoice files.</span>
                        </div>
                    )}
                </div>
            </main>

            <footer className="footer">
                <div className="container">
                    <p>
                        Invoice Data Extractor for Tally • Built by{' '}
                        <a href="#">Harshal S. Badgujar</a>
                    </p>
                </div>
            </footer>
        </div>
    )
}

export default App
