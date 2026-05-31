import { Sidebar } from "@/components/Sidebar"
import { Outlet } from "react-router-dom"

export function DashboardLayout() {
  return (
    <div className="flex min-h-screen bg-background">
      <Sidebar />
      <main className="ml-60 flex-1 overflow-auto">
        <div className="mx-auto max-w-7xl px-8 py-8">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
