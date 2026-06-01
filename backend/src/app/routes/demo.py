"""Demo data seed — pre-built skills and workflows for demo tenants."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.auth import get_current_user
from src.app.database import get_db
from src.app.models.user import User
from src.app.models.skill import Skill
from src.app.models.workflow import Workflow

router = APIRouter(prefix="/api/demo", tags=["demo"])

# ── Pre-built Skills ─────────────────────────────────────────────────

DEMO_SKILLS = [
    {
        "name": "Policy Brief",
        "description": "Formats research notes into a professional government policy brief with executive summary, background, analysis, and recommendations.",
        "trigger_command": "/policy-brief",
        "definition_str": """## Policy Brief Skill

This skill takes research notes and formats them into a structured government policy brief.

### Inputs
- `topic` (string, required): The policy topic
- `research_notes` (string, required): Raw research notes or findings
- `target_audience` (string, optional): Who the brief is for (e.g. "Minister", "Department Head")

### Process
1. Read the research notes carefully
2. Structure the output as a formal policy brief with these sections:
   - **Executive Summary** (2-3 paragraphs summarising the key issue, findings, and recommendation)
   - **Background** (context, why this matters, relevant history)
   - **Key Findings** (bullet points of the most important research outcomes)
   - **Analysis** (implications, risks, opportunities)
   - **Recommendations** (clear, actionable next steps)
   - **Next Steps** (who needs to do what, timeline)
3. Keep the tone formal and objective — this is a government document
4. Use Australian English spelling (organisation, analyse, centre, etc.)

### Outputs
- `brief`: The full formatted policy brief as text
- `word_count`: Approximate word count of the brief
- `sections`: List of section headings generated""",
    },
    {
        "name": "Meeting Minutes",
        "description": "Converts meeting notes or transcripts into structured minutes with action items, decisions, and attendees.",
        "trigger_command": "/minutes",
        "definition_str": """## Meeting Minutes Skill

Takes raw meeting notes or transcripts and produces formal meeting minutes.

### Inputs
- `meeting_title` (string, required): Name of the meeting
- `date` (string, required): Meeting date
- `attendees` (string, required): Comma-separated list of attendees
- `notes` (string, required): Raw meeting notes or transcript
- `chairperson` (string, optional): Who chaired the meeting

### Process
1. Review all notes/transcript content
2. Structure into formal minutes:
   - **Meeting Title, Date, Location**
   - **Attendees** (present, apologies)
   - **Agenda Items** (numbered, each with discussion summary)
   - **Decisions Made** (clear record of each decision)
   - **Action Items** (who, what, by when)
   - **Next Meeting** (date/time if known)
3. Extract action items as a table: Owner | Action | Due Date
4. Use clear, concise language — minutes are a record, not a transcript

### Outputs
- `minutes`: The full formatted meeting minutes
- `action_items`: Numbered list of action items with owners
- `decisions`: List of decisions made during the meeting""",
    },
    {
        "name": "Research & Summarise",
        "description": "Researches a topic using web sources and produces a structured summary with key findings and sources.",
        "trigger_command": "/research",
        "definition_str": """## Research & Summarise Skill

Researches a given topic and produces a clear, structured summary.

### Inputs
- `topic` (string, required): The topic to research
- `depth` (string, optional): "brief", "standard", or "deep" (default: "standard")
- `focus_areas` (string, optional): Comma-separated specific aspects to cover

### Process
1. If web fetch tools are available, use them to gather current information on the topic
2. Organise findings into clear sections
3. For each key claim or statistic, note the source
4. Structure the output:
   - **Overview** (2-3 sentences on what this is)
   - **Key Findings** (bullet points of the most important information)
   - **Details** (deeper dive organised by sub-topic)
   - **Sources** (list of references with URLs where available)
5. Be objective — present multiple perspectives where relevant
6. Flag uncertainty: note if information is dated, contested, or incomplete
7. Use Australian English spelling

### Outputs
- `summary`: The full research summary with findings organised by theme
- `key_points`: Bullet list of the most important takeaways
- `sources`: List of sources referenced""",
    },
    {
        "name": "Document QA",
        "description": "Reviews a document for quality, completeness, and compliance against standards.",
        "trigger_command": "/qa-review",
        "definition_str": """## Document QA Review Skill

Reviews documents for quality, completeness, and compliance.

### Inputs
- `document_title` (string, required): Title of the document being reviewed
- `document_content` (string, required): The full document text to review
- `document_type` (string, optional): Type of document (e.g. "policy", "brief", "report")
- `qa_standards` (string, optional): Specific standards to check against

### Process
1. Read the full document carefully
2. Review against these criteria:
   - **Completeness**: Are all required sections present?
   - **Clarity**: Is the language clear and unambiguous?
   - **Consistency**: Is terminology used consistently?
   - **Structure**: Is the document well-organised?
   - **Tone**: Is the tone appropriate for the audience?
   - **Spelling & Grammar**: Are there errors?
3. For each issue found, note the specific location and suggested fix
4. Score each category as: ✅ Pass | ⚠️ Minor Issue | ❌ Needs Work
5. Provide an overall assessment and recommendation

### Outputs
- `qa_report`: The full QA review with per-category scores
- `issues_found`: List of specific issues with locations and suggestions
- `overall_score`: Pass / Conditional Pass / Needs Revision
- `recommendation`: Recommended next action""",
    },
]


# ── Pre-built Workflows ─────────────────────────────────────────────

DEMO_WORKFLOWS = [
    {
        "name": "New Policy Approval Process",
        "description": "Researches a policy topic, drafts a formal brief, runs QA, and pauses for human approval before finalising.",
        "trigger": "chat",
        "definition": {
            "name": "New Policy Approval Process",
            "trigger": "chat",
            "tasks": [
                {
                    "id": "task_1",
                    "type": "skill",
                    "skill": "Research & Summarise",
                    "description": "Research the policy topic and gather key findings",
                    "depends_on": [],
                    "inputs": {
                        "topic": "{{task.topic}}",
                        "depth": "standard"
                    },
                    "outputs": {
                        "summary": "Research findings and key points",
                        "key_points": "List of important takeaways",
                        "sources": "Referenced sources"
                    }
                },
                {
                    "id": "task_2",
                    "type": "skill",
                    "skill": "Policy Brief",
                    "description": "Draft a formal policy brief from the research",
                    "depends_on": ["task_1"],
                    "inputs": {
                        "topic": "{{task.topic}}",
                        "research_notes": "{{task_1.summary}}"
                    },
                    "outputs": {
                        "brief": "Full policy brief document",
                        "sections": "List of section headings"
                    }
                },
                {
                    "id": "task_3",
                    "type": "skill",
                    "skill": "Document QA",
                    "description": "Review the draft policy brief for quality and completeness",
                    "depends_on": ["task_2"],
                    "inputs": {
                        "document_title": "Policy Brief: {{task.topic}}",
                        "document_content": "{{task_2.brief}}",
                        "document_type": "policy brief"
                    },
                    "outputs": {
                        "qa_report": "QA review results",
                        "overall_score": "Pass / Conditional / Needs Revision"
                    }
                },
                {
                    "id": "task_4",
                    "type": "human_approval",
                    "skill": None,
                    "description": "Review and approve the final policy brief before distribution",
                    "depends_on": ["task_3"],
                    "inputs": {
                        "task_3.qa_report": "QA results for reviewer"
                    },
                    "outputs": {
                        "approved": "Whether the brief was approved",
                        "feedback": "Reviewer feedback"
                    }
                }
            ],
            "checkpoints": [
                {
                    "task_id": "task_4",
                    "on_approve": "Finalise and distribute the policy brief",
                    "on_reject": "Return to task_2 with reviewer feedback for revision"
                }
            ]
        }
    },
    {
        "name": "Weekly Briefing Note Pipeline",
        "description": "Gathers intelligence, summarises key developments, formats a briefing note, and sends for review.",
        "trigger": "scheduled",
        "schedule": "0 9 * * 1",
        "definition": {
            "name": "Weekly Briefing Note Pipeline",
            "trigger": "scheduled",
            "tasks": [
                {
                    "id": "task_1",
                    "type": "skill",
                    "skill": "Research & Summarise",
                    "description": "Gather key developments and news for the week",
                    "depends_on": [],
                    "inputs": {
                        "topic": "Key developments in [department portfolio] this week",
                        "depth": "brief"
                    },
                    "outputs": {
                        "summary": "Weekly developments summary",
                        "key_points": "Key takeaways"
                    }
                },
                {
                    "id": "task_2",
                    "type": "skill",
                    "skill": "Meeting Minutes",
                    "description": "Format the briefing into structured note format",
                    "depends_on": ["task_1"],
                    "inputs": {
                        "meeting_title": "Weekly Briefing Note",
                        "date": "{{task.current_date}}",
                        "attendees": "Department Leadership",
                        "notes": "{{task_1.summary}}",
                        "chairperson": "Department Head"
                    },
                    "outputs": {
                        "minutes": "Formatted briefing note",
                        "action_items": "Action items from the briefing"
                    }
                },
                {
                    "id": "task_3",
                    "type": "human_approval",
                    "skill": None,
                    "description": "Review the briefing note before distribution",
                    "depends_on": ["task_2"],
                    "inputs": {
                        "briefing": "Draft briefing note for review"
                    },
                    "outputs": {
                        "approved": "Whether the briefing was approved",
                        "feedback": "Reviewer comments"
                    }
                }
            ],
            "checkpoints": [
                {
                    "task_id": "task_3",
                    "on_approve": "Distribute briefing to leadership team",
                    "on_reject": "Flag for revision with reviewer feedback"
                }
            ]
        }
    },
    {
        "name": "FOI Request Handling",
        "description": "Logs an FOI request, searches internal documents, drafts a response, and routes through legal review.",
        "trigger": "chat",
        "definition": {
            "name": "FOI Request Handling",
            "trigger": "chat",
            "tasks": [
                {
                    "id": "task_1",
                    "type": "skill",
                    "skill": "Meeting Minutes",
                    "description": "Log and categorise the FOI request details",
                    "depends_on": [],
                    "inputs": {
                        "meeting_title": "FOI Request: {{task.request_id}}",
                        "date": "{{task.current_date}}",
                        "attendees": "FOI Officer",
                        "notes": "{{task.request_details}}"
                    },
                    "outputs": {
                        "minutes": "Logged FOI request",
                        "action_items": "Required actions"
                    }
                },
                {
                    "id": "task_2",
                    "type": "skill",
                    "skill": "Research & Summarise",
                    "description": "Search internal documents relevant to the FOI request",
                    "depends_on": ["task_1"],
                    "inputs": {
                        "topic": "Internal documents related to: {{task.request_details}}",
                        "depth": "deep"
                    },
                    "outputs": {
                        "summary": "Relevant document findings",
                        "sources": "Document references"
                    }
                },
                {
                    "id": "task_3",
                    "type": "skill",
                    "skill": "Policy Brief",
                    "description": "Draft FOI response based on findings",
                    "depends_on": ["task_2"],
                    "inputs": {
                        "topic": "FOI Response: {{task.request_id}}",
                        "research_notes": "{{task_2.summary}}"
                    },
                    "outputs": {
                        "brief": "Draft FOI response",
                        "sections": "Response sections"
                    }
                },
                {
                    "id": "task_4",
                    "type": "human_approval",
                    "skill": None,
                    "description": "Legal review and approval of FOI response",
                    "depends_on": ["task_3"],
                    "inputs": {
                        "draft_response": "Draft FOI response for legal review"
                    },
                    "outputs": {
                        "approved": "Whether the response was approved",
                        "feedback": "Legal review feedback"
                    }
                }
            ],
            "checkpoints": [
                {
                    "task_id": "task_4",
                    "on_approve": "Finalise and send FOI response to requester",
                    "on_reject": "Return to task_3 with legal feedback for revision"
                }
            ]
        }
    },
]


# ── Seed Endpoint ────────────────────────────────────────────────────


@router.post("/seed", status_code=status.HTTP_201_CREATED)
async def seed_demo_data(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Seed the current user's tenant with demo skills and workflows."""
    tenant_id = current_user.tenant_id
    now = datetime.now(timezone.utc)

    created_skills = []
    created_workflows = []

    # ── Create Skills ──────────────────────────────────────────
    for skill_data in DEMO_SKILLS:
        # Check if skill already exists for this tenant
        existing = await db.execute(
            select(Skill).where(
                Skill.name == skill_data["name"],
                Skill.tenant_id == tenant_id,
                Skill.owner_id == current_user.id,
            )
        )
        if existing.scalar_one_or_none():
            continue  # Skip if already exists

        skill = Skill(
            id=uuid.uuid4(),
            name=skill_data["name"],
            description=skill_data["description"],
            trigger_command=skill_data["trigger_command"],
            definition_str=skill_data["definition_str"],
            owner_id=current_user.id,
            tenant_id=tenant_id,
            visibility="private",
            status="active",
            created_at=now,
            updated_at=now,
        )
        db.add(skill)
        created_skills.append(skill_data["name"])

    await db.flush()

    # ── Create Workflows ───────────────────────────────────────
    for wf_data in DEMO_WORKFLOWS:
        existing = await db.execute(
            select(Workflow).where(
                Workflow.name == wf_data["name"],
                Workflow.owner_id == current_user.id,
            )
        )
        if existing.scalar_one_or_none():
            continue

        wf = Workflow(
            id=uuid.uuid4(),
            name=wf_data["name"],
            description=wf_data["description"],
            trigger=wf_data.get("trigger", "chat"),
            definition=json.dumps(wf_data["definition"]),
            source_text=None,
            schedule=wf_data.get("schedule"),
            status="active",
            owner_id=current_user.id,
            tenant_id=tenant_id,
            created_at=now,
            updated_at=now,
        )
        db.add(wf)
        created_workflows.append(wf_data["name"])

    await db.flush()

    return {
        "status": "ok",
        "tenant_id": str(tenant_id),
        "skills_created": created_skills,
        "workflows_created": created_workflows,
        "message": (
            f"Demo data seeded: {len(created_skills)} skills, "
            f"{len(created_workflows)} workflows"
        ),
    }


@router.get("/seed")
async def get_demo_seed_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Check what demo data exists for the current user."""
    skill_count = await db.execute(
        select(Skill).where(
            Skill.owner_id == current_user.id,
            Skill.name.in_([s["name"] for s in DEMO_SKILLS]),
        )
    )
    existing_skills = {s.name for s in list(skill_count.scalars().all())}

    wf_count = await db.execute(
        select(Workflow).where(
            Workflow.owner_id == current_user.id,
            Workflow.name.in_([w["name"] for w in DEMO_WORKFLOWS]),
        )
    )
    existing_wfs = {w.name for w in list(wf_count.scalars().all())}

    available_skills = [s["name"] for s in DEMO_SKILLS]
    available_wfs = [w["name"] for w in DEMO_WORKFLOWS]

    return {
        "is_seeded": len(existing_skills) == len(available_skills) and len(existing_wfs) == len(available_wfs),
        "skills": {
            "available": available_skills,
            "existing": sorted(existing_skills),
            "missing": [s for s in available_skills if s not in existing_skills],
        },
        "workflows": {
            "available": available_wfs,
            "existing": sorted(existing_wfs),
            "missing": [w for w in available_wfs if w not in existing_wfs],
        },
    }
