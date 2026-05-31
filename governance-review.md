# Governance Review: Flow AI Agent Platform

**Review Date:** 1 June 2026
**Prepared by:** Joint Finance & Legal/Compliance Task Force
**Subject:** Proposed self-hosted AI agent platform — "Flow"
**Status:** Pre-commitment review (no resources committed yet)

---

## Executive Summary

Flow is a proposed self-hosted AI agent platform where every employee gets a personalised AI agent with skills, skill sharing, and process-to-workflow automation. The build plan relies on Hermes + Claude Code + Codex as the dev team, with zero budget commitment and an AWS Free Tier foundation.

**Overall Assessment: CONDITIONAL PROCEED.**
Both teams agree the initiative is viable as a zero-budget proof-of-concept build, but with firm structural, legal, and financial guardrails that must be established before day one of client-facing operations. The three-phase gating framework below is the key recommendation.

---

## 1. Finance Assessment (COO_Finance)

### 1.1 Financial Risk: Building with No Pre-Sold Customers

**Risk Rating: MODERATE (but manageable)**

Building without pre-sold customers is the single biggest financial risk. However, the proposed model mitigates this significantly:

| Risk Factor | Severity | Mitigation |
|---|---|---|
| No committed revenue during build | High | Zero-budget dev spend limits downside |
| Opportunity cost of Taran's time | Medium | No hard deadline; 14-week timeline is a target, not a burn-rate constraint |
| Product-market fit uncertainty | High | Using Hermes (existing tool) as foundation de-risks core tech risk |
| Competition in agent platform space | Medium | Government compliance niche is a defensible moat |

**Verdict:** Building first, selling later is acceptable **only** because the financial outlay is near-zero. The primary cost is Taran's time, which is recoverable (skills transfer to other uses). If even $1,000/month of cash burn were required, the answer would be **do not proceed** without a committed pilot customer.

### 1.2 Cost Exposure: If the Product Can't Be Sold After 14 Weeks

**Maximum downside: ~$0–$70 + ~200 hours of Taran's time**

| Cost Category | 14-Week Estimate | Notes |
|---|---|---|
| AWS infra (Free Tier) | $0 | First 12 months within Free Tier limits |
| AWS overage (contingency) | $0–$50 | Only if Lambda/EC2 usage exceeds Free Tier |
| Domain name (flow.dev or similar) | $10–$20 | One-time annual cost |
| LLM API keys for dev/testing | $0 | Taran's existing keys; BYO-LLM is the product model |
| Total cash outlay | **$10–$70** | Negligible |
| Taran's time (opportunity cost) | ~200 hours | ~3-4 hrs/day × 5 days × 14 weeks |

**Worst case scenario:** The product doesn't sell. Taran has lost ~200 hours and $70. The codebase remains as a portfolio asset and can be repurposed. The Hermes/Claude Code/Codex skills gained transfer directly to future projects.

**Verdict:** This is one of the lowest-risk product builds possible. The break-even point is selling a single license.

### 1.3 Dev Spend: Is $0–$5/Month Sensible? Contingency?

**YES, but budget a small contingency.**

The AWS Free Tier is genuinely generous for a single-developer build:
- 750 hrs/month EC2 (t2.micro/t3.micro) — sufficient for dev
- 1 million Lambda requests/month
- 25 GB DynamoDB storage
- 1 million API Gateway calls/month

**Recommendation:** Budget **$50 total contingency** for the 14-week build. Use cases:
- If a paid AWS service is needed (e.g., RDS, higher-tier EC2 for testing)
- Domain registration ($10–$20/year)
- One month of a paid service if Free Tier limits are hit

**Don't upgrade to paid tiers preemptively.** The Free Tier limitation is a forcing function for lean architecture, which is a feature, not a bug, at this stage.

### 1.4 Kill Criteria (When to Stop and Reassess)

Three hard gates must be passed before continuing to the next phase.

#### Phase 1: Core Prototype (Weeks 1–4)
| Kill Criterion | Trigger | Action |
|---|---|---|
| No working MVP with a single skill | End of week 4 | Stop. Technical basis is unproven |
| Taran disengaged for >7 consecutive days | Any point | Stop. Single-founder dependency is real |
| Architecture review reveals >$100/month minimum viable infra | End of week 2 | Re-scope to reduce infra needs or pause |

**Phase 1 gate: Working demo with exactly ONE skill that runs end-to-end.**

#### Phase 2: Dogfooding (Weeks 5–10)
| Kill Criterion | Trigger | Action |
|---|---|---|
| <3 internal users actively using the platform after 4 weeks of dogfooding | End of week 8 | Product-market fit failure; stop or pivot |
| Critical security vulnerability found requiring paid services | Any point | Reassess budget and timeline |
| No identified pilot customer with LOI by end of week 10 | End of week 10 | Do NOT proceed to Phase 3 (client-ready) |

**Phase 2 gate: At least one Letter of Intent (LOI) from a prospective government client.**

#### Phase 3: Client-Ready (Weeks 11–14)
| Kill Criterion | Trigger | Action |
|---|---|---|
| Legal structure not established (see §2.5) | Start of week 11 | Do not begin Phase 3 |
| Compliance framework not documented | End of week 12 | Delay client onboarding |
| JAWS or NIST 800-53 gap analysis not performed | End of week 13 | Do not enter client discussions |
| No budget allocated for Phase 3 legal/compliance costs | End of week 11 | Pause until funded |

**Phase 3 gate: Legal entity, compliance documentation, and funded audit budget.**

### 1.5 Revenue Projections (When We Sell)

These are directional only — no hard revenue data exists for this exact product category. Projections are based on comparable B2B SaaS agent platforms and government IT consulting rates.

#### Conservative Scenario
| Metric | Year 1 | Year 2 | Year 3 |
|---|---|---|---|
| Clients | 1 pilot | 3–5 | 8–12 |
| Seats per client (avg) | 50 | 75 | 100 |
| Price per seat/month | $15 | $20 | $25 |
| Annual revenue | ~$9,000 | ~$54,000–$90,000 | ~$240,000–$360,000 |

#### Moderate Scenario
| Metric | Year 1 | Year 2 | Year 3 |
|---|---|---|---|
| Clients | 2 | 6–10 | 15–25 |
| Seats per client (avg) | 50 | 100 | 150 |
| Price per seat/month | $20 | $25 | $30 |
| Annual revenue | ~$24,000 | ~$180,000–$300,000 | ~$810,000–$1.35M |

#### Aggressive Scenario
| Metric | Year 1 | Year 2 | Year 3 |
|---|---|---|---|
| Clients | 3 | 10–15 | 25–50 |
| Seats per client (avg) | 100 | 150 | 200 |
| Price per seat/month | $25 | $30 | $40 |
| Annual revenue | ~$90,000 | ~$540,000–$810,000 | ~$2.4M–$4.8M |

**Key assumptions:**
- Government sales cycles are 6–12 months. Year 1 revenue will start in Q3/Q4 at earliest.
- Pricing is per-seat/month with volume discounts for 500+ seats.
- Enterprise license model (self-hosted on client infra) may command 2–3× premium over SaaS.
- Support/maintenance fees at 20% of license value are standard for government contracts.

**Finance recommends targeting the moderate scenario for planning purposes.**

---

## 2. Legal & Compliance Assessment (COO_Legal)

### 2.1 Legal/Compliance Risks: AI Agent Platform for Government

**Risk Rating: HIGH — but manageable with early investment in compliance.**

Selling to government clients introduces several non-negotiable requirements:

| Risk Area | Severity | Details |
|---|---|---|
| **AI Governance Frameworks** | Critical | Australian Gov: AU Govt AI Ethics Principles (8 principles, mandatory from 2024). NIST AI Risk Management Framework (US). EU AI Act (if EU clients). Australia's Digital Transformation Agency (DTA) AI Assurance Framework. |
| **Security & Accreditation** | Critical | IRAP assessment for Australian Gov (Protected level minimum). FedRAMP equivalent in US. ISO 27001 certification often a baseline requirement for government SaaS. |
| **Accessibility** | High | WCAG 2.2 Level AA compliance legally required for government-facing digital products in Australia (Disability Discrimination Act 1992). |
| **Record-Keeping** | High | Public records legislation (e.g., Archives Act 1983 in Australia) requires that government communications via AI agents are logged, retainable, and discoverable. |
| **Procurement Rules** | High | Government panels (e.g., Digital Marketplace, DTA Panel). Must be on panel to sell. Panel application can take 3–6 months. |

**Critical Red Flag:** You cannot sell an AI product to an Australian government agency without IRAP certification or a System Security Plan (SSP) that the agency's CISO signs off on. IRAP assessment costs $20k–$80k+ and takes 3–6 months. **This is the single biggest barrier to entry.**

**Recommendation for Build Phase:**
- Self-host on Taran's AWS account with Free Tier for development — **no government data touches this environment**.
- Document the architecture from day one as if preparing for IRAP (this is cheap to do now, expensive to retrofit).
- Engage with DTA's AI Assurance Framework documentation proactively.

### 2.2 AWS Free Tier: Future Compliance Issues

**Assessment: LOW RISK for dev, DO NOT USE for client workloads.**

| Phase | AWS Account | Acceptable? |
|---|---|---|
| Development (Weeks 1–14) | Taran's personal AWS Free Tier | Yes — no client data, no compliance obligations |
| Internal dogfooding | Taran's personal AWS Free Tier | Conditional — only if no real client data is used |
| Pilot client | Dedicated AWS GovCloud or AU-based region | Required — must be client-owned or Flow-entity-owned account |
| Production (AU Gov clients) | AWS Sydney (ap-southeast-2) with appropriate compliance certifications | Required — data sovereignty mandates Australian-resident data |

**Key compliance requirements that Free Tier does NOT satisfy:**
- No encryption key management (KMS costs money)
- No CloudTrail retention beyond 90 days (need S3 for longer retention)
- No VPC Flow Logs (extra cost)
- No AWS Shield Advanced for DDoS protection
- No guaranteed uptime SLAs
- No HIPAA/BAA eligibility (irrelevant for AU gov but illustrative of Free Tier limitations)

**Recommendation:** Free Tier is fine for dev. Create a separate "Flow-entity" AWS account once the legal entity is established (Phase 3). Do NOT migrate client data through the personal account at any point.

### 2.3 Data Sovereignty, IP, and Contracts: Day-One Considerations

#### Data Sovereignty
| Requirement | Action Needed |
|---|---|
| Australian Government data must stay in Australia | Ensure all infrastructure uses AWS ap-southeast-2 (Sydney) for AU clients |
| State-level requirements may differ | QLD, NSW, VIC all have variations on data residency — check per-state DPC/CDO guidance |
| Client's data is THEIR data | Contracts must explicitly state the client retains full ownership of all data processed by Flow |
| Logs and metadata may also be subject to sovereignty | Don't assume only "content" data counts — metadata (who asked which agent what) is also a record |

#### Intellectual Property
| Asset | Who Owns It? | Notes |
|---|---|---|
| Flow platform codebase | Flow legal entity | Taran assigns IP via IP deed upon entity formation |
| Skills built by Flow | Flow legal entity | Unless commissioned by client for their exclusive use |
| Client-specific workflows/configs | Client | Treat as client IP; license Flow to use for service delivery |
| Hermes/Claude Code/Codex output | Muddled | These are tools, not sources of IP claims, but the legal status of AI-generated code is unsettled. Mitigate: human review of all generated code before production deployment. |

**Immediate actions needed (Week 1):**
1. **GitHub repository ownership:** Create the repo under Taran's personal account for now, but document that all IP will be assigned to the entity at formation.
2. **Contributor agreements:** If anyone else touches the codebase (even for small PRs), get an assignment agreement.
3. **Third-party dependency audit:** Track all open-source licenses used (MIT, Apache 2.0 are fine; GPL/AGPL can force source release — flag these).

#### Contracts
Start templating now for:
- **Master Services Agreement (MSA)** — the umbrella contract
- **Data Processing Agreement (DPA)** — GDPR/Privacy Act compliance
- **Service Level Agreement (SLA)** — uptime, support hours, response times
- **Acceptable Use Policy (AUP)** — what the client can't do with their agents
- **IP and Confidentiality Deed** — standard government requirement

**Don't use AI-generated contracts without a lawyer reviewing them.** Spend the money ($1k–$3k for a technology lawyer) when engaging first client.

### 2.4 Regulatory Red Flags: BYO-LLM Model

**Comfort Level: MODERATE.** The BYO-LLM model has advantages and risks.

| Aspect | Risk | Mitigation |
|---|---|---|
| **Data leakage to third-party LLM providers** | HIGH | Clients provide their own API keys to their preferred LLM provider. Flow does not proxy their data. Contractually disclaim liability for LLM provider's data handling. |
| **Liability for AI output** | MEDIUM | Who is liable when an AI agent gives bad advice? In a government context, this could be serious (incorrect policy advice, privacy breach, discrimination). Solution: (1) human-in-the-loop for high-stakes actions, (2) clear terms of use, (3) insurance. |
| **Model governance** | MEDIUM | Client may not understand that GPT-4o vs Claude vs local Llama have very different compliance profiles. Provide a "Model Suitability Matrix" that maps models to use case compliance requirements. |
| **API key security** | MEDIUM | Client API keys stored in Flow. Must be encrypted at rest (AWS KMS), managed via IAM, and the client must have the ability to rotate keys without downtime. |
| **Rate limiting and cost exposure** | LOW | Client uses their own API keys so they control spend, but a runaway agent loop could cost them. Build in agent cost controls (per-session limits, alerts, kill switches). |
| **Open-source models (local inference)** | LOW | Lowest risk option — data never leaves client infrastructure. Recommend this for sensitive government use cases. |

**Regulatory Red Flag — Australian Privacy Act:**
If the AI agent processes personal information (which it likely will — employee names, emails, performance data, inter-department communications), the Privacy Act 1988 applies. Key obligations:
- APP 1: Open and transparent management of personal information
- APP 5: Notification of collection
- APP 11: Security of personal information
- Notifiable Data Breaches (NDB) scheme: Must report eligible data breaches

**The BYO-LLM model does not absolve Flow of Privacy Act obligations.** Flow still controls the platform that processes the data. Flow must:
- Have a privacy policy that covers the platform
- Implement privacy-by-design
- Ensure data is securely deleted when a client terminates
- Have a data breach response plan

**Recommendation:** The BYO-LLM model is a net positive for compliance (client sees exactly where their data goes). Position it as a compliance feature, not a limitation.

### 2.5 Legal Structure

**Recommendation: New proprietary limited company (Pty Ltd) in Australia.**

| Structure | Pros | Cons | Verdict |
|---|---|---|---|
| **Taran personally (sole trader)** | Cheapest, simplest | Unlimited liability; government clients won't sign with a sole trader; no IP protection; no ability to raise investment; hard to get insurance | **Do not use for government sales** |
| **Existing business (if one exists)** | Existing ABN/GST setup | Mixed liability; harder to sell or raise capital if the business is in a different sector | **Conditional — only if the existing business is a related technology entity** |
| **New Pty Ltd** | Limited liability; government-standard structure; clean IP assignment; can raise investment; can get insurance | Incorporation cost (~$500); annual ASIC fees (~$300); accounting costs ($1k–$3k/year) | **RECOMMENDED** |
| **New Trust + Corporate Trustee** | Asset protection; income distribution flexibility | Higher cost; overkill for a pre-revenue startup | **Not recommended at this stage** |
| **US Delaware C-Corp** | Standard for VC fundraising | No Australian government client will sign with a US entity for data sovereignty reasons | **Do not use** |

**Recommended timeline for entity formation:**

| Timeline | Action | Cost |
|---|---|---|
| **Week 1** | Reserve business name (ASIC check) | ~$50 |
| **Week 1** | Register domain (flow.dev / flowagent.com / flowgov.ai) | $10–$20/yr |
| **Weeks 1–4** | Build on personal account; document all IP | $0 |
| **End of Week 4** | (Phase 1 gate passed) Register Pty Ltd, get ABN, TFN, GST registration | ~$500 |
| **End of Week 4** | Assign all IP from Taran to company via IP deed | ~$500 (lawyer) |
| **Weeks 5–10** | Open company bank account, set up company AWS account, get public liability + professional indemnity insurance (see below) | $2k–$5k one-off |
| **End of Week 10** | (Phase 2 gate passed) Move all infrastructure to company AWS account | $0 (Free Tier available for new accounts) |
| **Weeks 11–14** | Engage lawyer for MSA/DPA/SLA templates, begin IRAP pre-assessment, apply to government procurement panels | $3k–$8k |

**Insurance requirements for government clients:**
- Professional Indemnity: $5M–$20M (mandatory for most government contracts)
- Public Liability: $10M–$20M
- Cyber Insurance: $5M–$10M (increasingly mandatory)
- Directors & Officers: Recommended once entity exists

*Estimated annual premiums for early-stage tech: $2k–$5k total (excluding Cyber, which may be $3k–$8k).*

---

## 3. Merged Recommendations

### 3.1 Proceed Status: CONDITIONAL PROCEED

Both teams agree Flow should proceed, subject to strict adherence to the phase-gated framework.

### 3.2 Critical Path (Non-Negotiable)

1. **Week 1:** Reserve company name, register domain, document IP tracking
2. **Week 4 (Phase 1 Gate):** Working MVP with one skill. **No gate pass = stop.**
3. **Week 4:** Incorporate Pty Ltd, assign IP, get ABN/GST
4. **Weeks 5–10 (Phase 2):** Dogfood internally, secure at least one LOI. **No LOI by week 10 = stop.**
5. **Week 10 (Phase 2 Gate):** Legal entity active, insurance in place, compliance documentation started
6. **Weeks 11–14 (Phase 3):** Ready for first client engagement

### 3.3 Hard No-Gos

Under no circumstances should you:
- ✅ Use the Free Tier account for ANY client data, even in demo environments
- ✅ Sell to a government client without proper entity structure (Pty Ltd)
- ✅ Deploy to a government client without IRAP assessment (or SSP/CISO sign-off)
- ✅ Accept a contract of any value without lawyer-reviewed MSA and DPA
- ✅ Let the AI agents operate without human-in-the-loop on any decision with real-world consequences

### 3.4 Recommended Immediate Actions (This Week)

| Priority | Action | Owner | Cost |
|---|---|---|---|
| 🔴 P0 | Reserve company name + register domain | Taran | ~$70 |
| 🔴 P0 | Set up IP tracking log (who wrote what, date, repo) | Taran | $0 |
| 🟡 P1 | Read DTA AI Assurance Framework docs | Taran | 2 hrs |
| 🟡 P1 | Create Phase 1 architecture document (as if for IRAP) | Taran | 4 hrs |
| 🟢 P2 | Identify 3 target government clients + any warm intros | Taran | 2 hrs |
| 🟢 P2 | Start MSA/DPA template research | Taran | 2 hrs |
| ⚪ P3 | Get quotes for PI insurance ($5M) | Taran | 1 hr |

### 3.5 Total Estimated Pre-Revenue Legal/Compliance Spend

| Phase | Estimated Cost | Notes |
|---|---|---|
| Build (Weeks 1–14) | $0–$70 | Domain + name reservation |
| Entity setup (Week 4) | ~$1,000 | Incorporation + IP deed (lawyer) |
| Insurance (Weeks 5–8) | ~$5,000–$13,000 | PI + Cyber + Public Liability |
| Legal templates (Weeks 11–14) | ~$3,000–$5,000 | MSA, DPA, SLA, AUP |
| IRAP pre-assessment (pre-sales) | ~$5,000–$10,000 | Gap analysis only; full IRAP is $20k–$80k |
| **Total (to first client-ready)** | **~$14,000–$29,000** | |
| **Ongoing annual** | ~$5,000–$10,000 | ASIC fees, accounting, insurance renewal |

**Important:** The financial risk of the build phase ($0–$70) is negligible. The real financial exposure begins when legal/compliance costs kick in at Phase 3 (~$14k–$29k). **Do not enter Phase 3 without confirming the budget for this.**

---

## 4. Sign-Off Summary

| Team | Verdict | Conditions |
|---|---|---|
| **COO_Finance** | ✅ Proceed | Phase gates must be enforced. Zero-budget rule applies through Phase 2. |
| **COO_Legal** | ✅ Proceed with conditions | Entity must be formed before Phase 3. Compliance framework must precede client engagement. BYO-LLM model is sound. |
| **Joint** | ✅ CONDITIONAL PROCEED | Follow phase-gated framework. Stop if any gate fails. Budget $14k–$29k for Phase 3 legal/compliance. |

---

*This review was prepared based on the information provided in the Joint Task Force Brief dated 1 June 2026. All projections are directional. Legal advice from a qualified technology lawyer should be obtained before entering into client contracts. Compliance requirements may vary by jurisdiction and client type.*
