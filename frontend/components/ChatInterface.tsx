'use client'

import { useState, FormEvent, useRef, useEffect } from "react"
import { FullMessage } from "@/types/chat"

const EXAMPLE_QUERIES = [
    "TOP PRODUCTS BY REVENUE",
    "CUSTOMER CHURN TREND",
    "CART ABANDONMENT RATES",
    "CHANNEL CONVERSION COMP",
]

export function ChatInterface() {
    const [messages, setMessages] = useState<FullMessage[]>([]);
    const [loading, setLoading] = useState(false);
    const [inputValue, setInputValue] = useState("");
    const [error, setError] = useState<string | null>(null);
    const [streamingMessage, setStreamingMessage] = useState("");
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
        if (!inputValue.trim() || loading) { return }

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
        <div className="flex flex-col h-screen bg-background text-foreground font-mono text-sm">
            {/* Header */}
            <div className="border-b border-border px-6 py-4 flex justify-between items-center bg-card/50 backdrop-blur-md">
                <div>
                    <h1 className="text-sm font-bold tracking-widest uppercase">
                        ANALYTICS_TERMINAL_V1
                    </h1>
                </div>
                <div className="flex items-center gap-2">
                    <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
                    <span className="text-xs text-muted-foreground uppercase tracking-wider">System Online</span>
                </div>
            </div>

            {/* Conversation History */}
            <div className="flex-1 overflow-y-auto p-0">
                <div className="max-w-3xl mx-auto space-y-0 h-full flex flex-col justify-end min-h-0">
                    <div className="pb-8 pt-8 px-6 space-y-8">
                        {messages.length === 0 && !streamingMessage && (
                            <div className="h-full flex flex-col items-center justify-center opacity-0 animate-[fadeIn_0.5s_ease-out_forwards]" style={{ animationDelay: '0.1s', animationFillMode: 'forwards' }}>
                                <div className="border border-border p-8 max-w-lg w-full">
                                    <div className="mb-8 font-bold tracking-tighter text-2xl">
                                        INITIALIZE ANALYSIS...
                                    </div>
                                    <div className="space-y-2">
                                        {EXAMPLE_QUERIES.map((query, idx) => (
                                            <button
                                                key={idx}
                                                onClick={() => handleExampleClick(query)}
                                                className="w-full text-left px-4 py-3 border border-transparent hover:border-primary hover:bg-muted/30 transition-all duration-200 text-xs tracking-wider text-muted-foreground hover:text-foreground flex justify-between items-center group"
                                            >
                                                <span>{query}</span>
                                                <span className="opacity-0 group-hover:opacity-100 transition-opacity">→</span>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                        {messages.map((msg) => (
                            <div
                                key={msg.id}
                                className={`flex flex-col border-l-2 ${msg.role === 'user'
                                        ? 'border-primary pl-6 items-end'
                                        : 'border-muted pl-6 items-start'
                                    }`}
                            >
                                <div className="mb-2 text-[10px] uppercase tracking-widest text-muted-foreground">
                                    {msg.role === 'user' ? '[ USER_INPUT ]' : '[ SYSTEM_RESPONSE ]'}
                                </div>
                                <div className="whitespace-pre-wrap leading-relaxed max-w-2xl">
                                    {msg.message}
                                </div>
                            </div>
                        ))}

                        {streamingMessage && (
                            <div className="flex flex-col border-l-2 border-muted pl-6 items-start">
                                <div className="mb-2 text-[10px] uppercase tracking-widest text-muted-foreground animate-pulse">
                                    [ PROCESSING... ]
                                </div>
                                <div className="whitespace-pre-wrap leading-relaxed max-w-2xl">
                                    {streamingMessage}
                                    <span className="inline-block w-2 h-4 bg-primary ml-1 animate-pulse align-middle"></span>
                                </div>
                            </div>
                        )}
                        <div ref={messagesEndRef} />
                    </div>
                </div>
            </div>

            {/* Input Area */}
            <div className="border-t border-border bg-background p-6">
                <div className="max-w-3xl mx-auto">
                    {error && (
                        <div className="mb-4 border border-destructive/50 text-destructive text-xs p-3">
                            ERROR: {error}
                        </div>
                    )}
                    <form onSubmit={handleSumbmit} className="flex gap-4 items-end">
                        <div className="flex-1 relative">
                            <div className="absolute left-4 top-4 text-muted-foreground pointer-events-none select-none">
                                {'>'}
                            </div>
                            <input
                                value={inputValue}
                                onChange={(e) => setInputValue(e.target.value)}
                                className="w-full bg-card/50 border border-border text-foreground pl-10 pr-4 py-4 focus:outline-none focus:border-primary transition-colors placeholder:text-muted-foreground/30 font-mono text-sm"
                                placeholder="ENTER COMMAND..."
                                disabled={loading}
                                autoFocus
                            />
                        </div>
                        {loading ? (
                            <button
                                type="button"
                                onClick={handleCancel}
                                className="h-[54px] px-8 border border-border hover:bg-muted/50 hover:text-foreground hover:border-foreground transition-all duration-200 uppercase tracking-widest text-xs font-bold"
                            >
                                [ STOP ]
                            </button>
                        ) : (
                            <button
                                type="submit"
                                className="h-[54px] px-8 bg-primary text-primary-foreground hover:bg-primary/90 transition-all duration-200 uppercase tracking-widest text-xs font-bold disabled:opacity-50 disabled:cursor-not-allowed"
                                disabled={loading || !inputValue.trim()}
                            >
                                [ RUN ]
                            </button>
                        )}
                    </form>
                </div>
            </div>
        </div>
    )
}
