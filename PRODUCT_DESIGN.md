# Flow — Product Design: User Workflows, Processes, Inputs & Outputs

> Government-grade AI agent platform. Every employee gets a personalised agent that can build & share skills, design workflows from process descriptions, and execute them with human checkpoints. All decisions logged immutably.

---

## 0. Core Architecture Model

### Skills vs Workflows — The Foundation

```
┌──────────────────────────────────────────────────────────────┐
│                          WORKFLOW                             │
│  Orchestrated chain of tasks. Each task invokes a skill.      │
│                                                               │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   │
│  │ Task 1   │──>│ Task 2   │──>│ Task 3   │──>│ Task 4   │   │
│  │ Skill:   │   │ Skill:   │   │ Skill:   │   │ Skill:   │   │
│  │ Research │   │ Analyse  │   │ Draft    │   │ Present  │   │
│  └──────────┘   └──────────┘   └──────────┘   └──────────┘   │
│                                        │                      │
│                                        ▼                      │
│                                  ┌──────────┐                 │
│                                  │ Task 5   │                 │
│                                  │ Skill: QA│                 │
│                                  └──────────┘                 │
│                                        │                      │
│                                        ▼                      │
│                                    Deliver                    │
└──────────────────────────────────────────────────────────────┘

vs

┌──────────────────────────────────────────────────────────────┐
│                         SKILL                                  │
│  Atomic, single-purpose. May include human interaction.        │
│                                                               │
│  "Tell me about keeping a bee hive clean"                     │
│        │                                                      │
│        ▼                                                      │
│  ┌──────────────┐                                             │
│  │ Agent thinks │                                             │
│  │ & acts       │── may ask clarify questions mid-way         │
│  └──────┬───────┘── may pause for human input                 │
│         │          ── returns a single output                  │
│         ▼                                                     │
│  Response: "Here's how to keep a hive clean..."               │
└──────────────────────────────────────────────────────────────┘
```

**Skill** = an atomic, single-purpose capability. A skill takes inputs, processes them (possibly with human interaction along the way), and returns an output. A skill can ask clarify questions or pause for human input mid-execution.

**Workflow** = an orchestrated chain of tasks. Each task references a skill to execute. Workflows define the sequence, dependencies, and data flow between skills. They exist for complex processes that no single skill can handle.

Example:
> "Write me a report on bees and how to keep the hive clean"
> → Workflow: Task 1 (Skill: Research) → Task 2 (Skill: Analyse) → Task 3 (Skill: Draft) → Task 4 (Skill: Presentation Design) → Task 5 (Skill: QA) → Deliver

---

## 1. User Types (Personas)

| Role | Access Scope | Key Actions |
|---|---|---|
| **Employee** | Own agent, own skills, marketplace skills, assigned workflows | Chat, create skills, run workflows, approve checkpoints, submit skills to marketplace |
| **Manager** | Own agent + team visibility | Review team activity, approve/reject marketplace submissions, assign workflows |
| **Platform Admin** | Tenant-wide | User management, audit log access, LLM config, skill governance, risk settings |
| **Auditor** | Read-only | Immutable audit log review, export evidence, hash chain verification |

---

## 2. Core User Journeys

### Journey A: Daily Agent Chat

**Trigger:** Employee opens Flow to ask a question or get something done.

```
┌─────────────┐    ┌──────────────┐    ┌────────────────┐
│  Open Flow  │───>│  Chat View   │───>│  Agent Responds│
│  (browser)  │    │  type query  │    │  (LLM + tools) │
└─────────────┘    └──────────────┘    └───────┬────────┘
                                               │
                                        ┌──────▼──────┐
                                        │ Agent may:   │
                                        │ • Answer     │
                                        │ • Use a tool │
                                        │ • Run a skill│
                                        │ • Ask followup│
                                        │ • Trigger    │
                                        │   a workflow │
                                        └──────────────┘
```

**Inputs:**
- Natural language query
- Session history context
- User's identity/permissions
- Available skills (own + marketplace)

**Outputs:**
- Natural language response
- Skill execution results
- Workflow trigger (optional)
- Audit log entry for every agent action

---

### Journey B: Skill Creation (Through Chat)

**Trigger:** Employee sees the agent do something useful and wants to save it as a reusable skill.

> **Example:** "Every time I ask for a policy summary, you do the same thing. Can you save that as a skill called 'Policy Brief'?"

**Via Chat (natural language):**
```
User: "Save this as a skill called 'Policy Brief'. 
        When I say 'brief me on [policy name]', search 
        the policy docs, summarise in 3 paragraphs, 
        add relevant legislation references, and format 
        it as a memo."

Agent: "Skill created. Policy Brief is now available in 
        your skills list. When you type /brief National 
        Security Directive 42 it will run the skill."
```

**Skill internal structure:**

A skill can have human interaction *inside* it:
```
Skill: "Policy Brief"

┌─────────────────────────────────────────────┐
│ Step 1: Search policy docs for [policy name]│
│ Step 2: Ask user: "Focus on risk sections   │
│          or implementation?" (clarify)       │
│ Step 3: Summarise based on focus area       │
│ Step 4: Add legislation references          │
│ Step 5: Format as memo                      │
│ Return: formatted memo string               │
└─────────────────────────────────────────────┘
```

**Inputs:**
- Skill name & description
- Trigger phrase or command prefix
- Definition (what it does)
- Input variables (e.g. `[policy name]`)
- Output format specification

**Outputs:**
- Structured skill definition (stored in DB)
- Skill available via chat command
- Added to user's personal skill library
- Audit log: skill created

---

### Journey C: Skill Marketplace (Sharing)

**Trigger:** Employee creates a useful skill and wants to share it across the organisation.

**Visibility model:**

```
User saves a skill
  │
  ├── Private (default) — only me can use it
  │
  └── Submit to Org Marketplace
        │
        ▼
  Review & Assessment queue
        │
  ┌─────┴─────┐
  │           │
  ▼           ▼
Approved    Rejected
  │           │
  ▼           ▼
Available   Returned to
to all      creator with
employees   feedback
```

**Marketplace submission process:**
1. Creator tags a skill for marketplace
2. Skill enters assessment/review queue
3. Manager or assigned reviewer evaluates:
   - Functionality — does it work?
   - Compliance — any regulatory concerns?
   - Security — does it access sensitive data appropriately?
   - Quality — is the output reliable?
4. Approved → published to org marketplace
5. Rejected → returned to creator with notes

**Inputs (for sharing):**
- Skill ID
- Submission to marketplace flag
- Optional: usage notes for reviewers

**Outputs:**
- Skill visibility updated to marketplace (if approved)
- Notification to creator
- Audit log: marketplace submission / approval / rejection

---

### Journey D: Process → Workflow Compiler

**Trigger:** Employee has a multi-step process that takes multiple skills working together.

> **"I want a report on bees and how to keep the hive clean"**
> → Agent analyses: this needs Research, Analyse, Draft, Presentation Design, QA

```
┌─────────────┐    ┌───────────────────┐    ┌──────────────────┐
│ User submits │───>│ Agent analyses    │───>│ Agent identifies │
│ process      │    │ & extracts steps  │    │ which skills     │
│ (text/docx/  │    │ identifies:      │    │ each task needs  │
│  pdf/image)  │    │ • Tasks needed   │    │                  │
│              │    │ • Dependencies   │    │                  │
│              │    │ • Decision points│    │                  │
│              │    │ • Human approvals│    │                  │
│              │    │ • Data flow      │    │                  │
│              │    │ between tasks    │    │                  │
│              │    │ • Required skills│    │                  │
└─────────────┘    └───────────────────┘    └────────┬─────────┘
                                                      │
                                              ┌───────▼────────┐
                                              │ Agent proposes │
                                              │ workflow:      │
                                              │ Task 1 ->      │
                                              │ Skill: Research│
                                              │ → Task 2 ->    │
                                              │ Skill: Analyse │
                                              │ → etc         │
                                              └───────┬────────┘
                                                      │
                                              ┌───────▼────────┐
                                              │ User reviews & │
                                              │ edits workflow │
                                              │ (approve /     │
                                              │ modify /       │
                                              │ reject)        │
                                              └───────┬────────┘
                                                      │
                                              ┌───────▼────────┐
                                              │ Workflow saved │
                                              │ Ready to run   │
                                              └────────────────┘
```

**Input formats (flexible):**
- Plain text / markdown
- Document upload (.docx, .pdf)
- Image / screenshot (agent reads the image)
- Reference documents (optional)

**Outputs:**
- Structured workflow definition (JSON)
  - Ordered tasks, each referencing a skill
  - Dependencies between tasks
  - Human checkpoint nodes (where decisions needed)
  - Data contracts: what each task inputs and outputs
  - Error handling paths
- Visual workflow diagram (for review)
- Run button — execute on approval

**Workflow Definition Schema (conceptual):**

```yaml
workflow:
  name: "Bee Hive Report"
  trigger: "chat command"
  tasks:
    - id: task_1
      skill: "Research"
      description: "Research bees and hive maintenance"
      inputs:
        topic: "bees and keeping hive clean"
        depth: "comprehensive"
      outputs:
        research_notes: string
    - id: task_2
      skill: "Analyse"
      description: "Analyse research findings"
      depends_on: [task_1]
      inputs:
        source: "{{task_1.research_notes}}"
        focus: "key insights, actionable steps"
      outputs:
        analysis: string
    - id: task_3
      skill: "Draft"
      description: "Write the report"
      depends_on: [task_2]
      inputs:
        source: "{{task_2.analysis}}"
        format: "professional report"
      outputs:
        draft: string
    - id: task_4
      skill: "Presentation Design"
      description: "Design report slides"
      depends_on: [task_3]
      inputs:
        content: "{{task_3.draft}}"
        template: "corporate"
      outputs:
        slides: file
    - id: task_5
      type: human_approval
      skill: "QA"
      description: "Review and approve final deliverables"
      depends_on: [task_4]
      assignee: "requestor"
      inputs:
        items: ["{{task_3.draft}}", "{{task_4.slides}}"]
      outputs:
        approval: boolean
        feedback: string (optional)
      on_approve: deliver
      on_reject: return_to_task_3_with_feedback
```

---

### Journey E: Workflow Execution

**Trigger:** Employee runs a saved workflow (from chat command or workflow library).

**Triggers:**
- **Chat command** — "run the bee report workflow"
- **Scheduled** — "run this every Monday at 9am" (Phase 2+)

```
Run workflow
  │
  ▼
Task 1 → Skill: Research → executes → output stored
  │
  ▼
Task 2 → Skill: Analyse → gets Task 1 output → executes → output stored
  │
  ▼
Task 3 → Skill: Draft → gets Task 2 output → executes → output stored
  │
  ▼
Task 4 → Skill: Presentation Design → gets Task 3 output → executes
  │
  ▼
⏸️ Task 5: Human Checkpoint — QA Review
  │  → Notification sent to assignee
  │  → Waits for input
  │
  ├── ✅ Approve → Deliver final output
  └── ❌ Reject → Feedback → Loop back to Task 3
```

**Human Checkpoint Experience:**
```
Agent: ⏸️ Workflow 'Bee Hive Report' paused.
       Task 5 'QA' needs your input.

       Deliverables ready for review:
       📄 Report (draft)
       📊 Slides (presentation)

       ┌─────────────────────────────────────┐
       │ ✅ Approve — looks good              │
       │ ❌ Reject — needs changes             │
       │    └─ Feedback: "Add section on ...  │
       └─────────────────────────────────────┘
```

**Inputs (when running):**
- Workflow ID
- Run parameters (overrides if any)
- Checkpoint decisions with justifications

**Outputs (per run):**
- Execution trace (task-by-task with timestamps)
- Skill outputs at each step (stored for audit)
- Checkpoint decisions (who, what, when, why)
- Final deliverable(s)
- Run status: running / paused / completed / failed / cancelled

---

### Journey F: Audit & Compliance Review

**Trigger:** Auditor or Admin reviews agent activity for compliance.

```
Auditor logs in → Read-only audit view → Can:
  • View all agent actions with timestamps
  • Filter by user, date, action type
  • Drill into workflow executions
  • Drill into skill executions
  • Export evidence package
  • Verify hash chain integrity
```

**Audit Log Entry Schema:**
```json
{
  "timestamp": "2026-06-01T14:30:00Z",
  "user_id": "user_abc123",
  "session_id": "sess_xyz789",
  "action_type": "skill_execute | skill_create | workflow_run | checkpoint_decision",
  "action_detail": {
    "skill": "Research",
    "input": { "topic": "bees and hive maintenance" },
    "output_summary": "Research completed — 47 sources found"
  },
  "skill_id": "skill_def456",
  "workflow_run_id": "run_789ghi",
  "chain_hash": "sha256:abcdef...",
  "previous_hash": "sha256:123456...",
  "immutable": true
}
```

**Inputs (for review):**
- Filter criteria (date range, user, action type, skill, workflow)
- Optional: export format preference

**Outputs:**
- Filtered log entries (paginated)
- Export file (CSV/PDF/JSON)
- Hash chain integrity: valid / broken (alert if broken)

---

## 3. How These Journeys Fit Together

```
                ┌─────────────────────────┐
                │     Log in / Onboard    │
                └──────────┬──────────────┘
                           │
                ┌──────────▼──────────────┐
                │   Day-to-Day: Chat      │◄──────────────┐
                │   with your agent       │                │
                └──────────┬──────────────┘                │
                           │                                │
                ┌──────────▼──────────────┐                │
                │  Agent responds         │────────────────┘
                │  (LLM / tool / skill)   │  (keeps chatting)
                └──────────┬──────────────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
   ┌────────────────────┐   ┌──────────────────────────┐
   │ "Save that as a    │   │ "This needs multiple     │
   │  skill" via chat   │   │  skills. Process doc!"   │
   └──────────┬─────────┘   └──────────┬───────────────┘
              │                         │
              ▼                         ▼
   ┌────────────────────┐   ┌──────────────────────────┐
   │ Skill in my        │   │ Agent compiles workflow: │
   │ personal library   │   │ Task 1 → Skill: X        │
   │                    │   │ Task 2 → Skill: Y        │
   │ Use via /command   │   │ Task 3 → Skill: Z        │
   └──────────┬─────────┘   └──────────┬───────────────┘
              │                         │
              │              ┌──────────▼───────────────┐
              │              │ User reviews & approves  │
              │              │ workflow design          │
              │              └──────────┬───────────────┘
              │                         │
              │              ┌──────────▼───────────────┐
              │              │ Workflow saved to        │
              │              │ personal library         │
              │              └──────────┬───────────────┘
              │                         │
              └──────┬──────────────────┘
                     │
                     ▼
          ┌──────────────────────┐
          │ Run (chat / cron)    │
          └──────────┬───────────┘
                     │
          ┌──────────▼───────────┐
          │ Skill executes /     │
          │ Workflow runs step   │
          │ by step              │
          └──────────┬───────────┘
                     │
          ┌──────────▼───────────┐
          │ [Optional] Human     │
          │ checkpoint → input   │
          └──────────┬───────────┘
                     │
          ┌──────────▼───────────┐
          │ Deliver output       │
          │ Everything logged    │
          │ immutably            │
          └──────────────────────┘
```

---

## 4. Data Governance & Security (Foundation Principles)

Applies to everything we build from day one.

| Principle | Implementation |
|---|---|
| **Data isolation** | Tenant-level data separation. Employee A cannot see Employee B's skills, workflows, or chat history unless explicitly shared and approved |
| **Immutable audit trail** | Every agent action logged with hash chain. Tamper-evident: if anyone modifies a past log entry, the chain breaks |
| **Least privilege** | Agent inherits user permissions. No god-mode agent account |
| **Human-in-the-loop** | Consequential actions (approvals, sharing to marketplace, cross-boundary data access) require human decision |
| **Input validation** | All user inputs sanitised before reaching LLM. Prompt injection hardened |
| **Data sovereignty** | Australian data stays in Australia. BYO-LLM so no data leaves your infra |
| **Encryption at rest & in transit** | Database encryption, HTTPS, TLS everywhere |
| **Audit replay** | Any workflow execution can be fully replayed from audit logs for compliance review |

*Specific compliance level (IRAP PROTECTED, etc.) to be determined — architecture supports progressive hardening.*

---

## 5. Build Priority: Phase 1

Given current state (auth + basic chat + DeepSeek working), the proposed build order:

| Order | Feature | Why |
|---|---|---|
| **1** | **Skill system** — create from chat, store, invoke via `/command` | Core atomic unit. Everything else builds on this |
| **2** | **Skill builder UI** — visual skill creation | Makes skills accessible to non-technical users |
| **3** | **Marketplace** — submit, review, install skills | Org-wide value multiplier |
| **4** | **Workflow compiler** — upload process → get workflow | The flagship capability |
| **5** | **Workflow execution engine** — run, pause, checkpoint, resume | The runtime |
| **6** | **Scheduling** — cron-based workflow triggers | Phase 2 feature |

---

## 6. Design Decisions (Confirmed)

| Question | Decision |
|---|---|
| Skill vs Workflow distinction | **Skill = atomic task. Workflow = chain of skills.** Separated |
| Can skills have human interactions? | **Yes** — clarify questions, checkpoints, approvals all allowed mid-skill |
| Skill sharing model | **Private by default.** Creator can submit to org marketplace. Marketplace requires assessment/review before release |
| Workflow triggers | **Chat command** (v1). **Scheduled/cron** (v2). No webhook/API needed for now |
| Input formats | **Text, docx, pdf, image/screenshot** — flexible input supported |
| Compliance scope | **Utmost data governance & security.** Specific level (IRAP etc.) TBD. Architecture supports progressive hardening |
