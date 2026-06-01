import { useAuth } from "@/contexts/AuthContext"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ArrowRight, Shield, Workflow, Bot, Clock, Lock, Server, Microscope, ChevronRight, Users, Sparkles, Database, GitBranch, Globe, HardDrive, Briefcase, MessageSquare, Layers } from "lucide-react"

const INTEGRATIONS = [
  { icon: Database, name: "Postgres", label: "Query & explore" },
  { icon: HardDrive, name: "Filesystem", label: "Read, write, search" },
  { icon: GitBranch, name: "Git / GitHub", label: "Code, issues, PRs" },
  { icon: Globe, name: "Web Fetch", label: "Research & data" },
  { icon: MessageSquare, name: "Email / Comms", label: "Coming soon" },
  { icon: Briefcase, name: "Office 365", label: "Coming soon" },
]

export function Landing() {
  const { isAuthenticated } = useAuth()

  return (
    <div className="flex min-h-screen flex-col bg-background">
      {/* ── Nav ────────────────────────────────────────────── */}
      <header className="sticky top-0 z-50 border-b border-border/40 bg-background/80 backdrop-blur-sm">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
          <div className="flex items-center gap-2">
            <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-primary shadow-sm">
              <span className="text-xs font-bold text-primary-foreground">F</span>
            </div>
            <span className="text-sm font-semibold">Flow</span>
          </div>
          <div className="flex items-center gap-4">
            <a href={isAuthenticated ? "/dashboard" : "/login"} className="text-xs text-muted-foreground hover:text-foreground transition-colors">
              {isAuthenticated ? "Dashboard" : "Sign In"}
            </a>
            {!isAuthenticated && (
              <Button size="sm" className="h-8 text-xs" asChild>
                <a href="/register">
                  Get Started
                  <ArrowRight className="ml-1 h-3 w-3" />
                </a>
              </Button>
            )}
          </div>
        </div>
      </header>

      <main className="flex-1">
        {/* ── Hero ──────────────────────────────────────────── */}
        <section className="relative overflow-hidden border-b border-border/40">
          <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top,_var(--tw-gradient-stops))] from-primary/5 via-transparent to-transparent pointer-events-none" />
          <div className="mx-auto max-w-6xl px-6 py-24 sm:py-32">
            <div className="mx-auto max-w-3xl text-center">
              <Badge variant="outline" className="mb-6 text-[10px] tracking-wider uppercase border-primary/20 text-primary bg-primary/5">
                Self-hosted · Audit-first · BYO-LLM
              </Badge>
              <h1 className="text-4xl font-bold tracking-tight text-foreground sm:text-5xl lg:text-6xl">
                One chat to run{" "}
                <span className="text-primary">your whole work</span>
              </h1>
              <p className="mt-4 text-base text-muted-foreground sm:text-lg max-w-2xl mx-auto">
                Your personal AI agent — for every employee. Describe what you need,
                it runs the process, pauses for approval, and delivers the result.
                Connected to your files, databases, code, and tools.
                All on your infrastructure. All audited immutably.
              </p>
              <div className="mt-8 flex items-center justify-center gap-4">
                <Button size="lg" className="h-11 text-sm" asChild>
                  <a href="/register">
                    Try Flow Free
                    <ArrowRight className="ml-1.5 h-4 w-4" />
                  </a>
                </Button>
                <Button size="lg" variant="outline" className="h-11 text-sm" asChild>
                  <a href="#features">
                    See How It Works
                  </a>
                </Button>
              </div>
              <p className="mt-6 text-xs text-muted-foreground/60">
                No credit card. Deploy on your own AWS. Free tier included.
              </p>
            </div>
          </div>
        </section>

        {/* ── Trust Bar ─────────────────────────────────────── */}
        <section className="border-b border-border/40 py-8">
          <div className="mx-auto max-w-6xl px-6">
            <div className="flex flex-wrap items-center justify-center gap-x-10 gap-y-4 text-xs text-muted-foreground/60">
              <span className="flex items-center gap-1.5"><Lock className="h-3.5 w-3.5 text-primary/60" /> Data sovereignty</span>
              <span className="flex items-center gap-1.5"><Shield className="h-3.5 w-3.5 text-primary/60" /> Immutable audit</span>
              <span className="flex items-center gap-1.5"><Server className="h-3.5 w-3.5 text-primary/60" /> Self-hosted</span>
              <span className="flex items-center gap-1.5"><Microscope className="h-3.5 w-3.5 text-primary/60" /> BYO-LLM</span>
              <span className="flex items-center gap-1.5"><Users className="h-3.5 w-3.5 text-primary/60" /> Multi-tenant</span>
            </div>
          </div>
        </section>

        {/* ── Features ──────────────────────────────────────── */}
        <section id="features" className="border-b border-border/40 py-20 sm:py-28">
          <div className="mx-auto max-w-6xl px-6">
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                Everything you need to deploy AI agents at scale
              </h2>
              <p className="mt-3 text-sm text-muted-foreground">
                Built for government and enterprise from day one.
              </p>
            </div>

            <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
              {[
                {
                  icon: Bot,
                  title: "Your Personal Agent",
                  desc: "Every employee gets their own AI assistant. Chat to it like you chat to me — it handles the rest.",
                },
                {
                  icon: Sparkles,
                  title: "Build Skills from Chat",
                  desc: '"Save this as a skill." Your agent remembers how. Share it with your team or the whole organisation.',
                },
                {
                  icon: Workflow,
                  title: "Describe. Compile. Run.",
                  desc: "Describe a process in plain English. The agent builds a multi-step workflow with dependencies and human checkpoints — no coding required.",
                },
                {
                  icon: Layers,
                  title: "Human-in-the-Loop",
                  desc: "Workflows pause at decision points. Approve or reject right in the chat. Every action logged immutably. Nobody gets fired by a script.",
                },
                {
                  icon: Clock,
                  title: "Schedule Anything",
                  desc: '"Run the compliance report every Monday at 9am." Set a cron schedule. Reports land in your inbox. Automatically.',
                },
                {
                  icon: MessageSquare,
                  title: "One Interface for Everything",
                  desc: "Email, files, databases, GitHub, web research — all from one chat. The agent fetches what you need, runs what you ask, delivers the result.",
                },
              ].map((f, i) => (
                <div key={i} className="group rounded-xl border border-border/50 bg-card/50 p-6 transition-all hover:border-primary/30 hover:bg-card">
                  <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <f.icon className="h-5 w-5 text-primary" />
                  </div>
                  <h3 className="mb-2 text-sm font-semibold text-foreground">{f.title}</h3>
                  <p className="text-xs leading-relaxed text-muted-foreground">{f.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Integrations ──────────────────────────────────── */}
        <section className="border-b border-border/40 py-20 sm:py-28">
          <div className="mx-auto max-w-6xl px-6">
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                Connected to your tools
              </h2>
              <p className="mt-3 text-sm text-muted-foreground">
                Pre-built integrations — your agent uses them like you do.
              </p>
            </div>

            <div className="mt-12 grid gap-6 sm:grid-cols-3 lg:grid-cols-6">
              {INTEGRATIONS.map((item, i) => (
                <div key={i} className="flex flex-col items-center gap-3 rounded-xl border border-border/50 bg-card/50 p-6 text-center transition-all hover:border-primary/30 hover:bg-card">
                  <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-primary/10">
                    <item.icon className="h-5 w-5 text-primary" />
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-foreground">{item.name}</p>
                    <p className="text-[10px] text-muted-foreground/60">{item.label}</p>
                  </div>
                </div>
              ))}
            </div>

            <div className="mt-8 text-center">
              <p className="text-xs text-muted-foreground/60">
                Built on the Model Context Protocol (MCP) — extend with anything.
                Build once, own forever. No per-seat pricing on connectors.
              </p>
            </div>
          </div>
        </section>

        {/* ── How it Works ──────────────────────────────────── */}
        <section className="border-b border-border/40 py-20 sm:py-28">
          <div className="mx-auto max-w-6xl px-6">
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                Describe. Compile. Deliver.
              </h2>
              <p className="mt-3 text-sm text-muted-foreground">
                Three steps from idea to result.
              </p>
            </div>

            <div className="mt-16 grid gap-8 sm:grid-cols-3">
              {[
                {
                  step: "01",
                  title: "Describe",
                  desc: '"Run the weekly compliance report — research the topic, draft the findings, then ask me to approve before sending." The agent understands intent, not just keywords.',
                },
                {
                  step: "02",
                  title: "Review & Approve",
                  desc: "The agent builds the workflow, executes step-by-step, and pauses when it needs a decision. Approve or reject right in the chat — no tab-switching, no context lost.",
                },
                {
                  step: "03",
                  title: "Deliver & Log",
                  desc: "Documents, reports, decisions — the result lands in your chat. Every action is logged immutably with hash-chain integrity. Fully replayable for audit.",
                },
              ].map((s, i) => (
                <div key={i} className="relative text-center">
                  <div className="mb-4 inline-flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 text-sm font-semibold text-primary">
                    {s.step}
                  </div>
                  <h3 className="mb-2 text-sm font-semibold text-foreground">{s.title}</h3>
                  <p className="text-xs leading-relaxed text-muted-foreground max-w-xs mx-auto">{s.desc}</p>
                  {i < 2 && (
                    <ChevronRight className="hidden sm:absolute sm:right-0 sm:top-5 sm:block h-5 w-5 text-muted-foreground/20" />
                  )}
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── Governance ────────────────────────────────────── */}
        <section className="border-b border-border/40 py-20 sm:py-28">
          <div className="mx-auto max-w-6xl px-6">
            <div className="mx-auto max-w-2xl text-center">
              <Badge variant="outline" className="mb-4 text-[10px] tracking-wider uppercase border-primary/20 text-primary bg-primary/5">
                Governance First
              </Badge>
              <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                Built for the most regulated environments
              </h2>
            </div>

            <div className="mt-12 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[
                { title: "Immutable Audit", desc: "Every action — every tool call, approval, rejection — logged with hash-chain integrity. Tamper-evident. Fully replayable for compliance." },
                { title: "Data Isolation", desc: "Enterprise-grade tenant separation. Employee A cannot see Employee B's data, workflows, or conversations." },
                { title: "Least Privilege", desc: "Your agent inherits your permissions. No god-mode account. No standing access to systems." },
                { title: "BYO-LLM", desc: "Bring your own model key. Works with OpenAI, Claude, DeepSeek, or any OpenAI-compatible endpoint. Data never leaves your trust boundary." },
              ].map((g, i) => (
                <div key={i} className="rounded-xl border border-border/50 bg-card/50 p-5">
                  <h3 className="mb-1.5 text-sm font-semibold text-foreground">{g.title}</h3>
                  <p className="text-xs leading-relaxed text-muted-foreground">{g.desc}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* ── CTA ───────────────────────────────────────────── */}
        <section className="py-20 sm:py-28">
          <div className="mx-auto max-w-6xl px-6">
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                Ready to deploy?
              </h2>
              <p className="mt-3 text-sm text-muted-foreground">
                Self-hosted on your AWS. Free tier to get started. Enterprise pricing for scale.
              </p>
              <div className="mt-8 flex items-center justify-center gap-4">
                <Button size="lg" className="h-11 text-sm" asChild>
                  <a href="/register">
                    Start Free
                    <ArrowRight className="ml-1.5 h-4 w-4" />
                  </a>
                </Button>
                <Button size="lg" variant="outline" className="h-11 text-sm">
                  Talk to Us
                </Button>
              </div>
            </div>
          </div>
        </section>
      </main>

      {/* ── Footer ──────────────────────────────────────────── */}
      <footer className="border-t border-border/40 py-8">
        <div className="mx-auto max-w-6xl px-6">
          <div className="flex flex-col items-center justify-between gap-4 sm:flex-row">
            <div className="flex items-center gap-2">
              <div className="flex h-5 w-5 items-center justify-center rounded bg-primary/10">
                <span className="text-[8px] font-bold text-primary">F</span>
              </div>
              <span className="text-xs text-muted-foreground">Flow — Self-hosted AI Agent Platform</span>
            </div>
            <div className="flex items-center gap-6 text-[10px] text-muted-foreground/60">
              <span>Built by Taran Croxton</span>
              <span>© 2026</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}
