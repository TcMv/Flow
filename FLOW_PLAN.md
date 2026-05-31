# Flow — Master Project Plan

> Self-hosted AI agent platform. Every employee gets their own personalised agent.
> Build skills. Share skills. Upload a process → agent runs it end-to-end with human gates.

**Last updated:** 1 June 2026 (Phase 0 built)
**Owner:** Taran Croxton
**Builder Team:** Hermes EA (me) + Claude Code + Codex
**Status:** 🟡 Phase 0 — 80% complete (waiting on Taran for AWS + GitHub push)
**Governance:** COO_Finance ✅ | COO_Legal ✅ | (conditional proceed, phase-gated)

---

## How This Document Works

This is the **single source of truth** for the build. I update it daily. It lives at `~/Documents/flow/FLOW_PLAN.md`.

- **Every Monday:** I review current phase, move completed tasks, plan the week
- **Every Friday:** I present progress to Taran with a decision summary
- **After every gate decision:** I update the gate status below
- **When blocked:** I escalate to Taran immediately via Telegram

---

## PHASE GATES (Hard Boundaries)

These are non-negotiable. If a gate fails, we stop or reassess before continuing.

```
  Phase 0 ──┬── Phase 1 ──┬── Phase 2 ──┬── Phase 3 ──┬── Phase 4
  Setup     │  Prototype   │  Dogfood     │  Client-Ready│  Scale
            │              │              │              │
        Gate 0          Gate 1          Gate 2          Gate 3
      Week 1 start    Week 4 end      Week 10 end     Week 14 end
```

| Gate | Phase | Criteria | Status |
|---|---|---|---|
| **G0** | Phase 0 → Phase 1 | Repo created, AWS Free Tier ready, DB schema applied, Taran AWS creds configured | ⬜ Pending |
| **G1** | Phase 1 → Phase 2 | Working agent with ONE skill that queries a database end-to-end. Demoable to Taran. | ⬜ Pending |
| **G2** | Phase 2 → Phase 3 | Taran using it daily. At least one LOI from prospective gov client. Entity formed. | ⬜ Pending |
| **G3** | Phase 3 → Phase 4 | Legal entity active, insurance in place, IRAP pre-assessment done, first client onboarding ready | ⬜ Pending |

---

## PHASE 0: Foundation (Week 1)

**Goal:** Everything we need standing before writing any product code.

### Must Haves Before We Start Phase 1
- [ ] GitHub repo created (`flow` under Taran's account)
- [ ] Monorepo scaffolded: `backend/` `frontend/` `infra/` `docs/`
- [ ] AWS Free Tier account set up and confirmed working
- [ ] AWS CDK bootstrapped
- [ ] Backend skeleton: FastAPI + health endpoint + Docker
- [ ] Frontend skeleton: React + Tailwind + shadcn/ui
- [ ] Database: first migration with core schema
- [ ] CI/CD: GitHub Actions deploys to AWS (basic)

### Tasks

|| # | Task | Owner | Status | Notes |
|---|---|---|---|---|---|
|| 0.1 | Create GitHub repo | Taran | ✅ | github.com/TcMv/Flow — code pushed |
|| 0.2 | Set up AWS Free Tier account | Taran | 🟡 | Doing this afternoon |
|| 0.3 | Reserve business name + domain | Taran | 🟡 | Using Vercel domain for now |
|| 0.4 | Scaffold monorepo structure | Me/Claude Code | ✅ | Done |
|| 0.5 | AWS CDK bootstrap + VPC | Claude Code | ⬜ | Needs AWS creds from 0.2 |
|| 0.6 | Backend skeleton + health endpoint | Claude Code | ✅ | FastAPI, health endpoint verified |
|| 0.7 | Frontend skeleton + blank app | Codex | ✅ | React + Tailwind + dark theme + login + dashboard |
|| 0.8 | Database: first migration | Codex | ✅ | Tenants, Users, AuditLog with hash chain |
|| 0.9 | CI/CD: GitHub Actions + Docker Compose | Claude Code | ✅ | Workflows, docker-compose, .gitignore, README |
|| 0.10 | **Gate 0 check: Everything ready for Phase 1** | Me | 🟡 | Waiting on AWS creds + GitHub push |

### Decisions I Need From Taran (Phase 0)

| Question | Why | Needed By |
|---|---|---|
| GitHub account name or org? | Where to create the repo | Day 1 |
| Domain preference? | flow.dev? flowgov.ai? something else? | Day 1 |
| AWS account email | Will need to walk through Free Tier sign-up | Day 1 |
| Target region | ap-southeast-2 (Sydney) for AU gov alignment? | Day 2 |

---

## PHASE 1: Agent Prototype (Weeks 2–4)

**Goal:** A working AI agent you can chat with that connects to a database, runs skills, and logs everything.

### Scope
- [ ] Multi-tenant auth (register, login, password reset)
- [ ] RBAC: Admin, Builder, User roles
- [ ] Agent execution engine (think → act → observe → log)
- [ ] LLM router (OpenAI + Claude + Azure swap-in)
- [ ] Tool layer (RDS query at minimum)
- [ ] Full audit logging (every action logged before execution)
- [ ] Basic chat UI (send message, stream response)
- [ ] Skill: one working skill loaded into agent
- [ ] **Gate 1: Demo to Taran — agent with one skill working end-to-end**

### Tasks

| # | Task | Owner | Status | Notes |
|---|---|---|---|---|
| 1.1 | Auth: registration + login + session mgmt | Claude Code | ⬜ | JWT-based, multi-tenant |
| 1.2 | Auth: RBAC (Admin, Builder, User) | Claude Code | ⬜ | Scoped to tenant |
| 1.3 | Agent engine: core loop | Me + Claude Code | ⬜ | This is the heart. Multiple iterations likely |
| 1.4 | LLM router: multi-provider support | Claude Code | ⬜ | Keys stored encrypted per tenant |
| 1.5 | Tool: RDS query connector | Codex | ⬜ | Parameterised, read-only for now |
| 1.6 | Audit: append-only logger | Me → Claude Code | ⬜ | Must log BEFORE execution |
| 1.7 | Chat UI: message input + streaming response | Claude Code | ⬜ | WebSocket-based |
| 1.8 | Chat UI: conversation history sidebar | Codex | ⬜ | |
| 1.9 | Skill: build first demo skill | Me | ⬜ | Pick one useful skill (see below) |
| 1.10 | Wire skill into agent execution | Me + Claude Code | ⬜ | |
| 1.11 | **Gate 1 check: Demo to Taran** | Me | ⬜ | Live demo with one skill |

### First Demo Skill (I Need Your Pick)

The first skill should be something real we can demo. Options:

| Skill | What it does | Why |
|---|---|---|
| **DB Query** | "Show me all users who signed up this month" | Simplest possible — proves agent→tool→DB pipeline |
| **Document Search** | "Find the policy document about leave" | More impressive demo — shows RAG capability |
| **Process Notetaker** | "Log a meeting note to the system" | Practical for internal dogfooding |

**Pick one and I'll build toward it.**

### Architecture Decisions For You (Phase 1)

| Question | Options | Needed By |
|---|---|---|
| Chat UI style? | Like ChatGPT (left sidebar + centre chat) or like Slack (threaded)? | Week 2 |
| Agent persona per user? | Yes — every user can name and style their agent | Week 3 |
| | No — one standard agent persona for now | |
| Skill definition format? | Skills as prompt templates (simpler) | Week 3 |
| | Skills as code modules (more powerful) | |
| | Both — start simple, add code later | |

---

## PHASE 2: Skill System (Weeks 5–7)

**Goal:** Users can build, install, and share skills. Platform is dogfoodable.

- [ ] Skill CRUD API + data model
- [ ] Skill builder UI (name, description, prompt, tool config)
- [ ] Skill runtime: loaded per user at session start
- [ ] Skill marketplace (browse, search, install)
- [ ] Skill versioning + publish/deprecate workflow
- [ ] Skill sharing (within team, across tenant with approval)
- [ ] Admin dashboard basics (usage, skills, users)
- [ ] Internal dogfooding starts

### Decisions For You (Phase 2)

| Question | Why | Needed By |
|---|---|---|
| Who dogfoods first? | Just you? Or a few trusted people? | Week 6 |
| Skill marketplace: public or private? | Within-company only, or cross-company marketplace? | Week 6 |

---

## PHASE 3: Process → Workflow (Weeks 8–10)

**Goal:** Upload a process description → agent designs the workflow → runs it with human checkpoints.

This is the crown jewel. The genuinely novel feature.

- [ ] Process ingestion (upload text/doc → agent parses into steps)
- [ ] Step types: automated, human-approval, quality-gate, conditional, parallel
- [ ] Workflow execution engine (state machine)
- [ ] Human-in-the-loop: approval requests, quality checks
- [ ] Escalation rules (if step not done by deadline)
- [ ] Workflow visualisation (DAG view in UI)
- [ ] Error handling + retry + manual intervention
- [ ] **Gate 2 check (end of Week 10): At least one LOI from gov prospect**

### Decisions For You (Phase 3)

| Question | Why | Needed By |
|---|---|---|
| First process to test? | Pick a real process from your life or a prospect's | Week 8 |
| Human approval channel? | In-app? Email? Telegram? | Week 9 |

---

## PHASE 4: Compliance & Client-Ready (Weeks 11–14)

**Goal:** Platform can be deployed to a government client.

- [ ] Pty Ltd formed + IP assigned (end of Week 10)
- [ ] Company AWS account created + infra migrated
- [ ] Insurance in place (PI, Cyber, Public Liability)
- [ ] Legal templates: MSA, DPA, SLA, AUP (lawyer-reviewed)
- [ ] Hash-chained audit log (tamper-evident)
- [ ] Encryption: at rest + in transit
- [ ] Session hardening, SSO/SAML
- [ ] IRAP pre-assessment / gap analysis
- [ ] Procurement panel applications (Digital Marketplace, DTA)
- [ ] Demo environment for prospects
- [ ] **Gate 3: First client onboarding ready**

---

## ONGOING DECISIONS LOG

Every time I need a decision from you, I log it here with a status.

| # | Question | Raised | Needed By | Status |
|---|---|---|---|---|
| D01 | First demo skill: DB Query / Document Search / Process Notetaker? | Phase 1 | Week 2 | ⬜ Pending |
| D02 | Chat UI style: ChatGPT-like or Slack-like? | Phase 1 | Week 2 | ⬜ Pending |
| D03 | Agent persona: per-user customisable or standard? | Phase 1 | Week 3 | ⬜ Pending |
| D04 | Skill format: prompt templates, code modules, or both? | Phase 1 | Week 3 | ⬜ Pending |
| D05 | Who dogfoods Phase 2? | Phase 2 | Week 6 | ⬜ Pending |
| D06 | First test process for Phase 3? | Phase 3 | Week 8 | ⬜ Pending |

---

## WEEKLY RHYTHM

### What I Do
- **Daily:** Build during the day. Brief you on progress via Telegram.
- **Blockers:** I escalate immediately if something needs you.
- **Friday:** I prepare a weekly summary with:
  - What was built
  - What's blocked (if anything)
  - What I need from you
  - Is the phase gate on track?

### What You Do
- **Daily:** Read my Telegram brief (5 mins)
- **Friday:** Review demo + steer for next week (30–60 mins)
- **Ad hoc:** Jump in when I need a decision on the big questions above

---

## RISK WATCH

I keep a live risk log here. Status updates as we go.

| Risk | Likelihood | Impact | Status | Mitigation |
|---|---|---|---|---|
| Process→workflow compiler harder than expected | Medium | High | ⬜ Watching | Prototype early (Week 8). Simple 3-step first. |
| Scope creep | High | Medium | ⬜ Watching | Phase gates are hard boundaries. No feature without passing gate. |
| AWS Free Tier insufficient | Low | Medium | ⬜ Watching | $50 contingency. Pay only if needed. |
| Taran loses interest / gets busy | Medium | High | ⬜ Watching | I keep summaries tight. Weekly demos keep momentum. |
| Government compliance costs surprise us | Low | High | ⬜ Watching | ~$14k–$29k known. Budget confirmed before Phase 3. |
| Claude Code / Codex quality issues | Low | Medium | ⬜ Watching | Every output reviewed before merge. |

---

## QUICK REFERENCE

### Repo
- `github.com/tarancroxton/flow` (or wherever we put it)
- Branches: `main` (stable), `develop` (daily work), feature branches

### Key Paths
- **Plan:** `~/Documents/flow/FLOW_PLAN.md`
- **Governance:** `~/Documents/flow/governance-review.md`
- **Code:** `~/Documents/flow/`
- **Architecture diagrams:** Added when built

### Tools
- **Backend:** Python + FastAPI
- **Frontend:** React + Tailwind + shadcn/ui
- **Infra:** AWS CDK (TypeScript)
- **DB:** PostgreSQL on RDS (Free Tier)
- **CI/CD:** GitHub Actions
- **Auth:** Self-hosted JWT (Supabase Auth later if needed)
- **Monitoring:** CloudWatch (free tier adequate for dev)

---

*This document is the single source of truth. Updated by Hermes EA every Friday and after any gate decision.*
