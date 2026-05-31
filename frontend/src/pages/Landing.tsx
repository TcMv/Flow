import { useAuth } from "@/contexts/AuthContext"
import { Button } from "@/components/ui/button"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Bot, Workflow, MessagesSquare, ArrowRight } from "lucide-react"

export function Landing() {
  const { isAuthenticated } = useAuth()

  return (
    <div className="flex min-h-screen flex-col items-center justify-center bg-background">
      <div className="mx-auto flex max-w-2xl flex-col items-center px-6 text-center">
        {/* Logo */}
        <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-2xl bg-primary shadow-lg shadow-primary/20">
          <span className="text-2xl font-bold text-primary-foreground">F</span>
        </div>

        {/* Tagline */}
        <h1 className="mb-3 text-4xl font-bold tracking-tight text-foreground sm:text-5xl">
          Flow
        </h1>
        <p className="mb-2 text-lg text-muted-foreground">
          Self-hosted AI agent platform for the enterprise.
        </p>
        <p className="mb-8 text-sm text-muted-foreground/70">
          Deploy, manage, and orchestrate intelligent agents — on your infrastructure.
        </p>

        {/* CTA */}
        <div className="flex gap-4">
          <Button size="lg" asChild>
            <a href={isAuthenticated ? "/dashboard" : "/login"}>
              {isAuthenticated ? "Go to Dashboard" : "Sign In"}
              <ArrowRight className="ml-2 h-4 w-4" />
            </a>
          </Button>
          <Button size="lg" variant="outline" disabled>
            View Docs
          </Button>
        </div>

        {/* Feature highlights */}
        <div className="mt-16 grid gap-4 sm:grid-cols-3">
          <Card className="border-border/50 bg-card/50">
            <CardContent className="flex flex-col items-center gap-3 p-6">
              <Bot className="h-8 w-8 text-primary" />
              <h3 className="text-sm font-semibold">AI Agents</h3>
              <p className="text-xs text-muted-foreground text-center">
                Deploy custom agents with the tools they need.
              </p>
            </CardContent>
          </Card>
          <Card className="border-border/50 bg-card/50">
            <CardContent className="flex flex-col items-center gap-3 p-6">
              <Workflow className="h-8 w-8 text-primary" />
              <h3 className="text-sm font-semibold">Workflows</h3>
              <p className="text-xs text-muted-foreground text-center">
                Chain agents into automated multi-step pipelines.
              </p>
            </CardContent>
          </Card>
          <Card className="border-border/50 bg-card/50">
            <CardContent className="flex flex-col items-center gap-3 p-6">
              <MessagesSquare className="h-8 w-8 text-primary" />
              <h3 className="text-sm font-semibold">Chat Interface</h3>
              <p className="text-xs text-muted-foreground text-center">
                Interact with agents through a real-time chat UI.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Footer badge */}
        <Badge variant="outline" className="mt-12 text-xs text-muted-foreground/60">
          Self-hosted · Open-source · Enterprise-grade
        </Badge>
      </div>
    </div>
  )
}
