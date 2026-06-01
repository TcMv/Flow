"""Memory MCP tools — persistent knowledge graph for agent memory.

Stores entities, relations, and observations in a local JSONL file.
Every entry is scoped by tenant_id for multi-tenant isolation.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.app.agent.tools import Tool


# Memory storage (JSONL file, one per tenant)
_MEMORY_DIR = Path(os.environ.get("FLOW_MEMORY_DIR", "/tmp/flow-memory"))
_MEMORY_DIR.mkdir(parents=True, exist_ok=True)


def _memory_path(tenant_id: str | None) -> Path:
    """Get the memory file path for a tenant."""
    tid = tenant_id or "default"
    # Sanitize tenant ID for filename
    safe = tid.replace("-", "_")
    return _MEMORY_DIR / f"knowledge_{safe}.jsonl"


def _read_entries(tenant_id: str | None) -> list[dict]:
    """Read all memory entries for a tenant."""
    path = _memory_path(tenant_id)
    if not path.exists():
        return []
    entries = []
    try:
        with path.open("r") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        entries.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
    except OSError:
        return []
    return entries


def _append_entry(entry: dict, tenant_id: str | None) -> None:
    """Append a memory entry for a tenant."""
    path = _memory_path(tenant_id)
    with path.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def _delete_entries(predicate, tenant_id: str | None) -> int:
    """Delete entries matching a predicate. Rewrites the file."""
    path = _memory_path(tenant_id)
    if not path.exists():
        return 0
    entries = _read_entries(tenant_id)
    before = len(entries)
    entries = [e for e in entries if not predicate(e)]
    removed = before - len(entries)
    with path.open("w") as f:
        for e in entries:
            f.write(json.dumps(e) + "\n")
    return removed


class MemoryStore(Tool):
    """Store a fact or observation in persistent memory."""

    name: str = "mcp_memory_store"
    description: str = (
        "Store a fact, observation, or entity relationship in persistent memory. "
        "The agent can recall this information later. "
        "Use this when the user tells you something important to remember, "
        "or when you want to save knowledge across conversations. "
        "Supports three types:\n"
        "  - 'entity': Store information about a person, place, thing, or concept\n"
        "  - 'relation': Store a relationship between two entities\n"
        "  - 'observation': Store an observation about an existing entity"
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "description": "Type of memory to store: 'entity', 'relation', or 'observation'.",
                "enum": ["entity", "relation", "observation"],
            },
            "name": {
                "type": "string",
                "description": "Name of the entity (for 'entity' type) — the subject.",
            },
            "entity_type": {
                "type": "string",
                "description": "Type of entity, e.g. 'person', 'company', 'project', 'concept'. Only for 'entity' type.",
            },
            "observations": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of observations about this entity (for 'entity' type).",
            },
            "from_entity": {
                "type": "string",
                "description": "Source entity name (for 'relation' type).",
            },
            "to_entity": {
                "type": "string",
                "description": "Target entity name (for 'relation' type).",
            },
            "relation_type": {
                "type": "string",
                "description": "Type of relationship, e.g. 'works_at', 'reports_to', 'depends_on'. For 'relation' type.",
            },
            "entity_name": {
                "type": "string",
                "description": "Name of the entity to add an observation to (for 'observation' type).",
            },
            "content": {
                "type": "string",
                "description": "Observation content (for 'observation' type or additional context for others).",
            },
        },
        "required": ["type"],
    }

    def __init__(self, **kwargs):
        self._tenant_id = kwargs.get("tenant_id")
        self._user_id = kwargs.get("user_id")

    async def execute(self, **kwargs: Any) -> str:
        mem_type = kwargs.get("type", "").strip()

        if mem_type == "entity":
            name = kwargs.get("name", "").strip()
            if not name:
                return "Error: 'name' is required for entity type."
            entity_type = kwargs.get("entity_type", "general")
            observations = kwargs.get("observations", [])

            entry = {
                "id": str(uuid.uuid4()),
                "type": "entity",
                "name": name,
                "entityType": entity_type,
                "observations": observations,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "user_id": str(self._user_id) if self._user_id else None,
                "tenant_id": str(self._tenant_id) if self._tenant_id else None,
            }
            _append_entry(entry, self._tenant_id)
            obs_count = len(observations)
            return f"✅ Stored entity '{name}' ({entity_type}) with {obs_count} observation(s)"

        elif mem_type == "relation":
            from_e = kwargs.get("from_entity", "").strip()
            to_e = kwargs.get("to_entity", "").strip()
            rel_type = kwargs.get("relation_type", "").strip()

            if not from_e or not to_e or not rel_type:
                return "Error: 'from_entity', 'to_entity', and 'relation_type' are required for relation type."

            entry = {
                "id": str(uuid.uuid4()),
                "type": "relation",
                "from": from_e,
                "to": to_e,
                "relationType": rel_type,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "user_id": str(self._user_id) if self._user_id else None,
                "tenant_id": str(self._tenant_id) if self._tenant_id else None,
            }
            _append_entry(entry, self._tenant_id)
            return f"✅ Stored relation: '{from_e}' → [{rel_type}] → '{to_e}'"

        elif mem_type == "observation":
            entity_name = kwargs.get("entity_name", "").strip()
            content = kwargs.get("content", "").strip()

            if not entity_name or not content:
                return "Error: 'entity_name' and 'content' are required for observation type."

            # Find the entity and add observation
            entries = _read_entries(self._tenant_id)
            found = False
            for e in entries:
                if e.get("type") == "entity" and e.get("name") == entity_name:
                    if "observations" not in e:
                        e["observations"] = []
                    e["observations"].append(content)
                    found = True
                    break

            if found:
                # Rewrite the file
                path = _memory_path(self._tenant_id)
                with path.open("w") as f:
                    for e in entries:
                        f.write(json.dumps(e) + "\n")
                return f"✅ Added observation to '{entity_name}': {content}"
            else:
                # Store as a standalone observation
                entry = {
                    "id": str(uuid.uuid4()),
                    "type": "observation",
                    "entity_name": entity_name,
                    "content": content,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "user_id": str(self._user_id) if self._user_id else None,
                    "tenant_id": str(self._tenant_id) if self._tenant_id else None,
                }
                _append_entry(entry, self._tenant_id)
                return f"✅ Stored observation (no existing entity '{entity_name}' found — stored standalone): {content}"

        return "Error: Invalid type. Use 'entity', 'relation', or 'observation'."


class MemoryRecall(Tool):
    """Recall entities by name from persistent memory."""

    name: str = "mcp_memory_recall"
    description: str = (
        "Recall stored entities, their observations, and relations by name. "
        "Use this when you need to remember information about a person, project, or concept "
        "that was stored earlier."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "Name of the entity to recall.",
            },
        },
        "required": ["name"],
    }

    def __init__(self, **kwargs):
        self._tenant_id = kwargs.get("tenant_id")
        self._user_id = kwargs.get("user_id")

    async def execute(self, **kwargs: Any) -> str:
        name = kwargs.get("name", "").strip()
        if not name:
            return "Error: 'name' is required."

        entries = _read_entries(self._tenant_id)

        # Find matching entities (case-insensitive)
        entities = [e for e in entries if e.get("type") == "entity" and name.lower() in e.get("name", "").lower()]
        relations = [e for e in entries if e.get("type") == "relation" and (name.lower() in e.get("from", "").lower() or name.lower() in e.get("to", "").lower())]
        obs = [e for e in entries if e.get("type") == "observation" and name.lower() in e.get("entity_name", "").lower()]

        if not entities and not relations and not obs:
            return f"No memory found for '{name}'."

        result = []
        for entity in entities:
            result.append(f"**Entity:** {entity['name']} ({entity.get('entityType', 'general')})")
            obs_list = entity.get("observations", [])
            if obs_list:
                result.append("Observations:")
                for o in obs_list:
                    result.append(f"  • {o}")
            result.append("")

        if relations:
            result.append(f"**Relationships involving '{name}':**")
            for r in relations[:20]:
                result.append(f"  • {r['from']} → [{r['relationType']}] → {r['to']}")
            result.append("")

        if obs:
            result.append("**Additional observations:**")
            for o in obs[:10]:
                result.append(f"  • [{o.get('entity_name', '?')}] {o['content']}")

        return "\n".join(result)


class MemorySearch(Tool):
    """Search memory by keyword across all stored entities and observations."""

    name: str = "mcp_memory_search"
    description: str = (
        "Search all stored memory entries by keyword. "
        "Searches across entity names, observations, and relation types. "
        "Use this when you're not sure of the exact entity name but want to find relevant information."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search keyword or phrase.",
            },
        },
        "required": ["query"],
    }

    def __init__(self, **kwargs):
        self._tenant_id = kwargs.get("tenant_id")
        self._user_id = kwargs.get("user_id")

    async def execute(self, **kwargs: Any) -> str:
        query = kwargs.get("query", "").strip().lower()
        if not query:
            return "Error: 'query' is required."

        entries = _read_entries(self._tenant_id)
        if not entries:
            return "No memory stored yet."

        results = []
        for e in entries:
            match = False
            # Check entity name
            if query in e.get("name", "").lower():
                match = True
            # Check observations
            for obs in e.get("observations", []):
                if query in obs.lower():
                    match = True
            # Check content
            if query in e.get("content", "").lower():
                match = True
            # Check relations
            if query in e.get("relationType", "").lower():
                match = True
            if query in e.get("from", "").lower() or query in e.get("to", "").lower():
                match = True

            if match:
                results.append(e)

        if not results:
            return f"No memory found matching '{query}'."

        result = [f"Found {len(results)} memory entries matching '{query}':\n"]
        for e in results[:20]:
            if e.get("type") == "entity":
                result.append(f"  • **Entity:** {e['name']} ({e.get('entityType', 'general')})")
            elif e.get("type") == "relation":
                result.append(f"  • **Relation:** {e['from']} → [{e['relationType']}] → {e['to']}")
            elif e.get("type") == "observation":
                result.append(f"  • **Observation** [{e.get('entity_name', '?')}]: {e['content'][:100]}")

        if len(results) > 20:
            result.append(f"\n... and {len(results) - 20} more")

        return "\n".join(result)


class MemoryList(Tool):
    """List all stored entities in memory."""

    name: str = "mcp_memory_list"
    description: str = (
        "List all entities stored in persistent memory. "
        "Returns entity names, types, and observation counts. "
        "Use this for an overview of what's been remembered."
    )
    parameters: dict = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    def __init__(self, **kwargs):
        self._tenant_id = kwargs.get("tenant_id")
        self._user_id = kwargs.get("user_id")

    async def execute(self, **kwargs: Any) -> str:
        entries = _read_entries(self._tenant_id)
        entities = [e for e in entries if e.get("type") == "entity"]
        relations = [e for e in entries if e.get("type") == "relation"]

        if not entities and not relations:
            return "Memory is empty."

        result = []
        if entities:
            result.append(f"**Entities ({len(entities)}):**\n")
            for e in sorted(entities, key=lambda x: x.get("name", "")):
                obs_count = len(e.get("observations", []))
                result.append(f"  • {e['name']} ({e.get('entityType', 'general')}) — {obs_count} observation(s)")
            result.append("")

        if relations:
            result.append(f"**Relationships ({len(relations)}):**")
            for r in relations[:20]:
                result.append(f"  • {r['from']} → [{r['relationType']}] → {r['to']}")
            if len(relations) > 20:
                result.append(f"  ... and {len(relations) - 20} more")

        return "\n".join(result)
