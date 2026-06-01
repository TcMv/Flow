import { useState, useEffect } from "react"
import { useAuth } from "@/contexts/AuthContext"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Bot, Activity, Users, Cpu, Sparkles, CheckCircle2, Loader2, Database, Workflow } from "lucide-react"

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000"

export function DashboardHome() {
  const { user } = useAuth()
  const [seedStatus, setSeedStatus] = useState<{
    is_seeded: boolean
    skills: { available: string[]; existing: string[]; missing: string[] }
    workflows: { available: string[]; existing: string[]; missing: string[] }
  } | null>(null)
  const [loading, setLoading] = useState(true)
  const [seeding, setSeeding] = useState(false)
  const [seedResult, setSeedResult] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    checkSeedStatus()
  }, [])

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
      try { const b = await res.json(); if (b.detail) detail = b.detail } catch {}
      throw new Error(detail)
    }
    return res.json() as Promise<T>
  }

  async function checkSeedStatus() {
    setLoading(true)
    setError(null)
    try {
      const data = await request<{
        is_seeded: boolean
        skills: { available: string[]; existing: string[]; missing: string[] }
        workflows: { available: string[]; existing: string[]; missing: string[] }
      }>("/api/demo/seed")
      setSeedStatus(data)
    } catch (e) {
      // Silently handle — probably not implemented on backend yet
      setSeedStatus(null)
    } finally {
      setLoading(false)
    }
  }

  async function handleSeed() {
    setSeeding(true)
    setSeedResult(null)
    setError(null)
    try {
      const data = await request<{
        status: string
        skills_created: string[]
        workflows_created: string[]
        message: string
      }>("/api/demo/seed", { method: "POST" })
      setSeedResult(data.message)
      checkSeedStatus()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to seed demo data")
    } finally {
      setSeeding(false)
    }
  }

  const isSeeded = seedStatus?.is_seeded ?? false
  const totalAvailable = (seedStatus?.skills.available.length ?? 0) + (seedStatus?.workflows.available.length ?? 0)

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Welcome back, {user?.name ?? "User"}.
        </p>
      </div>

      {/* Seed banner — shown when no demo data exists */}
      {!loading && !isSeeded && (
        <Card className="border-emerald-500/30 bg-emerald-500/5">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-emerald-500/10">
                  <Sparkles className="h-5 w-5 text-emerald-500" />
                </div>
                <div>
                  <CardTitle className="text-sm">Welcome to Flow! 🚀</CardTitle>
                  <CardDescription className="text-xs">
                    Your workspace is empty. Populate it with sample skills and workflows to see Flow in action.
                  </CardDescription>
                </div>
              </div>
              <Button
                onClick={handleSeed}
                disabled={seeding}
                size="sm"
                className="bg-emerald-600 hover:bg-emerald-700 text-white h-9"
              >
                {seeding ? (
                  <><Loader2 className="mr-1.5 h-4 w-4 animate-spin" /> Loading...</>
                ) : (
                  <><Sparkles className="mr-1.5 h-4 w-4" /> Seed Demo Data</>
                )}
              </Button>
            </div>
          </CardHeader>
        </Card>
      )}

      {/* Seed success message */}
      {seedResult && (
        <div className="flex items-center gap-2 rounded-lg border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          <CheckCircle2 className="h-4 w-4 shrink-0" />
          {seedResult}
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
          <button onClick={() => setError(null)} className="ml-2 underline">Dismiss</button>
        </div>
      )}

      {/* Stats grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {[
          { label: "Skills Available", value: isSeeded ? seedStatus!.skills.available.length.toString() : "—", icon: Bot },
          { label: "Workflows Ready", value: isSeeded ? seedStatus!.workflows.available.length.toString() : "—", icon: Workflow },
          { label: "Team Members", value: "1", icon: Users },
          { label: "Status", value: isSeeded ? "Ready" : "Needs Setup", icon: Cpu },
        ].map((stat) => (
          <Card key={stat.label} className="border-border/50">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.label}
              </CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-foreground">{stat.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Demo content — shown when seeded */}
      {isSeeded && (
        <div className="grid gap-4 sm:grid-cols-2">
          <Card className="border-border/50">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm">
                <Bot className="h-4 w-4 text-primary" />
                Pre-loaded Skills
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {seedStatus!.skills.existing.map((name) => (
                <div key={name} className="flex items-center gap-2 rounded-md bg-muted/50 px-3 py-2 text-xs">
                  <Sparkles className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
                  <span className="font-medium">{name}</span>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="border-border/50">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-sm">
                <Workflow className="h-4 w-4 text-primary" />
                Pre-built Workflows
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {seedStatus!.workflows.existing.map((name) => (
                <div key={name} className="flex items-center gap-2 rounded-md bg-muted/50 px-3 py-2 text-xs">
                  <Activity className="h-3.5 w-3.5 text-primary shrink-0" />
                  <span className="font-medium">{name}</span>
                </div>
              ))}
              <div className="mt-3 rounded-md bg-primary/5 px-3 py-2 text-xs text-muted-foreground">
                💡 Go to <strong>Workflows</strong> to run one, or <strong>Chat</strong> to ask your agent to run it.
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Quick actions */}
      <Card className="border-border/50">
        <CardHeader>
          <CardTitle className="text-base">Quick Actions</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3">
          <div className="flex items-center justify-between rounded-lg border border-border/50 px-4 py-3">
            <div className="flex items-center gap-3">
              <Bot className="h-5 w-5 text-primary" />
              <div>
                <p className="text-sm font-medium">Chat with your Agent</p>
                <p className="text-xs text-muted-foreground">Ask it to do anything — research, draft, run workflows</p>
              </div>
            </div>
            <Button variant="outline" size="sm" className="text-xs" onClick={() => window.location.href = "/chat"}>
              Open Chat
            </Button>
          </div>
          <div className="flex items-center justify-between rounded-lg border border-border/50 px-4 py-3">
            <div className="flex items-center gap-3">
              <Activity className="h-5 w-5 text-primary" />
              <div>
                <p className="text-sm font-medium">Run a Workflow</p>
                <p className="text-xs text-muted-foreground">Execute a pre-built process with human checkpoints</p>
              </div>
            </div>
            <Button variant="outline" size="sm" className="text-xs" onClick={() => window.location.href = "/workflows"}>
              View Workflows
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
