import { useState, useEffect, useRef } from "react"
import { useAuth } from "@/contexts/AuthContext"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Bot, Send, Plus, Trash2, User, MessageSquare, PanelLeftClose, PanelLeft, X } from "lucide-react"

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000"

interface Message {
  id: string
  role: "user" | "assistant"
  content: string
  timestamp: string
}

interface SessionSummary {
  id: string
  title: string | null
  created_at: string
  updated_at: string
  message_count: number
}

function formatTime(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  } catch {
    return ""
  }
}

function ChatMessage({ msg }: { msg: Message }) {
  const isUser = msg.role === "user"

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
      <div
        className={`flex h-8 w-8 shrink-0 items-center justify-center rounded-full ${
          isUser
            ? "bg-primary/20 text-primary"
            : "bg-secondary text-muted-foreground"
        }`}
      >
        {isUser ? <User className="h-4 w-4" /> : <Bot className="h-4 w-4" />}
      </div>

      <div className={`max-w-[75%] ${isUser ? "items-end" : "items-start"}`}>
        <div
          className={`rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
            isUser
              ? "bg-primary text-primary-foreground"
              : "bg-secondary text-foreground"
          }`}
        >
          {msg.content}
        </div>
        <p
          className={`mt-1 text-[10px] text-muted-foreground/50 ${
            isUser ? "text-right" : "text-left"
          }`}
        >
          {formatTime(msg.timestamp)}
        </p>
      </div>
    </div>
  )
}

function LoadingDots() {
  return (
    <div className="flex items-center gap-1 px-1 py-2">
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground/40 [animation-delay:0ms]" />
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground/40 [animation-delay:150ms]" />
      <span className="h-1.5 w-1.5 animate-bounce rounded-full bg-muted-foreground/40 [animation-delay:300ms]" />
    </div>
  )
}

export function ChatPage() {
  const { user } = useAuth()
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState("")
  const [sessions, setSessions] = useState<SessionSummary[]>([])
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" })
  }, [messages])

  // Focus input on load
  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // Load sessions on mount
  useEffect(() => {
    loadSessions()
  }, [])

  // Load messages when active session changes
  useEffect(() => {
    if (activeSessionId) {
      loadMessages(activeSessionId)
    } else {
      setMessages([])
    }
  }, [activeSessionId])

  async function request<T>(path: string, options?: RequestInit): Promise<T> {
    const token = localStorage.getItem("flow_access_token")
    const res = await fetch(`${API_URL}${path}`, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...options?.headers,
      },
    })

    if (!res.ok) {
      let detail = `Request failed (${res.status})`
      try {
        const body = await res.json()
        if (body.detail) detail = body.detail
      } catch {
        // ignore
      }
      throw new Error(detail)
    }

    if (res.status === 204) return undefined as T
    return res.json() as Promise<T>
  }

  async function loadSessions() {
    setIsLoading(true)
    setError(null)
    try {
      const data = await request<{ sessions: SessionSummary[] }>(
        "/api/agent/sessions"
      )
      setSessions(data.sessions)
      // Auto-select most recent session if none active
      if (!activeSessionId && data.sessions.length > 0) {
        setActiveSessionId(data.sessions[0].id)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load sessions")
    } finally {
      setIsLoading(false)
    }
  }

  async function loadMessages(_sessionId: string) {
    // The backend doesn't have a GET messages endpoint yet,
    // so we show a placeholder. Messages come from the chat flow.
    setMessages([])
  }

  async function newSession() {
    setActiveSessionId(null)
    setMessages([])
    setInput("")
    setError(null)
    inputRef.current?.focus()
  }

  async function deleteSession(sessionId: string) {
    try {
      await request(`/api/agent/sessions/${sessionId}`, {
        method: "DELETE",
      })
      setSessions((prev) => prev.filter((s) => s.id !== sessionId))
      if (activeSessionId === sessionId) {
        const remaining = sessions.filter((s) => s.id !== sessionId)
        setActiveSessionId(remaining.length > 0 ? remaining[0].id : null)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete session")
    }
  }

  async function sendMessage() {
    const text = input.trim()
    if (!text || isSending) return

    setInput("")
    setError(null)

    // Add user message immediately
    const userMsg: Message = {
      id: `user-${Date.now()}`,
      role: "user",
      content: text,
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMsg])

    setIsSending(true)

    try {
      const data = await request<{
        session_id: string
        response: string
      }>("/api/agent/chat", {
        method: "POST",
        body: JSON.stringify({
          session_id: activeSessionId,
          message: text,
        }),
      })

      // Update active session
      setActiveSessionId(data.session_id)

      // Add assistant response
      const assistantMsg: Message = {
        id: `assistant-${Date.now()}`,
        role: "assistant",
        content: data.response,
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, assistantMsg])

      // Refresh session list
      loadSessions()
    } catch (e) {
      const errorMsg: Message = {
        id: `error-${Date.now()}`,
        role: "assistant",
        content: e instanceof Error ? e.message : "Something went wrong",
        timestamp: new Date().toISOString(),
      }
      setMessages((prev) => [...prev, errorMsg])
    } finally {
      setIsSending(false)
      inputRef.current?.focus()
    }
  }

  function handleKeyDown(e: React.KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <div className="flex h-[calc(100vh-3.5rem)] -mx-8 -mt-8 gap-0 relative">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/40 sm:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Toggle button — mobile */}
      <button
        onClick={() => setSidebarOpen(!sidebarOpen)}
        className="fixed bottom-24 left-4 z-40 flex h-9 w-9 items-center justify-center rounded-full bg-primary text-primary-foreground shadow-lg sm:hidden"
        aria-label={sidebarOpen ? "Close sidebar" : "Open sidebar"}
      >
        {sidebarOpen ? <PanelLeftClose className="h-4 w-4" /> : <PanelLeft className="h-4 w-4" />}
      </button>

      {/* Session sidebar */}
      <div className={`fixed inset-y-0 left-0 z-40 flex w-72 flex-col border-r border-border bg-sidebar-background transition-transform duration-200 sm:relative sm:translate-x-0 ${
        sidebarOpen ? "translate-x-0" : "-translate-x-full"
      }`}>
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <h2 className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
            Sessions
          </h2>
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={newSession}
              className="h-7 gap-1.5 text-xs"
            >
              <Plus className="h-3.5 w-3.5" />
              New
            </Button>
            <button
              onClick={() => setSidebarOpen(false)}
              className="flex h-6 w-6 items-center justify-center rounded-md text-muted-foreground hover:text-foreground sm:hidden"
              aria-label="Close sidebar"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-2 py-3">
          {isLoading && sessions.length === 0 && (
            <div className="px-3 py-8 text-center text-xs text-muted-foreground">
              Loading sessions...
            </div>
          )}

          {!isLoading && sessions.length === 0 && (
            <div className="px-3 py-8 text-center text-xs text-muted-foreground">
              <MessageSquare className="mx-auto mb-2 h-8 w-8 opacity-30" />
              <p>No sessions yet</p>
              <p className="mt-1">Start a new chat to begin</p>
            </div>
          )}

          {sessions.map((session) => (
            <div
              key={session.id}
              className={`group mb-1 flex cursor-pointer items-center justify-between rounded-md px-3 py-2 text-sm transition-colors ${
                activeSessionId === session.id
                  ? "bg-sidebar-accent text-sidebar-foreground"
                  : "text-sidebar-foreground/60 hover:bg-sidebar-accent hover:text-sidebar-foreground"
              }`}
              onClick={() => setActiveSessionId(session.id)}
            >
              <div className="min-w-0 flex-1">
                <p className="truncate text-xs font-medium">
                  {session.title || `Chat ${session.message_count > 0 ? `(${session.message_count})` : ""}`}
                </p>
                <p className="text-[10px] text-muted-foreground/50">
                  {session.message_count} messages
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  deleteSession(session.id)
                }}
                className="ml-2 shrink-0 opacity-0 transition-opacity group-hover:opacity-100"
              >
                <Trash2 className="h-3.5 w-3.5 text-muted-foreground hover:text-destructive" />
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Main chat area */}
      <div className="flex flex-1 flex-col">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto px-6 py-6">
          {messages.length === 0 && !isSending && (
            <div className="flex h-full items-center justify-center">
              <div className="max-w-md text-center">
                <Bot className="mx-auto mb-4 h-12 w-12 text-muted-foreground/30" />
                <h3 className="text-lg font-semibold text-foreground">
                  {activeSessionId ? "Continue your conversation" : "Start a new conversation"}
                </h3>
                <p className="mt-2 text-sm text-muted-foreground">
                  {activeSessionId
                    ? "This session has no messages yet. Send a message to get started."
                    : 'Click "New" or select a session, then type your message below to begin.'}
                </p>
              </div>
            </div>
          )}

          {messages.length > 0 && (
            <div className="mx-auto max-w-3xl space-y-4">
              {messages.map((msg) => (
                <ChatMessage key={msg.id} msg={msg} />
              ))}
            </div>
          )}

          {isSending && (
            <div className="mx-auto max-w-3xl pt-2">
              <div className="flex items-center gap-3">
                <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-secondary text-muted-foreground">
                  <Bot className="h-4 w-4" />
                </div>
                <LoadingDots />
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* Error banner */}
        {error && (
          <div className="mx-6 mb-2 rounded-md bg-destructive/10 px-4 py-2 text-xs text-destructive">
            {error}
            <button
              onClick={() => setError(null)}
              className="ml-2 underline hover:no-underline"
            >
              Dismiss
            </button>
          </div>
        )}

        {/* Input */}
        <div className="border-t border-border px-6 py-4">
          <div className="mx-auto flex max-w-3xl gap-3">
            <Input
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={
                isSending
                  ? "Waiting for response..."
                  : (user
                      ? `Ask your agent anything, ${user.name?.split(" ")[0]}...`
                      : "Type your message...")
              }
              disabled={isSending}
              className="h-10 bg-secondary/50"
            />
            <Button
              onClick={sendMessage}
              disabled={!input.trim() || isSending}
              className="h-10 px-4"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  )
}
