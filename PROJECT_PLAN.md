# Project Plan: Flow

> A self-hosted AI agent platform where every employee gets their own personalised agent, can build and share skills, and upload processes for end-to-end workflow delivery.

---

## 1. Vision

Every person in an organisation gets their own AI assistant — like Hermes but for them. Personalised, skilled, connected to what counts. Teams share skills. Processes get uploaded as plain text and the agent designs and runs the workflow with human quality gates.

**One sentence:** *Give every employee an agent as capable as mine, wrapped in governance that makes government comfortable.*

---

## 2. Core Principles

| Principle | Why |
|---|---|
| **Self-hosted on customer AWS** | Data sovereignty. Customer controls infra. |
| **BYO-LLM** | They bring their own API key. No vendor lock-in. |
| **Audit-first architecture** | Every action logged immutably before it happens. |
| **Chat-native builder** | Non-engineers build agents by describing what they want. |
| **Skills as primitives** | Skills are shareable, versioned, composable blocks. |

---

## 3. Architecture Overview

```
┌─────────────────────────────────────────────────────┐
│                    Web UI (React)                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────┐   │
│  │ Chat      │  │ Skills   │  │ Process Upload   │   │
│  │ Interface │  │ Workshop │  │ → Workflow View  │   │
│  └─────┬────┘  └────┬─────┘  └────────┬─────────┘   │
├────────┼─────────────┼────────────────┼──────────────┤
│  Backend API (FastAPI / Python)                     │
│  ┌──────┴──────────────┴────────────────┴───────┐   │
│  │              Agent Execution Engine             │   │
│  │  (think → act → observe → log → repeat)       │   │
│  └──────┬──────────────┬────────────────┬───────┘   │
│  ┌──────┴──────┐ ┌─────┴──────┐ ┌──────┴────────┐  │
│  │ LLM Router  │ │ Tool Layer │ │ Workflow       │  │
│  │ OpenAI      │ │ RDS        │ │ Engine         │  │
│  │ Claude      │ │ DynamoDB   │ │ (process→steps)│  │
│  │ Azure/Copilot││ S3         │ │                │  │
│  │ Custom       │ │ API calls │ │                │  │
│  └──────┬──────┘ └─────┬──────┘ └──────┬────────┘  │
├─────────┼──────────────┼────────────────┼───────────┤
│  ┌──────┴──────────────┴────────────────┴───────┐   │
│  │         Audit Database (PostgreSQL)           │   │
│  │  · Every LLM call + response                 │   │
│  │  · Every tool invocation + result             │   │
│  │  · Every skill created / modified / shared    │   │
│  │  · Every workflow run + state transitions     │   │
│  │  · Append-only, no deletion, cryptographically │   │
│  │    chained (hash chain for tamper evidence)    │   │
│  └───────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

---

## 4. Stack Decisions

| Layer | Choice | Why |
|---|---|---|
| **Backend** | Python + FastAPI | Best ecosystem for AI/LLM work. FastAPI = async, auto-docs, type-safe. |
| **Frontend** | React + Tailwind + shadcn/ui | Fast to build, clean UI, well-known by dev agents. |
| **Database** | PostgreSQL (via RDS) | Audit logging needs relational integrity. Append-only tables. |
| **Auth** | Supabase Auth or Auth0 (self-hosted) | Multi-tenant, SSO/SAML, RBAC out of the box. |
| **Infra** | AWS CDK (TypeScript) | Infrastructure as code. Repeatable, auditable, versioned. |
| **Deployment** | Docker + ECS Fargate | Serverless containers. No servers to manage. Auto-scales. |
| **Caching** | Redis ElastiCache | Session state, rate limiting, skill cache. |
| **Object storage** | S3 | Process uploads, skill attachments, logs. |

---

## 5. Data Model (Core Tables)

### Tenants
- id, name, aws_region, created_at, settings (JSONB)

### Users
- id, tenant_id, email, name, role, agent_config (JSONB)

### LLM Keys
- id, tenant_id, provider (openai/anthropic/azure/custom), key_encrypted, base_url, created_at

### Agent Sessions
- id, user_id, created_at, ended_at, metadata (JSONB)

### Agent Messages
- id, session_id, role (user/assistant/tool), content, tool_calls (JSONB), created_at

### Skills
- id, tenant_id, author_id, name, description, prompt_template, tool_configs (JSONB), version, status (draft/published/deprecated), created_at

### Skill Installations
- id, skill_id, user_id, installed_at, config_overrides (JSONB)

### Processes
- id, tenant_id, author_id, source_text, parsed_steps (JSONB), status, created_at

### Workflow Runs
- id, process_id, user_id, current_step, state (JSONB), status (running/paused/blocked/completed/failed), created_at

### Audit Log (append-only)
- id, tenant_id, timestamp, actor_id, action_type, resource_type, resource_id, details (JSONB), hash_chain_prev, hash

### Access Controls
- id, tenant_id, role, resource_type, resource_id_pattern, permissions (JSONB)

---

## 6. Build Phases

### Phase 0: Setup & Scaffold (Week 1)

| Day | What | Who |
|---|---|---|
| 1 | Create GitHub repo, monorepo structure, CI/CD pipeline | Me + Claude Code |
| 2 | AWS CDK scaffold: VPC, RDS, ECS cluster, S3 buckets | Claude Code |
| 3 | Backend scaffold: FastAPI app, Dockerfile, health endpoint | Claudio Code |
| 4 | Frontend scaffold: React + Tailwind + shadcn/ui, blank app | Codex |
| 5 | Database migrations: core schema (tenants, users, audit, skills) | Me → Codex |

**Milestone:** Deployable skeleton running on AWS.

### Phase 1: Multi-Tenant Auth & User Management (Week 2)

| What | Who |
|---|---|
| Self-hosted auth: registration, login, password reset, MFA | Claude Code |
| Tenant isolation: every query scoped by tenant_id | Me (arch) → Claude Code |
| RBAC: Admin, Agent Builder, Agent User roles | Codex |
| SSO/SAML integration (for government later) | Claude Code |
| Profile settings: name, preferences, agent persona | Codex |

### Phase 2: Agent Engine (Weeks 3–4)

| What | Who |
|---|---|
| Agent loop: think → act → observe → log → repeat | Me + Claude Code |
| LLM router: multi-provider support with key management | Claude Code |
| Tool abstraction layer: AWS SDK wrappers (RDS, DynamoDB, S3) | Codex |
| Tool execution sandbox: timeout, error handling, rate limiting | Claude Code |
| Full audit logging: every step logged before execution | Me → Claude Code |
| Session management: conversation history, resumability | Codex |

**Milestone:** A working agent you can chat with that queries a database and logs everything.

### Phase 3: Chat Interface (Week 5)

| What | Who |
|---|---|
| Real-time chat UI (WebSockets, streaming responses) | Claude Code (React) |
| Conversation history sidebar | Codex |
| Markdown rendering, code blocks, file uploads | Codex |
| Agent persona / settings panel | Claude Code |
| Mobile-responsive layout | Codex |

**Milestone:** Employees can log in and chat with their personal agent.

### Phase 4: Skill System (Weeks 6–7)

| What | Who |
|---|---|
| Skill data model + CRUD API | Codex |
| Skill builder UI: name, description, prompt template, tool config | Claude Code |
| Agent runtime integration: skills loaded per user at session start | Me + Claude Code |
| Skill marketplace: browse, search, install, uninstall | Claude Code |
| Skill versioning: draft → publish → deprecate | Codex |
| Skill sharing: within team, within tenant, cross-tenant (admin approval) | Me (arch) → Claude Code |

**Milestone:** Users can build skills by describing them, and share with their team.

### Phase 5: Process → Workflow Compiler (Weeks 8–10)

This is the crown jewel. Genuinely novel.

| What | Who |
|---|---|
| Process ingestion: user uploads text/doc → agent parses into structured workflow | Me (prompt engineering) + Claude Code |
| Step types: automated, human-approval, quality-gate, conditional, parallel | Claude Code |
| Workflow execution engine: run steps, track state, handle transitions | Claude Code |
| Human-in-the-loop: approval requests, quality checks, notifications | Claude Code |
| Escalation rules: if step not completed by deadline, escalate | Codex |
| Workflow visualisation: DAG view of running process | Claude Code (React) |
| Error handling: retry logic, dead-letter queue, manual intervention | Me → Claude Code |

**Milestone:** Upload a process description → agent designs it → runs it with human checkpoints.

### Phase 6: Admin Dashboard & Monitoring (Week 11)

| What | Who |
|---|---|
| Usage analytics: active users, sessions, skill adoption | Codex |
| Audit log viewer: search, filter, export | Claude Code |
| Agent monitoring: failed runs, slow responses, token usage | Codex |
| LLM key management UI: add/rotate/remove keys | Codex |
| Tenant settings: custom branding, allowed LLM providers | Claude Code |

### Phase 7: Compliance & Hardening (Weeks 12–13)

| What | Who |
|---|---|
| Cryptographically chained audit log (hash chain for tamper evidence) | Claude Code |
| Data encryption: at rest (RDS/S3 encryption), in transit (TLS 1.3) | Codex |
| Session timeout, automatic logout, IP allowlisting | Codex |
| Audit for ASD Essential Eight alignment | Me |
| Penetration test prep + documentation package | Me |
| IRAP documentation template (self-assessment ready) | Me |

### Phase 8: Polish & Demo Ready (Week 14)

| What | Who |
|---|---|
| End-to-end testing of all flows | Me |
| Sample tenant with demo data | Codex |
| Sample processes pre-loaded for demo | Me |
| Deployment guide for new tenants | Me → Claude Code |
| Customer-facing landing page | Claude Code |

**Milestone:** We can demo to a government prospect.

---

## 7. Weekly Workflow (How We Operate)

| Day | What |
|---|---|
| **Monday** | I review current state, write specs for the week's work, assign to Claude Code / Codex. You get a brief in the morning. |
| **Tuesday–Thursday** | Claude Code and Codex build. I QA every output, fix issues, adjust specs. You review daily summaries in Telegram. |
| **Friday** | Demo of the week's progress to you. You steer, we plan next week. |
| **Ad hoc** | You jump in whenever to steer, ask questions, redirect. |

**Communication:**
- Daily standup via Telegram — I brief you on what was built, what's blocked, what's next
- You give quick direction shifts via voice note or text
- I escalate blockers immediately

**Quality control:**
- Every piece of code Claude Code or Codex writes gets reviewed by me or each other before merge
- Tests are written alongside code (not after)
- Each phase milestone has a working demo before we move on

---

## 8. Key Risks & Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| **Process→workflow compiler is harder than expected** | Medium | Prototype early (Week 8). Start with simple 3-step processes. Iterate. |
| **Claude Code or Codex produces unreliable code** | Low | Every output reviewed. No automatic merges. |
| **AWS costs spiral during dev** | Low | Dev environment on minimal instances (~$100/month). Prod scales later. |
| **Scope creep — building too many features** | High | **Strict phase gates.** Phase N does not start until Phase N-1 is signed off. |
| **Government compliance requirements change** | Medium | Build clean, audit-addicted architecture. Compliance is a wrapper, not a rebuild. |
| **We lose momentum** | Medium | Daily standups. Weekly demos. Visible progress keeps us moving. |

---

## 9. Investment Estimate

### Time
- **Demo-ready (chat + skills):** ~7 weeks
- **Process→workflow MVP:** ~10 weeks
- **Production + compliance:** ~14 weeks

### AWS Costs (Dev)
| Service | Monthly |
|---|---|
| RDS db.t3.small | ~$25 |
| ECS Fargate (1 task) | ~$15 |
| ElastiCache (small) | ~$20 |
| S3 | ~$5 |
| **Total** | **~$65/month** |

### Your Time Commitment
- **Daily:** 5–10 mins reviewing summary
- **Weekly:** 30–60 min demo + steer
- **Ad hoc:** Direction calls when needed

---

## 10. What I Need From You

| By when | What |
|---|---|
| **Now** | Name for the product (working name: "Flow" — happy to change) |
| **This week** | AWS account sign-up or I create a dev account under yours |
| **Week 1** | First use-case to build toward (so I can test against something real) |
| **Weekly** | 30 min for Friday demo |

---

## 11. First Actions (Tomorrow)

1. Create GitHub repo: `flow` under your account
2. Set up monorepo: `backend/`, `frontend/`, `infra/`, `docs/`
3. AWS CDK bootstrap (I'll need your AWS creds)
4. Scaffold backend + frontend
5. First database migration

---

*This plan is a living document. We update it every Friday after demo.*
