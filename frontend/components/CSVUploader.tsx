'use client'

import { useCallback, useState } from 'react'
import { useDropzone } from 'react-dropzone'

interface UploadResult {
  session_id: string
  schema: Array<{ column_name: string; column_type: string }>
  preview: Array<Record<string, any>>
  row_count: number
}

interface CSVUploaderProps {
  onUploadSuccess: (result: UploadResult) => void
}

export function CSVUploader({ onUploadSuccess }: CSVUploaderProps) {
  const [uploading, setUploading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const onDrop = useCallback(async (acceptedFiles: File[]) => {
    const file = acceptedFiles[0]
    if (!file) return

    setUploading(true)
    setError(null)

    try {
      const formData = new FormData()
      formData.append('file', file)

      const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Upload failed')
      }

      const result: UploadResult = await response.json()
      onUploadSuccess(result)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Upload failed')
    } finally {
      setUploading(false)
    }
  }, [onUploadSuccess])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/csv': ['.csv'],
      'application/vnd.ms-excel': ['.csv'],
    },
    maxFiles: 1,
    disabled: uploading,
  })

  return (
    <div className="w-full">
      <div
        {...getRootProps()}
        className={`
          border-2 border-dashed rounded-lg p-8 text-center cursor-pointer
          transition-colors duration-200
          ${isDragActive
            ? 'border-white bg-neutral-800'
            : 'border-neutral-700 hover:border-neutral-600 bg-neutral-900'
          }
          ${uploading ? 'opacity-50 cursor-not-allowed' : ''}
        `}
      >
        <input {...getInputProps()} />

        <div className="flex flex-col items-center gap-3">
          {uploading ? (
            <>
              <div className="w-12 h-12 border-4 border-neutral-700 border-t-white rounded-full animate-spin" />
              <p className="text-white font-medium">Uploading...</p>
            </>
          ) : (
            <>
              <svg
                className="w-12 h-12 text-neutral-400"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>

              {isDragActive ? (
                <p className="text-white font-medium">Drop your CSV file here</p>
              ) : (
                <>
                  <p className="text-white font-medium">
                    Drag and drop a CSV file here
                  </p>
                  <p className="text-neutral-400 text-sm">or click to browse</p>
                </>
              )}

              <p className="text-neutral-500 text-xs mt-2">
                Supported format: CSV files only
              </p>
            </>
          )}
        </div>
      </div>

      {error && (
        <div className="mt-3 bg-red-950/50 border border-red-900 text-red-400 px-4 py-3 rounded-lg text-sm">
          {error}
        </div>
      )}
    </div>
  )
}
