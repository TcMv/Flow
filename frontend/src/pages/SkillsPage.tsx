import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs"
import { SkillBuilderDialog } from "@/components/SkillBuilderDialog"
import { Wand2, Search, User, Globe, ExternalLink, Clock } from "lucide-react"

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000"

interface Skill {
  id: string
  name: string
  description: string
  trigger_command: string | null
  definition_str: string
  owner_id: string
  owner_name: string | null
  visibility: string
  status: string
  created_at: string
  updated_at: string
}

function formatDate(iso: string): string {
  try {
    const d = new Date(iso)
    return d.toLocaleDateString([], { month: "short", day: "numeric", year: "numeric" })
  } catch {
    return ""
  }
}

function statusBadge(status: string) {
  const variants: Record<string, string> = {
    active: "bg-green-500/10 text-green-600 border-green-200",
    under_review: "bg-yellow-500/10 text-yellow-600 border-yellow-200",
    approved: "bg-blue-500/10 text-blue-600 border-blue-200",
    rejected: "bg-red-500/10 text-red-600 border-red-200",
  }
  return variants[status] ?? "bg-gray-500/10 text-gray-600 border-gray-200"
}

export function SkillsPage() {
  const [skills, setSkills] = useState<Skill[]>([])
  const [marketplaceSkills, setMarketplaceSkills] = useState<Skill[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [createOpen, setCreateOpen] = useState(false)
  const [searchQuery, setSearchQuery] = useState("")

  useEffect(() => {
    loadSkills()
    loadMarketplace()
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
      try {
        const body = await res.json()
        if (body.detail) detail = body.detail
      } catch {
        // ignore
      }
      throw new Error(detail)
    }
    if (res.status === 204) return undefined as T
    return res.json() as Promise<T>
  }

  async function loadSkills() {
    setIsLoading(true)
    setError(null)
    try {
      const data = await request<{ skills: Skill[] }>("/api/skills?scope=mine")
      setSkills(data.skills)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load skills")
    } finally {
      setIsLoading(false)
    }
  }

  async function loadMarketplace() {
    try {
      const data = await request<{ skills: Skill[] }>("/api/skills?scope=marketplace")
      setMarketplaceSkills(data.skills)
    } catch {
      // Non-critical
    }
  }

  async function submitToMarketplace(skillId: string) {
    try {
      await request(`/api/skills/${skillId}/submit`, { method: "POST" })
      loadSkills()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to submit")
    }
  }

  async function deleteSkill(skillId: string) {
    try {
      await request(`/api/skills/${skillId}`, { method: "DELETE" })
      loadSkills()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to delete")
    }
  }

  const filteredSkills = skills.filter(
    (s) =>
      s.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      s.description.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Skills</h1>
          <p className="text-sm text-muted-foreground">
            Create reusable capabilities via chat or browse the marketplace
          </p>
        </div>
        <Button onClick={() => setCreateOpen(true)} className="gap-2">
          <Wand2 className="h-4 w-4" />
          Build Skill
        </Button>
        <SkillBuilderDialog
          open={createOpen}
          onOpenChange={setCreateOpen}
          onSave={async (data) => {
            setError(null)
            await request("/api/skills", {
              method: "POST",
              body: JSON.stringify({
                name: data.name,
                description: data.description,
                trigger_command: data.triggerCommand || null,
                definition_str: data.definitionStr,
              }),
            })
            loadSkills()
          }}
        />
      </div>

      {/* Search */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          className="pl-9"
          placeholder="Search your skills..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
        />
      </div>

      {/* Error */}
      {error && (
        <div className="rounded-md bg-destructive/10 px-4 py-2 text-sm text-destructive">
          {error}
          <button onClick={() => setError(null)} className="ml-2 underline hover:no-underline">
            Dismiss
          </button>
        </div>
      )}

      {/* Tabs */}
      <Tabs defaultValue="my-skills">
        <TabsList>
          <TabsTrigger value="my-skills" className="gap-2">
            <User className="h-4 w-4" />
            My Skills ({skills.length})
          </TabsTrigger>
          <TabsTrigger value="marketplace" className="gap-2">
            <Globe className="h-4 w-4" />
            Marketplace ({marketplaceSkills.length})
          </TabsTrigger>
        </TabsList>

        <TabsContent value="my-skills" className="space-y-4">
          {isLoading ? (
            <div className="py-12 text-center text-sm text-muted-foreground">Loading skills...</div>
          ) : filteredSkills.length === 0 ? (
            <div className="py-12 text-center">
              <Wand2 className="mx-auto mb-4 h-10 w-10 text-muted-foreground/30" />
              <p className="text-sm text-muted-foreground">
                {searchQuery
                  ? "No skills match your search"
                  : "No skills yet. Create one through chat or use the button above."}
              </p>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {filteredSkills.map((skill) => (
                <Card key={skill.id} className="group relative">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="min-w-0 flex-1">
                        <CardTitle className="text-base">{skill.name}</CardTitle>
                        {skill.trigger_command && (
                          <code className="mt-0.5 inline-block rounded bg-muted px-1.5 py-0.5 text-xs text-muted-foreground">
                            {skill.trigger_command}
                          </code>
                        )}
                      </div>
                      <Badge className={`ml-2 border text-[10px] ${statusBadge(skill.status)}`} variant="outline">
                        {skill.status}
                      </Badge>
                    </div>
                    <CardDescription className="mt-1 line-clamp-2 text-xs">
                      {skill.description || "No description"}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
                      <span className="flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatDate(skill.updated_at)}
                      </span>
                      <Badge variant="outline" className="text-[10px]">
                        {skill.visibility}
                      </Badge>
                    </div>
                    {/* Hover actions */}
                    <div className="mt-3 flex gap-2 opacity-0 transition-opacity group-hover:opacity-100">
                      {skill.visibility === "private" && skill.status === "active" && (
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-7 text-xs"
                          onClick={() => submitToMarketplace(skill.id)}
                        >
                          <Globe className="mr-1 h-3 w-3" />
                          Submit to Marketplace
                        </Button>
                      )}
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 text-xs text-destructive hover:text-destructive"
                        onClick={() => deleteSkill(skill.id)}
                      >
                        Delete
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>

        <TabsContent value="marketplace" className="space-y-4">
          {marketplaceSkills.length === 0 ? (
            <div className="py-12 text-center">
              <Globe className="mx-auto mb-4 h-10 w-10 text-muted-foreground/30" />
              <p className="text-sm text-muted-foreground">
                No skills in the marketplace yet. Submit one from your skills.
              </p>
            </div>
          ) : (
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
              {marketplaceSkills.map((skill) => (
                <Card key={skill.id}>
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="min-w-0 flex-1">
                        <CardTitle className="text-base">{skill.name}</CardTitle>
                        {skill.trigger_command && (
                          <code className="mt-0.5 inline-block rounded bg-muted px-1.5 py-0.5 text-xs text-muted-foreground">
                            {skill.trigger_command}
                          </code>
                        )}
                      </div>
                      <ExternalLink className="ml-2 h-4 w-4 text-muted-foreground" />
                    </div>
                    <CardDescription className="mt-1 line-clamp-2 text-xs">
                      {skill.description || "No description"}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center gap-3 text-[10px] text-muted-foreground">
                      {skill.owner_name && (
                        <span className="flex items-center gap-1">
                          <User className="h-3 w-3" />
                          {skill.owner_name}
                        </span>
                      )}
                      <Badge variant="outline" className="text-[10px]">
                        {skill.status}
                      </Badge>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </TabsContent>
      </Tabs>
    </div>
  )
}
