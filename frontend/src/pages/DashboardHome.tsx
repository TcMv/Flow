import { useAuth } from "@/contexts/AuthContext"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Bot, Activity, Users, Cpu } from "lucide-react"

export function DashboardHome() {
  const { user } = useAuth()

  const stats = [
    { label: "Active Agents", value: "0", icon: Bot },
    { label: "Total Runs", value: "0", icon: Activity },
    { label: "Team Members", value: "1", icon: Users },
    { label: "System Health", value: "Healthy", icon: Cpu },
  ]

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-foreground">Dashboard</h1>
        <p className="mt-1 text-sm text-muted-foreground">
          Welcome back, {user?.name ?? "User"}.
        </p>
      </div>

      {/* Stats grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
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
                <p className="text-sm font-medium">Create an Agent</p>
                <p className="text-xs text-muted-foreground">Deploy a new AI agent</p>
              </div>
            </div>
            <Badge variant="secondary" className="text-xs">Coming soon</Badge>
          </div>
          <div className="flex items-center justify-between rounded-lg border border-border/50 px-4 py-3">
            <div className="flex items-center gap-3">
              <Activity className="h-5 w-5 text-primary" />
              <div>
                <p className="text-sm font-medium">View Activity Log</p>
                <p className="text-xs text-muted-foreground">Monitor agent runs and events</p>
              </div>
            </div>
            <Badge variant="secondary" className="text-xs">Coming soon</Badge>
          </div>
        </CardContent>
      </Card>

      {/* System status */}
      <Card className="border-border/50">
        <CardHeader>
          <CardTitle className="text-base">System Status</CardTitle>
        </CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          <p>Flow is running in development mode. Connect to the backend API to enable full functionality.</p>
          <p className="mt-2 text-xs text-muted-foreground/60">
            API Endpoint: http://localhost:8000
          </p>
        </CardContent>
      </Card>
    </div>
  )
}
