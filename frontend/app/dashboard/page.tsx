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

type DashboardStep = "upload" | "summary" | "chat"

export default function DashboardPage() {
  const [uploadResult, setUploadResult] = useState<UploadResult | null>(null)
  const [step, setStep] = useState<DashboardStep>("upload")
  const [prefilledQuestion, setPrefilledQuestion] = useState<string | null>(null)
  const [prefilledQuestionToken, setPrefilledQuestionToken] = useState(0)

  const handleUploadSuccess = (result: UploadResult) => {
    setUploadResult(result)
    setStep("summary")
  }

  const handleUploadReset = () => {
    setUploadResult(null)
    setStep("upload")
    setPrefilledQuestion(null)
    setPrefilledQuestionToken(0)
  }

  const handleSuggestedQuestionClick = (question: string) => {
    setPrefilledQuestion(question)
    setPrefilledQuestionToken((token) => token + 1)
    setStep("chat")
  }

  return (
    <div className="h-screen bg-black text-white flex flex-col">
      {/* Header */}
      <div className="bg-neutral-900/50 border-b border-neutral-800 px-6 py-4 backdrop-blur-sm">
        <h1 className="text-2xl font-bold">Data Analytics Dashboard</h1>
        <p className="text-sm text-neutral-400 mt-1">
          Upload once, review your summary, then move into full-screen chat.
        </p>
      </div>

      <main className="flex-1 min-h-0">
        {step === "upload" && (
          <section className="h-full flex items-center justify-center p-6">
            <div className="max-w-3xl w-full">
              <div className="mb-6">
                <h2 className="text-xl font-semibold mb-2">Upload Your Data</h2>
                <p className="text-neutral-400 text-sm">
                  Start by uploading a CSV file to analyze
                </p>
              </div>
              <CSVUploader onUploadSuccess={handleUploadSuccess} />
            </div>
          </section>
        )}

        {step === "summary" && uploadResult && (
          <section className="h-full overflow-y-auto p-6 md:p-8">
            <div className="mx-auto w-full max-w-6xl space-y-6">
              <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                <div>
                  <h2 className="text-2xl font-semibold">Dataset Summary</h2>
                  <p className="text-sm text-neutral-400 mt-1">
                    Review the upload details, then move into chat.
                  </p>
                </div>
                <div className="flex flex-wrap gap-3">
                  <button
                    onClick={handleUploadReset}
                    className="text-sm text-neutral-300 hover:text-white transition-colors px-4 py-2 border border-neutral-800 rounded hover:border-neutral-700"
                  >
                    Upload New File
                  </button>
                  <button
                    onClick={() => {
                      setPrefilledQuestion(null)
                      setStep("chat")
                    }}
                    className="text-sm text-black bg-white hover:bg-neutral-200 transition-colors px-4 py-2 rounded font-medium"
                  >
                    Continue to Chat
                  </button>
                </div>
              </div>

              <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-5">
                <h3 className="text-base font-semibold mb-3">Suggested Questions</h3>
                <p className="text-xs text-neutral-500 mb-4">
                  Click any suggested question to open it directly in the chat input.
                </p>
                {(uploadResult.profile?.recommended_questions ?? []).length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {(uploadResult.profile?.recommended_questions ?? []).slice(0, 8).map((question) => (
                      <button
                        key={question}
                        type="button"
                        onClick={() => handleSuggestedQuestionClick(question)}
                        className="text-xs border border-neutral-700 text-neutral-300 px-3 py-2 rounded hover:border-neutral-500 hover:text-white transition-colors text-left"
                      >
                        {question}
                      </button>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-neutral-400">
                    No recommended follow-up questions were generated for this file.
                  </p>
                )}
              </div>

              <DataPreview
                schema={uploadResult.schema}
                preview={uploadResult.preview}
                rowCount={uploadResult.row_count}
                profile={uploadResult.profile}
              />
            </div>
          </section>
        )}

        {step === "chat" && uploadResult && (
          <section className="h-full min-h-0 p-4 md:p-6 flex flex-col gap-4">
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
              <div>
                <h2 className="text-xl font-semibold">Chat Interface</h2>
                <p className="text-sm text-neutral-400 mt-1">
                  Full-screen workspace for dataset analysis.
                </p>
              </div>
              <div className="flex flex-wrap gap-3">
                <button
                  onClick={() => setStep("summary")}
                  className="text-sm text-neutral-300 hover:text-white transition-colors px-4 py-2 border border-neutral-800 rounded hover:border-neutral-700"
                >
                  Back to Summary
                </button>
                <button
                  onClick={handleUploadReset}
                  className="text-sm text-neutral-300 hover:text-white transition-colors px-4 py-2 border border-neutral-800 rounded hover:border-neutral-700"
                >
                  Upload New File
                </button>
              </div>
            </div>

            <div className="flex-1 min-h-0">
              <DataChatInterface
                sessionId={uploadResult.session_id}
                profile={uploadResult.profile}
                showStarterPrompts={false}
                prefilledQuestion={prefilledQuestion}
                prefilledQuestionToken={prefilledQuestionToken}
              />
            </div>
          </section>
        )}
      </main>
    </div>
  )
}
