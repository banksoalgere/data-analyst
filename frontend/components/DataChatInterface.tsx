'use client'

import { useState, FormEvent, useRef, useEffect } from "react"
import { FullMessage } from "@/types/chat"
import { DynamicChart } from "./DynamicChart"

interface DataChatInterfaceProps {
  sessionId: string | null
}

export function DataChatInterface({ sessionId }: DataChatInterfaceProps) {
  const [messages, setMessages] = useState<FullMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [inputValue, setInputValue] = useState("")
  const [error, setError] = useState<string | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    if (!inputValue.trim() || loading || !sessionId) return

    const userMessage: FullMessage = {
      id: crypto.randomUUID(),
      role: 'user',
      message: inputValue
    }

    setMessages((prev) => [...prev, userMessage])
    setInputValue("")
    setLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          session_id: sessionId,
          question: inputValue
        }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Analysis failed')
      }

      const result = await response.json()

      const assistantMessage: FullMessage = {
        id: crypto.randomUUID(),
        role: 'assistant',
        message: result.insight,
        chartData: result.data,
        chartConfig: result.chart_config
      }

      setMessages((prev) => [...prev, assistantMessage])

    } catch (err) {
      setError(err instanceof Error ? err.message : 'An error occurred')
    } finally {
      setLoading(false)
    }
  }

  if (!sessionId) {
    return (
      <div className="flex items-center justify-center h-64 bg-neutral-900 border border-neutral-800 rounded-lg">
        <p className="text-neutral-400">
          Upload a CSV file to start analyzing
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-neutral-950 border border-neutral-800 rounded-lg">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-neutral-800 rounded-full mb-4">
                <svg className="w-8 h-8 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-white mb-2">
                Ready to Analyze
              </h2>
              <p className="text-neutral-400">
                Ask questions about your data in plain English
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <div
              key={msg.id}
              className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div className="max-w-3xl w-full">
                <div
                  className={`rounded-lg p-4 ${
                    msg.role === 'user'
                      ? 'bg-neutral-800 text-white ml-auto max-w-2xl'
                      : 'bg-neutral-900 border border-neutral-800 text-neutral-100'
                  }`}
                >
                  <div className="whitespace-pre-wrap mb-3">
                    {msg.message}
                  </div>

                  {/* Render chart if available */}
                  {msg.role === 'assistant' && msg.chartData && msg.chartConfig && (
                    <div className="mt-4">
                      <DynamicChart
                        data={msg.chartData}
                        config={msg.chartConfig}
                      />
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}

          {loading && (
            <div className="flex justify-start">
              <div className="bg-neutral-900 border border-neutral-800 rounded-lg p-4">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 bg-neutral-400 rounded-full animate-pulse" />
                  <div className="w-2 h-2 bg-neutral-400 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }} />
                  <div className="w-2 h-2 bg-neutral-400 rounded-full animate-pulse" style={{ animationDelay: '0.4s' }} />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input */}
      <div className="border-t border-neutral-800 p-4">
        <div className="max-w-4xl mx-auto">
          {error && (
            <div className="mb-3 bg-red-950/50 border border-red-900 text-red-400 px-4 py-2 rounded-lg text-sm">
              {error}
            </div>
          )}
          <form onSubmit={handleSubmit} className="flex gap-3">
            <input
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              className="flex-1 bg-neutral-950 border border-neutral-800 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-700 focus:border-neutral-700 placeholder:text-neutral-500"
              placeholder="Ask a question about your data..."
              disabled={loading}
            />
            <button
              type="submit"
              className="px-6 py-3 bg-neutral-800 text-white rounded-lg hover:bg-neutral-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed border border-neutral-700"
              disabled={loading || !inputValue.trim()}
            >
              {loading ? 'Analyzing...' : 'Ask'}
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}
