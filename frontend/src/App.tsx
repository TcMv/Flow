import { BrowserRouter, Routes, Route } from "react-router-dom"
import { AuthProvider } from "@/contexts/AuthContext"
import { ProtectedRoute } from "@/components/ProtectedRoute"
import { Toaster } from "@/components/ui/toaster"
import { Landing } from "@/pages/Landing"
import { Login } from "@/pages/Login"
import { Register } from "@/pages/Register"
import { DashboardLayout } from "@/pages/DashboardLayout"
import { DashboardHome } from "@/pages/DashboardHome"
import { ChatPage } from "@/pages/ChatPage"
import { SkillsPage } from "@/pages/SkillsPage"
import { WorkflowsPage } from "@/pages/WorkflowsPage"
import {
  KnowledgePage,
  SettingsPage,
} from "@/pages/PlaceholderPages"

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected dashboard routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<DashboardLayout />}>
              <Route path="/dashboard" element={<DashboardHome />} />
              <Route path="/dashboard/skills" element={<SkillsPage />} />
              <Route path="/dashboard/chat" element={<ChatPage />} />
              <Route path="/dashboard/workflows" element={<WorkflowsPage />} />
              <Route path="/dashboard/knowledge" element={<KnowledgePage />} />
              <Route path="/dashboard/settings" element={<SettingsPage />} />
            </Route>
          </Route>
        </Routes>
        <Toaster />
      </AuthProvider>
    </BrowserRouter>
  )
}
