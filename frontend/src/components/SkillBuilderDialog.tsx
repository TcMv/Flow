import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import {
  ChevronLeft,
  ChevronRight,
  Wand2,
  Plus,
  Trash2,
  Bot,
  Search,
  FileText,
  Image,
  MessageSquare,
  CheckCircle2,
  ArrowDown,
} from "lucide-react"

interface SkillStep {
  id: string
  type: "search" | "analyze" | "draft" | "ask_user" | "generate_image" | "custom"
  description: string
  details: string
}

interface SkillInput {
  name: string
  type: "string" | "text" | "number"
  description: string
}

const STEP_TYPES = [
  { id: "search" as const, label: "Search", icon: Search, color: "bg-blue-500/10 text-blue-600" },
  { id: "analyze" as const, label: "Analyze", icon: Bot, color: "bg-purple-500/10 text-purple-600" },
  { id: "draft" as const, label: "Draft", icon: FileText, color: "bg-green-500/10 text-green-600" },
  { id: "generate_image" as const, label: "Generate Image", icon: Image, color: "bg-pink-500/10 text-pink-600" },
  { id: "ask_user" as const, label: "Ask User", icon: MessageSquare, color: "bg-amber-500/10 text-amber-600" },
  { id: "custom" as const, label: "Custom", icon: Wand2, color: "bg-gray-500/10 text-gray-600" },
]

function getStepIcon(type: string) {
  return STEP_TYPES.find((s) => s.id === type)?.icon ?? Wand2
}

function getStepColor(type: string) {
  return STEP_TYPES.find((s) => s.id === type)?.color ?? "bg-gray-500/10 text-gray-600"
}

function generateDefinition(steps: SkillStep[], inputs: SkillInput[], clarifyQuestions: string): string {
  const lines: string[] = []
  lines.push("## Skill Steps")
  steps.forEach((step, i) => {
    lines.push(`${i + 1}. **${step.type.replace("_", " ")}**: ${step.description}`)
    if (step.details) lines.push(`   ${step.details}`)
  })
  if (inputs.length > 0) {
    lines.push("")
    lines.push("## Inputs")
    inputs.forEach((input) => {
      lines.push(`- ${input.name} (${input.type}): ${input.description}`)
    })
  }
  if (clarifyQuestions) {
    lines.push("")
    lines.push("## Clarifying Questions")
    lines.push(clarifyQuestions)
  }
  return lines.join("\n")
}

interface SkillBuilderDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  onSave: (data: {
    name: string
    description: string
    triggerCommand: string
    definitionStr: string
  }) => Promise<void>
}

export function SkillBuilderDialog({ open, onOpenChange, onSave }: SkillBuilderDialogProps) {
  const [step, setStep] = useState(1)
  const [saving, setSaving] = useState(false)

  // Step 1: Basic info
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [triggerCommand, setTriggerCommand] = useState("")

  // Step 2: Steps
  const [steps, setSteps] = useState<SkillStep[]>([
    { id: crypto.randomUUID(), type: "search", description: "", details: "" },
  ])

  // Step 3: Inputs & clarify
  const [inputs, setInputs] = useState<SkillInput[]>([])
  const [clarifyQuestions, setClarifyQuestions] = useState("")

  function resetForm() {
    setStep(1)
    setName("")
    setDescription("")
    setTriggerCommand("")
    setSteps([{ id: crypto.randomUUID(), type: "search", description: "", details: "" }])
    setInputs([])
    setClarifyQuestions("")
    setSaving(false)
  }

  function addStep() {
    const newStep: SkillStep = {
      id: crypto.randomUUID(),
      type: "custom",
      description: "",
      details: "",
    }
    // Insert before the last step (before deliver)
    setSteps([...steps.slice(0, -1), newStep, ...steps.slice(-1)])
  }

  function removeStep(id: string) {
    if (steps.length <= 1) return
    setSteps(steps.filter((s) => s.id !== id))
  }

  function updateStep(id: string, updates: Partial<SkillStep>) {
    setSteps(steps.map((s) => (s.id === id ? { ...s, ...updates } : s)))
  }

  function moveStep(index: number, direction: "up" | "down") {
    const newSteps = [...steps]
    const target = direction === "up" ? index - 1 : index + 1
    if (target < 0 || target >= newSteps.length) return
    // Don't move the Deliver step
    if (index === newSteps.length - 1 || target === newSteps.length - 1) return
    ;[newSteps[index], newSteps[target]] = [newSteps[target], newSteps[index]]
    setSteps(newSteps)
  }

  function addInput() {
    setInputs([...inputs, { name: "", type: "string", description: "" }])
  }

  function updateInput(index: number, updates: Partial<SkillInput>) {
    setInputs(inputs.map((i, idx) => (idx === index ? { ...i, ...updates } : i)))
  }

  function removeInput(index: number) {
    setInputs(inputs.filter((_, i) => i !== index))
  }

  async function handleSave() {
    if (!name.trim()) return
    setSaving(true)
    try {
      // Always append a final "Deliver" step
      const finalSteps = [...steps, { id: crypto.randomUUID(), type: "custom" as const, description: "Deliver the final output to the user", details: "Format and present the result clearly." }]

      const definitionStr = generateDefinition(finalSteps, inputs, clarifyQuestions)
      await onSave({
        name: name.trim(),
        description: description.trim(),
        triggerCommand: triggerCommand.trim() || "",
        definitionStr,
      })
      resetForm()
      onOpenChange(false)
    } catch {
      // Error handled by parent
    } finally {
      setSaving(false)
    }
  }

  function canProceed(): boolean {
    switch (step) {
      case 1:
        return name.trim().length > 0
      case 2:
        return steps.every((s) => s.description.trim().length > 0)
      default:
        return true
    }
  }

  return (
    <Dialog
      open={open}
      onOpenChange={(v) => {
        if (!v) resetForm()
        onOpenChange(v)
      }}
    >
      <DialogContent className="sm:max-w-[600px] max-h-[85vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Wand2 className="h-5 w-5 text-primary" />
            Build a Skill
          </DialogTitle>
          <DialogDescription>
            {step === 1 && "Give your skill a name and trigger command"}
            {step === 2 && "Define what your skill does, step by step"}
            {step === 3 && "Configure inputs and clarifying questions"}
            {step === 4 && "Review your skill before saving"}
          </DialogDescription>
        </DialogHeader>

        {/* Progress */}
        <div className="flex items-center gap-1.5 px-1">
          {[1, 2, 3, 4].map((s) => (
            <div key={s} className="flex items-center gap-1.5 flex-1">
              <div
                className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[10px] font-medium ${
                  s < step
                    ? "bg-primary text-primary-foreground"
                    : s === step
                      ? "bg-primary/20 text-primary ring-1 ring-primary"
                      : "bg-muted text-muted-foreground"
                }`}
              >
                {s < step ? <CheckCircle2 className="h-3.5 w-3.5" /> : s}
              </div>
              <div className={`h-px flex-1 ${s < step ? "bg-primary" : "bg-border"}`} />
            </div>
          ))}
        </div>

        {/* Step 1: Basic Info */}
        {step === 1 && (
          <div className="space-y-4 py-4">
            <div>
              <label className="text-sm font-medium">Skill Name *</label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Policy Brief"
                className="mt-1.5"
                autoFocus
              />
              <p className="mt-1 text-xs text-muted-foreground">A short, memorable name</p>
            </div>
            <div>
              <label className="text-sm font-medium">Description</label>
              <Input
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="What does this skill do?"
                className="mt-1.5"
              />
            </div>
            <div>
              <label className="text-sm font-medium">Trigger Command</label>
              <Input
                value={triggerCommand}
                onChange={(e) => setTriggerCommand(e.target.value.startsWith("/") ? e.target.value : `/${e.target.value}`)}
                placeholder="/brief"
                className="mt-1.5 font-mono"
              />
              <p className="mt-1 text-xs text-muted-foreground">
                Type <code className="rounded bg-muted px-1">/command</code> in chat to invoke this skill
              </p>
            </div>
          </div>
        )}

        {/* Step 2: Steps */}
        {step === 2 && (
          <div className="space-y-3 py-4">
            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground">
                What steps should the agent follow?
              </p>
              <Button variant="outline" size="sm" className="h-7 gap-1 text-xs" onClick={addStep}>
                <Plus className="h-3 w-3" />
                Add Step
              </Button>
            </div>

            <div className="space-y-2">
              {steps.map((s, i) => {
                const Icon = getStepIcon(s.type)
                const color = getStepColor(s.type)
                const isLast = i === steps.length - 1

                return (
                  <div key={s.id}>
                    <div className="group rounded-lg border border-border bg-card p-4 transition-colors hover:border-primary/30">
                      <div className="flex items-start gap-3">
                        {/* Step number */}
                        <div className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-muted text-[10px] font-medium text-muted-foreground">
                          {i + 1}
                        </div>

                        <div className="flex-1 space-y-2.5">
                          {/* Step type selector */}
                          <div className="flex flex-wrap gap-1.5">
                            {STEP_TYPES.map((type) => {
                              const TypeIcon = type.icon
                              const isActive = s.type === type.id
                              return (
                                <button
                                  key={type.id}
                                  onClick={() => updateStep(s.id, { type: type.id })}
                                  className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-[10px] font-medium transition-colors ${
                                    isActive
                                      ? type.color + " ring-1 ring-inset ring-current"
                                      : "text-muted-foreground hover:bg-muted"
                                  }`}
                                >
                                  <TypeIcon className="h-3 w-3" />
                                  {type.label}
                                </button>
                              )
                            })}
                          </div>

                          {/* Step description */}
                          <Input
                            value={s.description}
                            onChange={(e) => updateStep(s.id, { description: e.target.value })}
                            placeholder="Describe what this step does..."
                            className="h-8 text-sm"
                          />

                          {/* Step details */}
                          <Input
                            value={s.details}
                            onChange={(e) => updateStep(s.id, { details: e.target.value })}
                            placeholder="Additional details or instructions (optional)"
                            className="h-7 text-xs text-muted-foreground"
                          />
                        </div>

                        {/* Actions */}
                        <div className="flex shrink-0 items-center gap-0.5 opacity-0 transition-opacity group-hover:opacity-100">
                          <button
                            onClick={() => moveStep(i, "up")}
                            disabled={i === 0}
                            className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-20"
                          >
                            <ChevronLeft className="h-3.5 w-3.5 rotate-90" />
                          </button>
                          <button
                            onClick={() => moveStep(i, "down")}
                            disabled={i === steps.length - 1}
                            className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground disabled:opacity-20"
                          >
                            <ChevronRight className="h-3.5 w-3.5 rotate-90" />
                          </button>
                          <button
                            onClick={() => removeStep(s.id)}
                            disabled={steps.length <= 1}
                            className="rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive disabled:opacity-20"
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Connector arrow */}
                    {!isLast && (
                      <div className="flex justify-center py-0.5">
                        <ArrowDown className="h-3.5 w-3.5 text-muted-foreground/40" />
                      </div>
                    )}
                  </div>
                )
              })}
            </div>

            <p className="text-xs text-muted-foreground">
              The final step will "Deliver the output" — this is added automatically
            </p>
          </div>
        )}

        {/* Step 3: Inputs & Clarify */}
        {step === 3 && (
          <div className="space-y-5 py-4">
            {/* Inputs */}
            <div>
              <div className="flex items-center justify-between mb-2">
                <label className="text-sm font-medium">Inputs</label>
                <Button variant="outline" size="sm" className="h-7 gap-1 text-xs" onClick={addInput}>
                  <Plus className="h-3 w-3" />
                  Add Input
                </Button>
              </div>
              {inputs.length === 0 && (
                <p className="text-xs text-muted-foreground py-2">
                  No inputs needed? Leave blank. Add inputs if the skill needs data from the user (e.g. a policy name)
                </p>
              )}
              <div className="space-y-2">
                {inputs.map((input, i) => (
                  <div key={i} className="flex items-start gap-2 rounded-lg border border-border p-3">
                    <div className="flex-1 space-y-2">
                      <div className="flex gap-2">
                        <Input
                          value={input.name}
                          onChange={(e) => updateInput(i, { name: e.target.value })}
                          placeholder="Input name (e.g. policy_name)"
                          className="h-8 flex-1 text-sm font-mono"
                        />
                        <select
                          value={input.type}
                          onChange={(e) => updateInput(i, { type: e.target.value as "string" | "text" | "number" })}
                          className="h-8 rounded-md border border-input bg-background px-2 text-xs"
                        >
                          <option value="string">String</option>
                          <option value="text">Text</option>
                          <option value="number">Number</option>
                        </select>
                      </div>
                      <Input
                        value={input.description}
                        onChange={(e) => updateInput(i, { description: e.target.value })}
                        placeholder="What is this input for?"
                        className="h-7 text-xs"
                      />
                    </div>
                    <button
                      onClick={() => removeInput(i)}
                      className="rounded p-1 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* Clarifying questions */}
            <div>
              <label className="text-sm font-medium">Clarifying Questions</label>
              <Textarea
                value={clarifyQuestions}
                onChange={(e) => setClarifyQuestions(e.target.value)}
                placeholder="e.g.
      - What depth of research do you need? (quick overview / comprehensive)
      - Should I focus on any specific aspect?
      - Who is the audience for this output?"
                rows={4}
                className="mt-1.5"
              />
              <p className="mt-1 text-xs text-muted-foreground">
                These questions will be asked before the skill runs, to clarify the user's intent
              </p>
            </div>
          </div>
        )}

        {/* Step 4: Review */}
        {step === 4 && (
          <div className="space-y-4 py-4">
            <div className="rounded-lg border border-border bg-card p-4">
              <h3 className="font-semibold text-sm">{name || "Unnamed Skill"}</h3>
              {description && (
                <p className="mt-1 text-xs text-muted-foreground">{description}</p>
              )}
              {triggerCommand && (
                <code className="mt-2 inline-block rounded bg-muted px-2 py-0.5 text-xs font-mono">
                  {triggerCommand}
                </code>
              )}
            </div>

            <div className="space-y-1.5">
              <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider">Steps</p>
              {steps.map((s, i) => {
                const Icon = getStepIcon(s.type)
                const color = getStepColor(s.type)
                return (
                  <div key={s.id} className="flex items-start gap-3 rounded-lg border border-border bg-card px-3 py-2">
                    <Badge className={`${color} border-0 text-[10px]`} variant="outline">
                      <Icon className="mr-1 h-3 w-3" />
                      {s.type.replace("_", " ")}
                    </Badge>
                    <span className="text-xs text-muted-foreground flex-1">{s.description}</span>
                    {i < steps.length - 1 && (
                      <ArrowDown className="h-3 w-3 text-muted-foreground/30 shrink-0" />
                    )}
                  </div>
                )
              })}
            </div>

            {inputs.length > 0 && (
              <div>
                <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-1">Inputs</p>
                <div className="flex flex-wrap gap-1.5">
                  {inputs.map((input, i) => (
                    <Badge key={i} variant="outline" className="text-[10px]">
                      {input.name} ({input.type})
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {clarifyQuestions && (
              <div className="rounded-lg border border-border bg-amber-500/5 p-3">
                <p className="text-xs font-medium text-muted-foreground mb-1">Clarifying Questions</p>
                <pre className="text-xs text-muted-foreground whitespace-pre-wrap">{clarifyQuestions}</pre>
              </div>
            )}
          </div>
        )}

        {/* Footer */}
        <DialogFooter className="gap-2">
          {step > 1 && (
            <Button variant="outline" onClick={() => setStep(step - 1)} className="gap-1">
              <ChevronLeft className="h-4 w-4" />
              Back
            </Button>
          )}
          <div className="flex-1" />
          {step < 4 ? (
            <Button onClick={() => setStep(step + 1)} disabled={!canProceed()} className="gap-1">
              Next
              <ChevronRight className="h-4 w-4" />
            </Button>
          ) : (
            <Button onClick={handleSave} disabled={saving || !name.trim()} className="gap-2">
              {saving ? (
                <>Saving...</>
              ) : (
                <>
                  <CheckCircle2 className="h-4 w-4" />
                  Save Skill
                </>
              )}
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
