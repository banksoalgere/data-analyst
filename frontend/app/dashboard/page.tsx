'use client'

import { useState } from "react"
import { CSVUploader } from "@/components/CSVUploader"
import { DataPreview } from "@/components/DataPreview"
import { DataChatInterface } from "@/components/DataChatInterface"

interface UploadResult {
  session_id: string
  schema: Array<{ column_name: string; column_type: string }>
  preview: Array<Record<string, unknown>>
  row_count: number
  profile?: {
    row_count: number
    column_count: number
    numeric_columns: string[]
    temporal_columns: string[]
    categorical_columns: string[]
    top_correlations: Array<{ column_x: string; column_y: string; correlation: number }>
    recommended_questions: string[]
  }
}

export default function DashboardPage() {
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null)

  return (
    <div className="min-h-screen bg-black text-white">
      {/* Header */}
      <div className="bg-neutral-900/50 border-b border-neutral-800 px-6 py-4 backdrop-blur-sm">
        <h1 className="text-2xl font-bold">Data Analytics Dashboard</h1>
        <p className="text-sm text-neutral-400 mt-1">
          Upload your CSV and ask questions in natural language
        </p>
      </div>

      <div className="container mx-auto px-6 py-8">
        {!uploadResult ? (
          /* Upload Section */
          <div className="max-w-3xl mx-auto">
            <div className="mb-6">
              <h2 className="text-xl font-semibold mb-2">Upload Your Data</h2>
              <p className="text-neutral-400 text-sm">
                Start by uploading a CSV file to analyze
              </p>
            </div>
            <CSVUploader onUploadSuccess={setUploadResult} />
          </div>
        ) : (
          /* Analysis Section */
          <div className="grid grid-cols-1 gap-6">
            {/* Data Preview */}
            <div>
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-xl font-semibold">Your Data</h2>
                <button
                  onClick={() => setUploadResult(null)}
                  className="text-sm text-neutral-400 hover:text-white transition-colors px-3 py-1 border border-neutral-800 rounded hover:border-neutral-700"
                >
                  Upload New File
                </button>
              </div>
              <DataPreview
                schema={uploadResult.schema}
                preview={uploadResult.preview}
                rowCount={uploadResult.row_count}
                profile={uploadResult.profile}
              />
            </div>

            {/* Chat Interface */}
            <div>
              <h2 className="text-xl font-semibold mb-4">Ask Questions</h2>
              <div className="h-[600px]">
                <DataChatInterface
                  sessionId={uploadResult.session_id}
                  profile={uploadResult.profile}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
