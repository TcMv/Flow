import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Bot } from "lucide-react"

export function AgentsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Agents</h1>
        <p className="mt-1 text-sm text-muted-foreground">Manage your AI agents</p>
      </div>
      <Card className="border-border/50">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Bot className="h-5 w-5 text-primary" />
            Agent Hub
          </CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Create, configure, and deploy AI agents. This page will be built out in Phase 1.
        </CardContent>
      </Card>
    </div>
  )
}

export function ChatPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Chat</h1>
        <p className="mt-1 text-sm text-muted-foreground">Interact with your agents</p>
      </div>
      <Card className="border-border/50">
        <CardHeader>
          <CardTitle className="text-base">Chat Interface</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Real-time chat with agents. This page will be built out in Phase 1.
        </CardContent>
      </Card>
    </div>
  )
}

export function WorkflowsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Workflows</h1>
        <p className="mt-1 text-sm text-muted-foreground">Automate multi-step pipelines</p>
      </div>
      <Card className="border-border/50">
        <CardHeader>
          <CardTitle className="text-base">Workflow Builder</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Chain agents into automated pipelines. This page will be built out in Phase 1.
        </CardContent>
      </Card>
    </div>
  )
}

export function KnowledgePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Knowledge</h1>
        <p className="mt-1 text-sm text-muted-foreground">Manage knowledge bases</p>
      </div>
      <Card className="border-border/50">
        <CardHeader>
          <CardTitle className="text-base">Knowledge Base</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Upload documents and manage data sources. This page will be built out in Phase 1.
        </CardContent>
      </Card>
    </div>
  )
}

export function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-foreground">Settings</h1>
        <p className="mt-1 text-sm text-muted-foreground">Configure your Flow instance</p>
      </div>
      <Card className="border-border/50">
        <CardHeader>
          <CardTitle className="text-base">Instance Settings</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Manage API keys, team members, and system preferences. This page will be built out in Phase 1.
        </CardContent>
      </Card>
    </div>
  )
}
