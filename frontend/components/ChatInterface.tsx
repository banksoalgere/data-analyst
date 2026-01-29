'use client'

import { useState, FormEvent, useRef, useEffect } from "react"
import { FullMessage } from "@/types/chat"

const EXAMPLE_QUERIES = [
    "What were our top 5 products by revenue last month?",
    "Show me the customer churn rate trend",
    "Which products have the highest cart abandonment?",
    "Compare conversion rates across marketing channels",
]

export function ChatInterface() {
    const [ messages, setMessages ] = useState<FullMessage[]>([]);
    const [ loading, setLoading ] = useState(false);
    const [ inputValue, setInputValue ] = useState("");
    const [ error, setError ] = useState<string | null>(null);
    const [ streamingMessage, setStreamingMessage ] = useState("");
    const abortControllerRef = useRef<AbortController | null>(null);
    const messagesEndRef = useRef<HTMLDivElement>(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }

    useEffect(() => {
        scrollToBottom();
    }, [messages, streamingMessage]);

    const handleSumbmit = async (e: FormEvent) => {
        e.preventDefault()
        if (!inputValue.trim() || loading) {return}

        const userMessage: FullMessage = {
            id: crypto.randomUUID(),
            role: 'user',
            message: inputValue
        }

        setMessages((prev) => [...prev, userMessage]);
        setInputValue("");
        setLoading(true);
        setError(null);
        setStreamingMessage("");

        // Create abort controller for cancelling the stream
        abortControllerRef.current = new AbortController();

        try {
            const response = await fetch('/api/chat/stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: userMessage.message }),
                signal: abortControllerRef.current.signal,
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const reader = response.body?.getReader();
            const decoder = new TextDecoder();

            if (!reader) {
                throw new Error('No response body');
            }

            let fullText = "";

            while (true) {
                const { done, value } = await reader.read();

                if (done) break;

                const chunk = decoder.decode(value);
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const jsonStr = line.slice(6);
                        if (jsonStr.trim()) {
                            try {
                                const data = JSON.parse(jsonStr);

                                if (data.error) {
                                    setError(data.error);
                                    break;
                                }

                                if (data.content) {
                                    fullText += data.content;
                                    setStreamingMessage(fullText);
                                }

                                if (data.done) {
                                    // Streaming complete, add final message
                                    const assistantMessage: FullMessage = {
                                        id: crypto.randomUUID(),
                                        role: 'assistant',
                                        message: fullText
                                    };
                                    setMessages((prev) => [...prev, assistantMessage]);
                                    setStreamingMessage("");
                                }
                            } catch (parseError) {
                                console.error('Failed to parse SSE data:', parseError);
                            }
                        }
                    }
                }
            }
        } catch (err) {
            if (err instanceof Error && err.name === 'AbortError') {
                setError('Request cancelled');
            } else {
                setError(err instanceof Error ? err.message : 'An error occurred');
            }
            setStreamingMessage("");
        } finally {
            setLoading(false);
            abortControllerRef.current = null;
        }
    }

    const handleCancel = () => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }
    }

    const handleExampleClick = (query: string) => {
        setInputValue(query);
    }

    return (
        <div className="flex flex-col h-screen bg-black">
            {/* Header */}
            <div className="bg-neutral-900/50 border-b border-neutral-800 px-6 py-4 backdrop-blur-sm">
                <h1 className="text-2xl font-bold text-white">
                    E-commerce Analytics AI
                </h1>
                <p className="text-sm text-neutral-400 mt-1">
                    Ask questions about your store performance, products, and customers
                </p>
            </div>

            {/* Conversation History */}
            <div className="flex-1 overflow-y-auto px-6 py-4">
                <div className="max-w-4xl mx-auto space-y-4">
                    {messages.length === 0 && !streamingMessage && (
                        <div className="text-center py-12">
                            <div className="inline-flex items-center justify-center w-16 h-16 bg-neutral-800 rounded-full mb-4">
                                <svg className="w-8 h-8 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                </svg>
                            </div>
                            <h2 className="text-xl font-semibold text-white mb-2">
                                Welcome to Your Analytics Assistant
                            </h2>
                            <p className="text-neutral-400 mb-6">
                                Get instant insights about your e-commerce data
                            </p>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 max-w-2xl mx-auto">
                                {EXAMPLE_QUERIES.map((query, idx) => (
                                    <button
                                        key={idx}
                                        onClick={() => handleExampleClick(query)}
                                        className="text-left p-3 bg-neutral-900 border border-neutral-800 rounded-lg hover:border-neutral-700 hover:bg-neutral-800 transition-colors text-sm text-neutral-300 hover:text-white"
                                    >
                                        {query}
                                    </button>
                                ))}
                            </div>
                        </div>
                    )}

                    {messages.map((msg) => (
                        <div
                            key={msg.id}
                            className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
                        >
                            <div
                                className={`max-w-3xl rounded-lg p-4 ${
                                    msg.role === 'user'
                                        ? 'bg-neutral-800 text-white'
                                        : 'bg-neutral-900 border border-neutral-800 text-neutral-100'
                                }`}
                            >
                                <div className="flex items-start gap-3">
                                    {msg.role === 'assistant' && (
                                        <div className="flex-shrink-0 w-8 h-8 bg-neutral-800 rounded-full flex items-center justify-center">
                                            <svg className="w-5 h-5 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                            </svg>
                                        </div>
                                    )}
                                    <div className="flex-1 whitespace-pre-wrap">
                                        {msg.message}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}

                    {streamingMessage && (
                        <div className="flex justify-start">
                            <div className="max-w-3xl rounded-lg p-4 bg-neutral-900 border border-neutral-800 text-neutral-100">
                                <div className="flex items-start gap-3">
                                    <div className="flex-shrink-0 w-8 h-8 bg-neutral-800 rounded-full flex items-center justify-center">
                                        <svg className="w-5 h-5 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                                        </svg>
                                    </div>
                                    <div className="flex-1">
                                        <div className="whitespace-pre-wrap">
                                            {streamingMessage}
                                            <span className="inline-block w-1 h-4 bg-neutral-400 ml-1 animate-pulse"></span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* Fixed Input at Bottom */}
            <div className="bg-neutral-900/50 border-t border-neutral-800 px-6 py-4 backdrop-blur-sm">
                <div className="max-w-4xl mx-auto">
                    {error && (
                        <div className="mb-3 bg-red-950/50 border border-red-900 text-red-400 px-4 py-2 rounded-lg text-sm">
                            {error}
                        </div>
                    )}
                    <form onSubmit={handleSumbmit} className="flex gap-3">
                        <input
                            value={inputValue}
                            onChange={(e) => setInputValue(e.target.value)}
                            className="flex-1 bg-neutral-950 border border-neutral-800 text-white px-4 py-3 rounded-lg focus:outline-none focus:ring-1 focus:ring-neutral-700 focus:border-neutral-700 placeholder:text-neutral-500"
                            placeholder="Ask about sales, products, customers, conversion rates..."
                            disabled={loading}
                        />
                        {loading ? (
                            <button
                                type="button"
                                onClick={handleCancel}
                                className="px-6 py-3 bg-red-950 text-red-400 border border-red-900 rounded-lg hover:bg-red-900 transition-colors font-medium"
                            >
                                Stop
                            </button>
                        ) : (
                            <button
                                type="submit"
                                className="px-6 py-3 bg-neutral-800 text-white rounded-lg hover:bg-neutral-700 transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed border border-neutral-700"
                                disabled={loading || !inputValue.trim()}
                            >
                                Send
                            </button>
                        )}
                    </form>
                    <p className="text-xs text-neutral-600 mt-2 text-center">
                        Ask questions about your e-commerce metrics, products, and customer behavior
                    </p>
                </div>
            </div>
        </div>
    )
}
