'use client'

import { FormEvent, useEffect, useMemo, useRef, useState } from "react"
import { FullMessage } from "@/types/chat"
import { AssistantMessageContent } from "@/components/data-chat/AssistantMessageContent"
import {
  AnalyzeProgressEvent,
  buildAssistantMessageFromAnalyzePayload,
  formatProgressMessage,
  parseAnalyzeStreamEvent,
  parseSseDataLine,
  splitSseFrames,
} from "@/lib/analyze-stream"

interface DatasetProfile {
  recommended_questions?: string[]
}

interface DataChatInterfaceProps {
  sessionId: string | null
  profile?: DatasetProfile | null
  showStarterPrompts?: boolean
  prefilledQuestion?: string | null
  prefilledQuestionToken?: number
}

const DEFAULT_STARTERS = [
  "Give me a high-level overview of this dataset.",
  "What trends stand out over time?",
  "Find meaningful correlations between key metrics.",
]

export function DataChatInterface({
  sessionId,
  profile,
  showStarterPrompts = true,
  prefilledQuestion,
  prefilledQuestionToken,
}: DataChatInterfaceProps) {
  const [messages, setMessages] = useState<FullMessage[]>([])
  const [loading, setLoading] = useState(false)
  const [inputValue, setInputValue] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [streamProgress, setStreamProgress] = useState<string[]>([])
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [showSql, setShowSql] = useState(false)
  const [followUps, setFollowUps] = useState<string[]>([])
  const [selectedChartByMessage, setSelectedChartByMessage] = useState<Record<string, number>>({})
  const [draftingByMessage, setDraftingByMessage] = useState<Record<string, boolean>>({})
  const [approvingByAction, setApprovingByAction] = useState<Record<string, boolean>>({})
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const previousUserQuestionByAssistantId = useMemo(() => {
    const byAssistantId: Record<string, string> = {}
    let latestUserQuestion = "Follow-up actions for this insight"

    for (const message of messages) {
      if (message.role === "user") {
        latestUserQuestion = message.message
      } else {
        byAssistantId[message.id] = latestUserQuestion
      }
    }

    return byAssistantId
  }, [messages])

  const starters = profile?.recommended_questions?.length
    ? profile.recommended_questions.slice(0, 4)
    : DEFAULT_STARTERS

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "auto" })
  }, [messages])

  useEffect(() => {
    setMessages([])
    setConversationId(null)
    setError(null)
    setInputValue("")
    setStreamProgress([])
    setFollowUps([])
    setSelectedChartByMessage({})
    setDraftingByMessage({})
    setApprovingByAction({})
  }, [sessionId])

  useEffect(() => {
    if (!prefilledQuestion) return
    setInputValue(prefilledQuestion)
  }, [prefilledQuestion, prefilledQuestionToken])

  const submitQuestion = async (question: string) => {
    if (!question.trim() || loading || !sessionId) return

    const trimmed = question.trim()
    const userMessage: FullMessage = {
      id: crypto.randomUUID(),
      role: "user",
      message: trimmed,
    }

    setMessages((prev) => [...prev, userMessage])
    setInputValue("")
    setLoading(true)
    setError(null)
    setStreamProgress([])

    try {
      const response = await fetch("/api/analyze/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          session_id: sessionId,
          question: trimmed,
          conversation_id: conversationId,
        }),
      })

      if (!response.ok) {
        const payload = await response.json()
        throw new Error(payload.detail || "Analysis failed")
      }

      if (!response.body) {
        throw new Error("Analysis stream did not return a response body")
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ""
      let receivedResult = false

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const parsedFrames = splitSseFrames(buffer)
        buffer = parsedFrames.remainder

        for (const frame of parsedFrames.frames) {
          const raw = parseSseDataLine(frame)
          if (!raw) continue

          const event = parseAnalyzeStreamEvent(raw)
          if (!event) continue

          const eventType = event.type
          if (eventType === "progress") {
            const progressLine = formatProgressMessage(event as AnalyzeProgressEvent)
            setStreamProgress((prev) => {
              const next = [...prev, progressLine]
              return next.slice(-8)
            })
            continue
          }

          if (eventType === "error") {
            const detail = typeof event.detail === "string" && event.detail ? event.detail : "Analysis failed"
            throw new Error(detail)
          }

          if (eventType === "result") {
            const payload = event.payload as Record<string, unknown> | undefined
            if (!payload) continue

            const assistantMessage = buildAssistantMessageFromAnalyzePayload(payload)

            const incomingConversationId = typeof event.conversation_id === "string" ? event.conversation_id : null
            if (incomingConversationId) {
              setConversationId(incomingConversationId)
            }

            const nextFollowUps = Array.isArray(payload.follow_up_questions)
              ? payload.follow_up_questions.filter((item): item is string => typeof item === "string").slice(0, 3)
              : []
            setFollowUps(nextFollowUps)
            setMessages((prev) => [...prev, assistantMessage])
            receivedResult = true
          }
        }
      }

      if (!receivedResult) {
        throw new Error("Analysis stream ended before returning a result")
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred")
      setStreamProgress([])
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault()
    await submitQuestion(inputValue)
  }

  const draftActionsForMessage = async (messageId: string, question: string, message: FullMessage) => {
    if (!sessionId || draftingByMessage[messageId] || !message.sql) return

    setDraftingByMessage((prev) => ({ ...prev, [messageId]: true }))
    try {
      const response = await fetch("/api/actions/draft", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          question,
          insight: message.message,
          sql: message.sql,
          analysis_type: message.analysisType ?? "other",
          trust: message.trust ?? {},
        }),
      })

      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload.detail || "Failed to draft actions")
      }

      setMessages((prev) =>
        prev.map((item) =>
          item.id === messageId ? { ...item, actionDrafts: payload.actions } : item
        )
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to draft actions")
    } finally {
      setDraftingByMessage((prev) => ({ ...prev, [messageId]: false }))
    }
  }

  const approveAction = async (messageId: string, actionId: string) => {
    if (!sessionId || approvingByAction[actionId]) return

    setApprovingByAction((prev) => ({ ...prev, [actionId]: true }))
    try {
      const response = await fetch("/api/actions/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: sessionId,
          action_id: actionId,
        }),
      })

      const payload = await response.json()
      if (!response.ok) {
        throw new Error(payload.detail || "Failed to approve action")
      }

      setMessages((prev) =>
        prev.map((item) => {
          if (item.id !== messageId || !item.actionDrafts) return item
          return {
            ...item,
            actionDrafts: item.actionDrafts.map((action) =>
              action.action_id === actionId ? payload.action : action
            ),
          }
        })
      )
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to approve action")
    } finally {
      setApprovingByAction((prev) => ({ ...prev, [actionId]: false }))
    }
  }

  if (!sessionId) {
    return (
      <div className="flex items-center justify-center h-64 bg-neutral-900 border border-neutral-800 rounded-lg">
        <p className="text-neutral-400">Upload a CSV file to start analyzing</p>
      </div>
    )
  }

  return (
    <div className="flex flex-col h-full bg-neutral-950 border border-neutral-800 rounded-lg">
      <div className="flex-1 overflow-y-auto p-6">
        <div className="w-full space-y-6">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <div className="inline-flex items-center justify-center w-16 h-16 bg-neutral-800 rounded-full mb-4">
                <svg className="w-8 h-8 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h2 className="text-xl font-semibold text-white mb-2">Ready to Analyze</h2>
              <p className="text-neutral-400">Ask questions about your data in plain English</p>
              {showStarterPrompts && (
                <div className="mt-6 flex flex-wrap justify-center gap-2">
                  {starters.map((starter) => (
                    <button
                      key={starter}
                      type="button"
                      className="text-xs border border-neutral-700 text-neutral-300 px-3 py-1.5 rounded hover:border-neutral-500 hover:text-white transition-colors"
                      onClick={() => setInputValue(starter)}
                    >
                      {starter}
                    </button>
                  ))}
                </div>
              )}
            </div>
          )}

          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === "user" ? "justify-end" : "justify-start"}`}>
              <div className="max-w-3xl w-full">
                <div
                  className={`rounded-lg p-4 ${
                    msg.role === "user"
                      ? "bg-neutral-800 text-white ml-auto max-w-2xl"
                      : "bg-neutral-900 border border-neutral-800 text-neutral-100"
                  }`}
                >
                  <div className="whitespace-pre-wrap mb-3">{msg.message}</div>

                  {msg.role === "assistant" && (
                    <AssistantMessageContent
                      message={msg}
                      showSql={showSql}
                      selectedChartIndex={selectedChartByMessage[msg.id] ?? 0}
                      onChartSelect={(chartIndex) =>
                        setSelectedChartByMessage((prev) => ({ ...prev, [msg.id]: chartIndex }))
                      }
                      onDraftActions={() => {
                        draftActionsForMessage(
                          msg.id,
                          previousUserQuestionByAssistantId[msg.id] ?? "Follow-up actions for this insight",
                          msg
                        )
                      }}
                      onApproveAction={(actionId) => approveAction(msg.id, actionId)}
                      drafting={Boolean(draftingByMessage[msg.id])}
                      approvingByAction={approvingByAction}
                    />
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
                  <div className="w-2 h-2 bg-neutral-400 rounded-full animate-pulse" style={{ animationDelay: "0.2s" }} />
                  <div className="w-2 h-2 bg-neutral-400 rounded-full animate-pulse" style={{ animationDelay: "0.4s" }} />
                </div>
                {streamProgress.length > 0 && (
                  <div className="mt-3 space-y-1">
                    {streamProgress.map((item, index) => (
                      <div key={`${item}-${index}`} className="text-xs text-neutral-400">
                        {item}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      <div className="border-t border-neutral-800 p-4">
        <div className="w-full">
          <div className="mb-3 flex items-center justify-between">
            <div className="text-xs text-neutral-500">Conversation: {conversationId ?? "new"}</div>
            <button
              type="button"
              onClick={() => setShowSql((value) => !value)}
              className="text-xs text-neutral-400 hover:text-white transition-colors border border-neutral-700 px-2 py-1 rounded"
            >
              {showSql ? "Hide SQL" : "Show SQL"}
            </button>
          </div>

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
              {loading ? "Analyzing..." : "Ask"}
            </button>
          </form>

          {followUps.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-2">
              {followUps.map((question) => (
                <button
                  key={question}
                  type="button"
                  onClick={() => submitQuestion(question)}
                  className="text-xs border border-neutral-700 text-neutral-300 px-3 py-1.5 rounded hover:border-neutral-500 hover:text-white transition-colors"
                  disabled={loading}
                >
                  {question}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
