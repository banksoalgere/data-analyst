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
  const [summaryMenuValue, setSummaryMenuValue] = useState("")
  const [chatMenuValue, setChatMenuValue] = useState("")
  const [suggestedQuestionValue, setSuggestedQuestionValue] = useState("")

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

  const handleSummaryMenuChange = (value: string) => {
    if (value === "chat") {
      setPrefilledQuestion(null)
      setStep("chat")
    } else if (value === "upload") {
      handleUploadReset()
    }
    setSummaryMenuValue("")
  }

  const handleChatMenuChange = (value: string) => {
    if (value === "summary") {
      setStep("summary")
    } else if (value === "upload") {
      handleUploadReset()
    }
    setChatMenuValue("")
  }

  return (
    <div className="h-screen bg-black text-white flex flex-col">
      <main className="h-full min-h-0">
        {step === "upload" && (
          <section className="h-full flex items-center justify-center p-6">
            <div className="max-w-3xl w-full">
              <CSVUploader onUploadSuccess={handleUploadSuccess} />
            </div>
          </section>
        )}

        {step === "summary" && uploadResult && (
          <section className="h-full overflow-y-auto px-4 py-4 md:px-6">
            <div className="w-full space-y-4">
              <div className="flex justify-end">
                <label htmlFor="summary-menu" className="sr-only">Summary menu</label>
                <select
                  id="summary-menu"
                  value={summaryMenuValue}
                  onChange={(event) => handleSummaryMenuChange(event.target.value)}
                  className="bg-neutral-900 border border-neutral-800 text-sm text-neutral-200 px-3 py-2 rounded focus:outline-none focus:ring-1 focus:ring-neutral-700"
                >
                  <option value="">Menu</option>
                  <option value="chat">Continue to Chat</option>
                  <option value="upload">Upload New File</option>
                </select>
              </div>

              <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
                <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                  <p className="text-xs text-neutral-400">Suggested questions (dropdown)</p>
                  <label htmlFor="suggested-question-menu" className="sr-only">Suggested questions</label>
                  <select
                    id="suggested-question-menu"
                    value={suggestedQuestionValue}
                    onChange={(event) => {
                      const value = event.target.value
                      if (!value) return
                      handleSuggestedQuestionClick(value)
                      setSuggestedQuestionValue("")
                    }}
                    className="bg-neutral-950 border border-neutral-800 text-sm text-neutral-200 px-3 py-2 rounded focus:outline-none focus:ring-1 focus:ring-neutral-700 md:min-w-[360px]"
                  >
                    <option value="">Open a suggested question...</option>
                    {(uploadResult.profile?.recommended_questions ?? []).slice(0, 12).map((question) => (
                      <option key={question} value={question}>
                        {question}
                      </option>
                    ))}
                  </select>
                </div>
                {(uploadResult.profile?.recommended_questions ?? []).length > 0 ? (
                  <p className="mt-3 text-xs text-neutral-500">
                    Choose a question from the dropdown to open chart exploration directly.
                  </p>
                ) : (
                  <p className="mt-3 text-sm text-neutral-400">
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
          <section className="h-full min-h-0 px-4 py-4 md:px-6 flex flex-col gap-3">
            <div className="flex justify-end">
              <label htmlFor="chat-menu" className="sr-only">Chat menu</label>
              <select
                id="chat-menu"
                value={chatMenuValue}
                onChange={(event) => handleChatMenuChange(event.target.value)}
                className="bg-neutral-900 border border-neutral-800 text-sm text-neutral-200 px-3 py-2 rounded focus:outline-none focus:ring-1 focus:ring-neutral-700"
              >
                <option value="">Menu</option>
                <option value="summary">Back to Summary</option>
                <option value="upload">Upload New File</option>
              </select>
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
