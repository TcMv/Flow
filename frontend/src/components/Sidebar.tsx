import { NavLink } from "react-router-dom"
import {
  LayoutDashboard,
  Bot,
  MessagesSquare,
  Settings,
  LogOut,
  Workflow,
  Database,
} from "lucide-react"
import { cn } from "@/lib/utils"
import { useAuth } from "@/contexts/AuthContext"
import { Button } from "@/components/ui/button"

const navItems = [
  { to: "/dashboard", icon: LayoutDashboard, label: "Dashboard" },
  { to: "/dashboard/agents", icon: Bot, label: "Agents" },
  { to: "/dashboard/chat", icon: MessagesSquare, label: "Chat" },
  { to: "/dashboard/workflows", icon: Workflow, label: "Workflows" },
  { to: "/dashboard/knowledge", icon: Database, label: "Knowledge" },
  { to: "/dashboard/settings", icon: Settings, label: "Settings" },
]

export function Sidebar() {
  const { logout } = useAuth()

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-60 flex-col border-r bg-sidebar-background">
      {/* Brand */}
      <div className="flex h-14 items-center gap-2 border-b border-border px-6">
        <div className="flex h-7 w-7 items-center justify-center rounded-md bg-primary text-xs font-bold text-primary-foreground">
          F
        </div>
        <span className="text-sm font-semibold tracking-wide text-sidebar-foreground">
          Flow
        </span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === "/dashboard"}
            className={({ isActive }) =>
              cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-sidebar-accent text-sidebar-foreground"
                  : "text-sidebar-foreground/60 hover:bg-sidebar-accent hover:text-sidebar-foreground"
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Logout */}
      <div className="border-t border-border p-3">
        <Button
          variant="ghost"
          className="w-full justify-start gap-3 text-sidebar-foreground/60 hover:text-sidebar-foreground"
          onClick={logout}
        >
          <LogOut className="h-4 w-4" />
          Logout
        </Button>
      </div>
    </aside>
  )
}
