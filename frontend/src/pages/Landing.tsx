import { useAuth } from "@/contexts/AuthContext"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { ArrowRight, Shield, Workflow, Bot, Clock, Lock, Server, Microscope, ChevronRight, Users, Sparkles } from "lucide-react"

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
                Every employee gets{" "}
                <span className="text-primary">their own AI agent</span>
              </h1>
              <p className="mt-4 text-base text-muted-foreground sm:text-lg max-w-2xl mx-auto">
                A platform where anyone can build skills, share them with their team,
                and describe a process — and their agent designs, runs, and delivers it.
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
                  title: "Personal Agents",
                  desc: "Every employee gets their own AI assistant. Personalised, skilled, and connected to the tools they need.",
                },
                {
                  icon: Sparkles,
                  title: "Build Skills from Chat",
                  desc: "Tell your agent what you need. It saves it as a reusable skill. Share it with your team or the whole org.",
                },
                {
                  icon: Workflow,
                  title: "Process → Workflow",
                  desc: "Upload a process description and the agent compiles it into a structured multi-step workflow with human checkpoints.",
                },
                {
                  icon: Clock,
                  title: "Scheduled Execution",
                  desc: "Set workflows to run on a cron schedule. Daily reports, compliance checks, data syncs — all automatic.",
                },
                {
                  icon: Shield,
                  title: "Human-in-the-Loop",
                  desc: "Every consequential action pauses for approval. Nobody gets fired by an AI. Audit trail on everything.",
                },
                {
                  icon: Server,
                  title: "Your Infra, Your Data",
                  desc: "Deploy on your own AWS. Bring your own LLM key. No data ever leaves your perimeter.",
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

        {/* ── How it Works ──────────────────────────────────── */}
        <section className="border-b border-border/40 py-20 sm:py-28">
          <div className="mx-auto max-w-6xl px-6">
            <div className="mx-auto max-w-2xl text-center">
              <h2 className="text-3xl font-bold tracking-tight text-foreground sm:text-4xl">
                Describe. Compile. Run.
              </h2>
              <p className="mt-3 text-sm text-muted-foreground">
                Three steps from process to automated delivery.
              </p>
            </div>

            <div className="mt-16 grid gap-8 sm:grid-cols-3">
              {[
                {
                  step: "01",
                  title: "Describe",
                  desc: "Upload a process document or describe what you need in plain English. The agent understands intent.",
                },
                {
                  step: "02",
                  title: "Compile & Review",
                  desc: "The agent generates a structured workflow with tasks, dependencies, and human checkpoints. You review and approve the design.",
                },
                {
                  step: "03",
                  title: "Run & Audit",
                  desc: "Execute on demand or schedule it. Every step logged immutably. Full replay capability for compliance.",
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
                { title: "Immutable Audit", desc: "Every action logged with hash chain. Tamper-evident. Full replay." },
                { title: "Data Isolation", desc: "Tenant-level separation. Employee A cannot see Employee B's data." },
                { title: "Least Privilege", desc: "Agent inherits user permissions. No god-mode agent account." },
                { title: "BYO-LLM", desc: "Bring your own model. Works with OpenAI, Claude, DeepSeek, or custom." },
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
