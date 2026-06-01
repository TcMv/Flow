"""Agent tools for skill creation and retrieval."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.agent.tools import Tool
from src.app.models.skill import Skill


class CreateSkill(Tool):
    """Save a reusable skill from chat. The agent calls this when a user asks to save something as a skill."""

    name: str = "create_skill"
    description: str = (
        "Save a reusable skill so the user can invoke it later. "
        "Call this when the user says 'save this as a skill', 'remember this as a skill', "
        "or asks you to create a named capability they can reuse. "
        "You provide the name, description, optional trigger command (e.g. '/brief'), "
        "and the full definition of what the skill does (steps, inputs, outputs)."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Short name for the skill, e.g. 'Policy Brief' or 'Research Assistant'",
            },
            "description": {
                "type": "string",
                "description": "One-line description of what this skill does",
            },
            "trigger_command": {
                "type": "string",
                "description": "Optional command to trigger this skill, e.g. '/brief' or '/research'. Must start with /",
            },
            "definition_str": {
                "type": "string",
                "description": (
                    "Full definition of what the skill does. Include: "
                    "step-by-step instructions, what inputs it needs, "
                    "how it processes them, what it outputs, and any "
                    "clarifying questions it might ask the user along the way. "
                    "Be thorough — this definition will be loaded when the skill is invoked."
                ),
            },
        },
        "required": ["name", "description", "definition_str"],
    }

    def __init__(self, db: AsyncSession | None = None, user_id: Any = None, tenant_id: Any = None) -> None:
        self._db = db
        self._user_id = user_id
        self._tenant_id = tenant_id

    async def execute(self, **kwargs: Any) -> str:
        name = kwargs.get("name", "").strip()
        description = kwargs.get("description", "").strip()
        trigger_command = kwargs.get("trigger_command", "").strip() or None
        definition_str = kwargs.get("definition_str", "").strip()

        if not name:
            return "Error: 'name' is required."

        if not self._db or not self._user_id or not self._tenant_id:
            return "Error: Skill database not available in this context."

        # Check for duplicate trigger command
        if trigger_command:
            existing = await self._db.execute(
                select(Skill).where(
                    Skill.trigger_command == trigger_command,
                    Skill.owner_id == self._user_id,
                    Skill.visibility == "private",
                )
            )
            if existing.scalar_one_or_none():
                return f"A skill with trigger command '{trigger_command}' already exists. Please use a different command."

        from uuid import uuid4
        from datetime import datetime, timezone

        skill = Skill(
            id=uuid4(),
            name=name,
            description=description,
            trigger_command=trigger_command,
            definition_str=definition_str,
            owner_id=self._user_id,
            tenant_id=self._tenant_id,
            visibility="private",
            status="active",
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        self._db.add(skill)
        await self._db.flush()

        cmd_note = f" Use the command `{trigger_command}` to invoke it." if trigger_command else ""
        return (
            f"Skill '{name}' created successfully!{cmd_note}\n\n"
            f"Trigger command: {trigger_command or 'None (invoke by name)'}\n"
            f"Definition length: {len(definition_str)} characters\n\n"
            f"Users can now invoke this skill by name or trigger command in chat."
        )


class GetSkill(Tool):
    """Look up a saved skill by name or trigger command. Returns the full definition."""

    name: str = "get_skill"
    description: str = (
        "Look up a saved skill by name or trigger command. "
        "Use this when the user mentions a skill name or types a command like '/brief'. "
        "Returns the skill's full definition so you can execute it."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The skill name or trigger command to look up, e.g. 'Policy Brief' or '/brief'",
            },
        },
        "required": ["query"],
    }

    def __init__(self, db: AsyncSession | None = None, user_id: Any = None, tenant_id: Any = None) -> None:
        self._db = db
        self._user_id = user_id
        self._tenant_id = tenant_id

    async def execute(self, **kwargs: Any) -> str:
        query = kwargs.get("query", "").strip()
        if not query:
            return "Error: 'query' is required."

        if not self._db:
            return "Error: Skill database not available."

        # Search by name or trigger_command, for this user's skills + marketplace
        from sqlalchemy import or_

        stmt = select(Skill).where(
            Skill.tenant_id == self._tenant_id,
            or_(
                Skill.name.ilike(f"%{query}%"),
                Skill.trigger_command == query,
            ),
            or_(
                Skill.owner_id == self._user_id,
                Skill.visibility == "marketplace",
            ),
        )
        result = await self._db.execute(stmt)
        skills = list(result.scalars().all())

        if not skills:
            return f"No skill found matching '{query}'. You can create one using the create_skill tool."

        # Return the best match (exact trigger command match first, then name match)
        exact = [s for s in skills if s.trigger_command == query]
        best = exact[0] if exact else skills[0]

        owner_name = best.owner.name if best.owner else "Unknown"
        return (
            f"**Skill: {best.name}**\n"
            f"Description: {best.description}\n"
            f"Trigger: {best.trigger_command or 'None'}\n"
            f"Visibility: {best.visibility}\n"
            f"Status: {best.status}\n"
            f"Owner: {owner_name}\n\n"
            f"--- Definition ---\n"
            f"{best.definition_str}\n"
            f"--- End Definition ---"
        )


class ListMySkills(Tool):
    """List all the user's saved skills."""

    name: str = "list_my_skills"
    description: str = (
        "List all skills the current user has created. "
        "Returns skill names, descriptions, and trigger commands."
    )
    parameters: dict = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    def __init__(self, db: AsyncSession | None = None, user_id: Any = None) -> None:
        self._db = db
        self._user_id = user_id

    async def execute(self, **kwargs: Any) -> str:
        if not self._db or not self._user_id:
            return "Error: Database not available."

        result = await self._db.execute(
            select(Skill)
            .where(Skill.owner_id == self._user_id)
            .order_by(Skill.updated_at.desc())
            .limit(50)
        )
        skills = list(result.scalars().all())

        if not skills:
            return "You don't have any skills yet. Ask me to save something as a skill and I can create one for you!"

        lines = [f"Your skills ({len(skills)}):"]
        for s in skills:
            cmd = f" [`{s.trigger_command}`]" if s.trigger_command else ""
            lines.append(f"  • {s.name}{cmd} — {s.description or 'No description'}")
        return "\n".join(lines)
