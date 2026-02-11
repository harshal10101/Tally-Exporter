function ResultsTable({ data }) {
    if (!data || data.length === 0) {
        return null
    }

    // Define columns to display (matching 24-column Excel format)
    const columns = [
        { key: 'invoice_type', label: 'Invoice Type' },
        { key: 'product', label: 'Product' },
        { key: 'invoice_no', label: 'Invoice No' },
        { key: 'invoice_date', label: 'Date' },
        { key: 'party_customer', label: 'Party/Customer' },
        { key: 'gst_state', label: 'State' },
        { key: 'invoice_period_from', label: 'Period From' },
        { key: 'invoice_period_to', label: 'Period To' },
        { key: 'billing_frequency', label: 'Frequency' },
        { key: 'submitted_qty', label: 'Submitted Qty' },
        { key: 'submitted_rate', label: 'Submitted Rate' },
        { key: 'delivered_qty', label: 'Delivered Qty' },
        { key: 'delivered_rate', label: 'Delivered Rate' },
        { key: 'amount', label: 'Amount' },
        { key: 'cgst', label: 'CGST' },
        { key: 'sgst', label: 'SGST' },
        { key: 'total_amount', label: 'Total' }
    ]

    const formatValue = (value, key) => {
        // Product column defaults to "SMS"
        if (key === 'product') {
            return value || 'SMS'
        }

        if (value === null || value === undefined || value === '') {
            return '-'
        }

        // Format amounts with commas (Indian format)
        if (['amount', 'cgst', 'sgst', 'total_amount'].includes(key)) {
            const num = parseFloat(value)
            if (!isNaN(num)) {
                return '₹ ' + num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
            }
        }

        // Format quantities with commas
        if (['submitted_qty', 'delivered_qty', 'dlt_qty'].includes(key)) {
            const num = parseFloat(value)
            if (!isNaN(num)) {
                return num.toLocaleString('en-IN')
            }
        }

        // Format rate values (show as-is with full precision)
        if (['submitted_rate', 'delivered_rate'].includes(key)) {
            return value
        }

        return String(value)
    }

    const getTypeBadgeClass = (type) => {
        const typeMap = {
            'cloudxp': 'cloudxp',
            'rjil': 'rjil',
            'jtl': 'jtl'
        }
        return typeMap[type?.toLowerCase()] || 'cloudxp'
    }

    return (
        <div className="table-wrapper">
            <div className="table-scroll">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th>#</th>
                            {columns.map(col => (
                                <th key={col.key}>{col.label}</th>
                            ))}
                        </tr>
                    </thead>
                    <tbody>
                        {data.map((row, index) => (
                            <tr key={index}>
                                <td>{index + 1}</td>
                                {columns.map(col => (
                                    <td key={col.key}>
                                        {col.key === 'invoice_type' ? (
                                            <span className={`type-badge ${getTypeBadgeClass(row[col.key])}`}>
                                                {row[col.key]?.toUpperCase() || 'N/A'}
                                            </span>
                                        ) : (
                                            formatValue(row[col.key], col.key)
                                        )}
                                    </td>
                                ))}
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}

export default ResultsTable
