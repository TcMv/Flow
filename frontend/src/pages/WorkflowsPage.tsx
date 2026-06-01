import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  Play,
  Plus,
  FileText,
  Loader2,
  CheckCircle2,
  XCircle,
  PauseCircle,
  Clock,
  ArrowLeft,
  Workflow,
  Sparkles,
} from "lucide-react"

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000"

interface WorkflowDef {
  id: string
  name: string
  description: string
  trigger: string
  definition: Record<string, unknown>
  source_text: string | null
  status: string
  schedule: string | null
  next_run_at: string | null
  owner_id: string
  owner_name: string | null
  created_at: string
  updated_at: string
}

interface TaskRun {
  id: string
  task_id: string
  skill_name: string | null
  task_type: string
  status: string
  input_data: Record<string, unknown> | null
  output_data: Record<string, unknown> | null
  feedback: string | null
  started_at: string | null
  completed_at: string | null
}

interface WorkflowRun {
  id: string
  workflow_id: string
  status: string
  current_task_id: string | null
  result: string | null
  error: string | null
  started_at: string | null
  completed_at: string | null
  created_at: string
  task_runs: TaskRun[]
}

function formatDate(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" })
  } catch {
    return ""
  }
}

function formatDateTime(iso: string | null): string {
  if (!iso) return ""
  try {
    const d = new Date(iso)
    return d.toLocaleString([], { month: "short", day: "numeric", hour: "2-digit", minute: "2-digit" })
  } catch {
    return ""
  }
}

function statusBadge(status: string) {
  const variants: Record<string, string> = {
    active: "bg-green-500/10 text-green-600 border-green-200",
    draft: "bg-yellow-500/10 text-yellow-600 border-yellow-200",
    archived: "bg-gray-500/10 text-gray-600 border-gray-200",
    completed: "bg-green-500/10 text-green-600 border-green-200",
    running: "bg-blue-500/10 text-blue-600 border-blue-200",
    paused: "bg-orange-500/10 text-orange-600 border-orange-200",
    failed: "bg-red-500/10 text-red-600 border-red-200",
    cancelled: "bg-gray-500/10 text-gray-600 border-gray-200",
  }
  return variants[status] ?? "bg-gray-500/10 text-gray-600 border-gray-200"
}

function statusIcon(status: string) {
  switch (status) {
    case "completed": return <CheckCircle2 className="h-4 w-4 text-green-600" />
    case "running": return <Loader2 className="h-4 w-4 text-blue-600 animate-spin" />
    case "paused": return <PauseCircle className="h-4 w-4 text-orange-600" />
    case "failed": return <XCircle className="h-4 w-4 text-red-600" />
    default: return <Clock className="h-4 w-4 text-yellow-600" />
  }
}

// ── API helper ──────────────────────────────────────────────────────

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
    try { const body = await res.json(); if (body.detail) detail = body.detail } catch { /* ignore */ }
    throw new Error(detail)
  }
  if (res.status === 204) return undefined as T
  return res.json() as Promise<T>
}

// ── Main Component ─────────────────────────────────────────────────

export function WorkflowsPage() {
  const [workflows, setWorkflows] = useState<WorkflowDef[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Compiler state
  const [compilerOpen, setCompilerOpen] = useState(false)
  const [processDesc, setProcessDesc] = useState("")
  const [wfName, setWfName] = useState("")
  const [compiling, setCompiling] = useState(false)
  const [compiledDef, setCompiledDef] = useState<Record<string, unknown> | null>(null)
  const [saving, setSaving] = useState(false)

  // Detail state
  const [selectedWf, setSelectedWf] = useState<WorkflowDef | null>(null)
  const [runs, setRuns] = useState<WorkflowRun[]>([])
  const [loadingRuns, setLoadingRuns] = useState(false)
  const [running, setRunning] = useState(false)
  const [cronInput, setCronInput] = useState("")
  const [scheduling, setScheduling] = useState(false)

  useEffect(() => {
    loadWorkflows()
  }, [])

  async function loadWorkflows() {
    setIsLoading(true)
    setError(null)
    try {
      const data = await request<{ workflows: WorkflowDef[] }>("/api/workflows")
      setWorkflows(data.workflows)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load workflows")
    } finally {
      setIsLoading(false)
    }
  }

  // ── Compiler ──────────────────────────────────────────────────────

  async function handleCompile() {
    if (!processDesc.trim()) return
    setCompiling(true)
    setCompiledDef(null)
    try {
      const data = await request<{
        name: string
        definition: Record<string, unknown>
        raw_response: string
      }>("/api/workflows/compile", {
        method: "POST",
        body: JSON.stringify({
          description: processDesc,
          name: wfName || undefined,
        }),
      })
      setCompiledDef(data.definition)
      setWfName(data.name)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Compilation failed")
    } finally {
      setCompiling(false)
    }
  }

  async function handleSave() {
    if (!compiledDef) return
    setSaving(true)
    try {
      await request<WorkflowDef>("/api/workflows", {
        method: "POST",
        body: JSON.stringify({
          name: wfName || compiledDef.name || "Unnamed Workflow",
          description: typeof compiledDef.description === "string" ? compiledDef.description : "",
          trigger: "chat",
          definition: compiledDef,
        }),
      })
      setCompiledDef(null)
      setProcessDesc("")
      setWfName("")
      setCompilerOpen(false)
      loadWorkflows()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to save workflow")
    } finally {
      setSaving(false)
    }
  }

  // ── Detail view ───────────────────────────────────────────────────

  async function openDetail(wf: WorkflowDef) {
    setSelectedWf(wf)
    setLoadingRuns(true)
    try {
      const data = await request<{ runs: WorkflowRun[] }>(`/api/workflows/${wf.id}/runs`)
      setRuns(data.runs)
    } catch {
      setRuns([])
    } finally {
      setLoadingRuns(false)
    }
  }

  async function handleRun() {
    if (!selectedWf) return
    setRunning(true)
    try {
      await request<WorkflowRun>(`/api/workflows/${selectedWf.id}/run`, {
        method: "POST",
      })
      // Reload runs
      const data = await request<{ runs: WorkflowRun[] }>(`/api/workflows/${selectedWf.id}/runs`)
      setRuns(data.runs)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to run workflow")
    } finally {
      setRunning(false)
    }
  }

  async function handleCheckpoint(runId: string, _taskId: string, approved: boolean) {
    try {
      await request<WorkflowRun>(`/api/workflows/runs/${runId}/checkpoint`, {
        method: "POST",
        body: JSON.stringify({
          approved,
          feedback: approved ? null : "Rejected by user",
        }),
      })
      // Refresh runs
      if (selectedWf) {
        const data = await request<{ runs: WorkflowRun[] }>(`/api/workflows/${selectedWf.id}/runs`)
        setRuns(data.runs)
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Checkpoint failed")
    }
  }

  // ── Schedule ──────────────────────────────────────────────────────

  async function handleSchedule() {
    if (!selectedWf || !cronInput.trim()) return
    setScheduling(true)
    try {
      const updated = await request<WorkflowDef>(`/api/workflows/${selectedWf.id}/schedule`, {
        method: "POST",
        body: JSON.stringify({ cron_expression: cronInput.trim() }),
      })
      setSelectedWf(updated)
      setCronInput("")
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to set schedule")
    } finally {
      setScheduling(false)
    }
  }

  async function handleUnschedule() {
    if (!selectedWf) return
    setScheduling(true)
    try {
      const updated = await request<WorkflowDef>(`/api/workflows/${selectedWf.id}/unschedule`, {
        method: "POST",
      })
      setSelectedWf(updated)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to remove schedule")
    } finally {
      setScheduling(false)
    }
  }

  // ── Render ────────────────────────────────────────────────────────

  if (selectedWf) {
    return (
      <div className="space-y-6">
        {/* Back button */}
        <button
          onClick={() => { setSelectedWf(null); setRuns([]) }}
          className="flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground transition-colors"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Workflows
        </button>

        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-foreground">{selectedWf.name}</h1>
            <p className="mt-1 text-sm text-muted-foreground">{selectedWf.description || "No description"}</p>
          </div>
          <div className="flex items-center gap-2">
            <Badge className={statusBadge(selectedWf.status)} variant="outline">
              {selectedWf.status}
            </Badge>
            <Button onClick={handleRun} disabled={running} size="sm">
              {running ? (
                <><Loader2 className="mr-1 h-4 w-4 animate-spin" /> Running...</>
              ) : (
                <><Play className="mr-1 h-4 w-4" /> Run</>
              )}
            </Button>
          </div>
        </div>

        {/* Schedule */}
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Clock className="h-4 w-4 text-primary" />
              Schedule
            </CardTitle>
          </CardHeader>
          <CardContent>
            {selectedWf.schedule ? (
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <code className="rounded bg-muted px-2 py-0.5 text-xs font-mono">
                      {selectedWf.schedule}
                    </code>
                    <Badge variant="outline" className="text-[10px] text-green-600 bg-green-500/10 border-green-200">
                      Active
                    </Badge>
                  </div>
                  {selectedWf.next_run_at && (
                    <p className="text-xs text-muted-foreground">
                      Next run: {formatDateTime(selectedWf.next_run_at)}
                    </p>
                  )}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleUnschedule}
                  disabled={scheduling}
                  className="text-xs text-red-500 hover:text-red-600"
                >
                  {scheduling ? <Loader2 className="h-3 w-3 animate-spin" /> : "Remove"}
                </Button>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Input
                  value={cronInput}
                  onChange={(e) => setCronInput(e.target.value)}
                  placeholder="e.g. 0 9 * * 1-5 (weekdays at 9am)"
                  className="h-8 flex-1 font-mono text-xs"
                  onKeyDown={(e) => e.key === "Enter" && handleSchedule()}
                />
                <Button
                  size="sm"
                  onClick={handleSchedule}
                  disabled={scheduling || !cronInput.trim()}
                  className="h-8 text-xs"
                >
                  {scheduling ? <Loader2 className="h-3 w-3 animate-spin" /> : "Set Schedule"}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Definition */}
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <FileText className="h-4 w-4 text-primary" />
              Workflow Definition
            </CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="max-h-80 overflow-auto rounded-lg bg-muted p-4 text-xs leading-relaxed">
              {JSON.stringify(selectedWf.definition, null, 2)}
            </pre>
          </CardContent>
        </Card>

        {/* Runs */}
        <Card className="border-border/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Play className="h-4 w-4 text-primary" />
              Run History
            </CardTitle>
          </CardHeader>
          <CardContent>
            {loadingRuns ? (
              <div className="flex items-center justify-center py-8 text-sm text-muted-foreground">
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Loading runs...
              </div>
            ) : runs.length === 0 ? (
              <div className="py-6 text-center text-sm text-muted-foreground">
                No runs yet. Click "Run" to execute this workflow.
              </div>
            ) : (
              <div className="space-y-3">
                {runs.map((run) => (
                  <div key={run.id} className="rounded-lg border border-border/50 p-4">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {statusIcon(run.status)}
                        <span className="text-sm font-medium capitalize">{run.status}</span>
                        <span className="text-xs text-muted-foreground">
                          {formatDateTime(run.started_at || run.created_at)}
                        </span>
                      </div>
                      {run.error && (
                        <span className="text-xs text-red-500">{run.error}</span>
                      )}
                    </div>

                    {/* Task traces */}
                    {run.task_runs && run.task_runs.length > 0 && (
                      <div className="mt-3 space-y-1.5">
                        {run.task_runs.map((tr) => (
                          <div key={tr.id} className="flex items-center gap-2 rounded-md bg-muted/50 px-3 py-1.5 text-xs">
                            {statusIcon(tr.status)}
                            <span className="font-medium">{tr.skill_name || tr.task_id}</span>
                            <span className="text-muted-foreground capitalize">({tr.task_type})</span>
                            <span className="text-muted-foreground">→ {tr.status}</span>
                            {tr.feedback && (
                              <span className="text-yellow-600">· "{tr.feedback}"</span>
                            )}

                            {/* Checkpoint actions */}
                            {tr.status === "waiting_for_approval" && (
                              <div className="ml-auto flex gap-1">
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="h-6 px-2 text-xs text-green-600"
                                  onClick={() => handleCheckpoint(run.id, tr.task_id, true)}
                                >
                                  Approve
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  className="h-6 px-2 text-xs text-red-600"
                                  onClick={() => handleCheckpoint(run.id, tr.task_id, false)}
                                >
                                  Reject
                                </Button>
                              </div>
                            )}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-foreground">Workflows</h1>
          <p className="mt-1 text-sm text-muted-foreground">
            Build and run multi-step automated pipelines
          </p>
        </div>
        <Button onClick={() => setCompilerOpen(true)}>
          <Sparkles className="mr-1.5 h-4 w-4" />
          New from Description
        </Button>
      </div>

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
          {error}
          <button onClick={() => setError(null)} className="ml-2 underline">Dismiss</button>
        </div>
      )}

      <Tabs defaultValue="workflows">
        <TabsList>
          <TabsTrigger value="workflows">My Workflows</TabsTrigger>
        </TabsList>

        <TabsContent value="workflows" className="mt-4">
          {isLoading ? (
            <div className="flex items-center justify-center py-12 text-sm text-muted-foreground">
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Loading workflows...
            </div>
          ) : workflows.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <Workflow className="mb-3 h-12 w-12 text-muted-foreground/30" />
              <p className="text-sm text-muted-foreground">No workflows yet</p>
              <p className="mt-1 text-xs text-muted-foreground/70">
                Click "New from Description" to describe a process and let the agent build it for you
              </p>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {workflows.map((wf) => (
                <Card
                  key={wf.id}
                  className="cursor-pointer border-border/50 transition-colors hover:border-primary/30"
                  onClick={() => openDetail(wf)}
                >
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <CardTitle className="text-sm font-semibold">{wf.name}</CardTitle>
                      <Badge className={statusBadge(wf.status)} variant="outline">
                        {wf.status}
                      </Badge>
                    </div>
                    <CardDescription className="text-xs line-clamp-2">
                      {wf.description || "No description"}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-3 text-xs text-muted-foreground">
                      <span>{wf.trigger}</span>
                      {wf.schedule && wf.next_run_at && (
                        <>
                          <span>·</span>
                          <span className="flex items-center gap-1">
                            <Clock className="h-3 w-3" />
                            Next: {formatDateTime(wf.next_run_at)}
                          </span>
                        </>
                      )}
                      <span>·</span>
                      <span>Updated {formatDate(wf.updated_at)}</span>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>

      {/* Compiler Dialog */}
      <Dialog open={compilerOpen} onOpenChange={(open) => {
        if (!open) { setCompilerOpen(false); setCompiledDef(null); setProcessDesc(""); setWfName("") }
      }}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Compile Workflow from Description</DialogTitle>
            <DialogDescription>
              Describe the process you want to automate. The AI agent will generate a structured workflow.
            </DialogDescription>
          </DialogHeader>

          {!compiledDef ? (
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">Workflow Name (optional)</label>
                <Input
                  value={wfName}
                  onChange={(e) => setWfName(e.target.value)}
                  placeholder="e.g. Weekly Report Pipeline"
                  className="mt-1"
                />
              </div>
              <div>
                <label className="text-sm font-medium">Process Description</label>
                <Textarea
                  value={processDesc}
                  onChange={(e) => setProcessDesc(e.target.value)}
                  placeholder="Describe the process step by step...&#10;&#10;e.g. First, research the topic using our Research skill. Then analyse the findings. Draft a report. Finally, create presentation slides and send for QA approval."
                  className="mt-1 min-h-[160px]"
                />
              </div>
              <Button
                onClick={handleCompile}
                disabled={compiling || !processDesc.trim()}
                className="w-full"
              >
                {compiling ? (
                  <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Compiling...</>
                ) : (
                  <><Sparkles className="mr-2 h-4 w-4" /> Compile Workflow</>
                )}
              </Button>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-5 w-5 text-green-600" />
                <span className="text-sm font-medium">Workflow compiled successfully</span>
              </div>

              <div>
                <label className="text-sm font-medium">Name</label>
                <Input
                  value={wfName}
                  onChange={(e) => setWfName(e.target.value)}
                  className="mt-1"
                />
              </div>

              <div>
                <label className="text-sm font-medium">Definition</label>
                <pre className="mt-1 max-h-60 overflow-auto rounded-lg bg-muted p-4 text-xs leading-relaxed">
                  {JSON.stringify(compiledDef, null, 2)}
                </pre>
              </div>

              <div className="flex gap-2">
                <Button
                  variant="outline"
                  onClick={() => { setCompiledDef(null); setWfName("") }}
                >
                  Back to Edit
                </Button>
                <Button onClick={handleSave} disabled={saving} className="ml-auto">
                  {saving ? (
                    <><Loader2 className="mr-2 h-4 w-4 animate-spin" /> Saving...</>
                  ) : (
                    <><Plus className="mr-2 h-4 w-4" /> Save Workflow</>
                  )}
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  )
}
