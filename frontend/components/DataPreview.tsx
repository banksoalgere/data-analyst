'use client'

interface DataPreviewProps {
  schema: Array<{ column_name: string; column_type: string }>
  preview: Array<Record<string, any>>
  rowCount: number
}

export function DataPreview({ schema, preview, rowCount }: DataPreviewProps) {
  return (
    <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-6">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-white mb-1">
          Data Preview
        </h3>
        <p className="text-sm text-neutral-400">
          {rowCount.toLocaleString()} rows • {schema.length} columns
        </p>
      </div>

      {/* Schema */}
      <div className="mb-6">
        <h4 className="text-sm font-medium text-neutral-300 mb-3">
          Columns
        </h4>
        <div className="flex flex-wrap gap-2">
          {schema.map((col, idx) => (
            <div
              key={idx}
              className="inline-flex items-center gap-2 bg-neutral-800 border border-neutral-700 px-3 py-1.5 rounded text-xs"
            >
              <span className="text-white font-medium">
                {col.column_name}
              </span>
              <span className="text-neutral-400">
                {col.column_type}
              </span>
            </div>
          ))}
        </div>
      </div>

      {/* Preview Table */}
      <div className="overflow-x-auto">
        <h4 className="text-sm font-medium text-neutral-300 mb-3">
          First 5 rows
        </h4>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-neutral-800">
              {schema.map((col, idx) => (
                <th
                  key={idx}
                  className="text-left px-3 py-2 text-neutral-400 font-medium"
                >
                  {col.column_name}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {preview.map((row, rowIdx) => (
              <tr
                key={rowIdx}
                className="border-b border-neutral-800 hover:bg-neutral-800/50 transition-colors"
              >
                {schema.map((col, colIdx) => (
                  <td
                    key={colIdx}
                    className="px-3 py-2 text-neutral-300"
                  >
                    {row[col.column_name] !== null && row[col.column_name] !== undefined
                      ? String(row[col.column_name])
                      : <span className="text-neutral-600">null</span>
                    }
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
