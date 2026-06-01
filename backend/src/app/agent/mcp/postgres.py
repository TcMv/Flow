"""Postgres MCP tools — query and inspect databases via SQLAlchemy."""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.agent.tools import Tool


_MAX_ROWS = 100
_MAX_CELL_LENGTH = 200


class PostgresQuery(Tool):
    """Execute a SQL query against a connected database."""

    name: str = "mcp_postgres_query"
    description: str = (
        "Execute a SQL SELECT query against the connected database. "
        "Returns results as a formatted table. "
        "READ-ONLY: only SELECT queries are allowed — INSERT/UPDATE/DELETE are blocked. "
        "Use this when the user wants to query data, run reports, or explore the database. "
        "Limit: max 100 rows returned."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The SQL SELECT query to execute. Must be a SELECT statement.",
            },
        },
        "required": ["query"],
    }

    def __init__(self, db: AsyncSession | None = None, **kwargs):
        self._db = db
        self._user_id = kwargs.get("user_id")
        self._tenant_id = kwargs.get("tenant_id")

    async def execute(self, **kwargs: Any) -> str:
        query_str = kwargs.get("query", "").strip()
        if not query_str:
            return "Error: 'query' is required."

        if not self._db:
            return "Error: Database connection not available in this context."

        # Safety: only allow SELECT
        stripped = query_str.strip().upper()
        if not stripped.startswith("SELECT"):
            return "Error: Only SELECT queries are allowed for safety."

        try:
            result = await self._db.execute(text(query_str))
            rows = result.all()

            if not rows:
                return "Query returned 0 rows."

            # Get column names from result keys
            col_names = list(result.keys())

            # Build formatted output
            total = len(rows)
            display = rows[:_MAX_ROWS]

            # Format as simple text table
            col_widths = {}
            for col in col_names:
                col_widths[col] = len(col)
            for row in display:
                for i, col in enumerate(col_names):
                    val = str(row[i]) if row[i] is not None else "NULL"
                    if len(val) > _MAX_CELL_LENGTH:
                        val = val[:_MAX_CELL_LENGTH] + "..."
                    col_widths[col] = max(col_widths[col], len(val))

            lines = []
            # Header
            header = " | ".join(col.ljust(col_widths[col]) for col in col_names)
            lines.append(header)
            lines.append("-+-".join("-" * col_widths[col] for col in col_names))

            # Rows
            for row in display:
                cells = []
                for i, col in enumerate(col_names):
                    val = str(row[i]) if row[i] is not None else "NULL"
                    if len(val) > _MAX_CELL_LENGTH:
                        val = val[:_MAX_CELL_LENGTH] + "..."
                    cells.append(val.ljust(col_widths[col]))
                lines.append(" | ".join(cells))

            summary = f"\n{len(display)} row(s) shown"
            if total > _MAX_ROWS:
                summary += f" (of {total} total)"
            lines.append(summary)

            return "\n".join(lines)

        except Exception as e:
            return f"Query error: {e}"


class PostgresListTables(Tool):
    """List all tables in the database with row counts."""

    name: str = "mcp_postgres_list_tables"
    description: str = (
        "List all tables in the connected database with their schema names and estimated row counts. "
        "Use this to discover what data is available for querying."
    )
    parameters: dict = {
        "type": "object",
        "properties": {},
        "required": [],
    }

    def __init__(self, db: AsyncSession | None = None, **kwargs):
        self._db = db
        self._user_id = kwargs.get("user_id")
        self._tenant_id = kwargs.get("tenant_id")

    async def execute(self, **kwargs: Any) -> str:
        if not self._db:
            return "Error: Database connection not available."

        try:
            result = await self._db.execute(
                text("""
                    SELECT
                        table_schema,
                        table_name,
                        (SELECT reltuples::BIGINT FROM pg_class WHERE oid = (quote_ident(table_schema) || '.' || quote_ident(table_name))::regclass) AS row_count
                    FROM information_schema.tables
                    WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                    ORDER BY table_schema, table_name
                """)
            )
            rows = result.all()

            if not rows:
                return "No tables found in database."

            lines = [f"Tables ({len(rows)}):\n"]
            for row in rows:
                schema, table, count = row
                count_str = f" (~{count:,} rows)" if count else ""
                lines.append(f"  • {schema}.{table}{count_str}")

            return "\n".join(lines)

        except Exception as e:
            return f"Error listing tables: {e}"


class PostgresDescribeTable(Tool):
    """Describe a table's columns, types, and constraints."""

    name: str = "mcp_postgres_describe_table"
    description: str = (
        "Describe a table's schema — column names, data types, nullable, defaults, and constraints. "
        "Use this to understand the structure of a table before querying it."
    )
    parameters: dict = {
        "type": "object",
        "properties": {
            "table_name": {
                "type": "string",
                "description": "The name of the table to describe. Can include schema prefix, e.g. 'public.users'.",
            },
        },
        "required": ["table_name"],
    }

    def __init__(self, db: AsyncSession | None = None, **kwargs):
        self._db = db
        self._user_id = kwargs.get("user_id")
        self._tenant_id = kwargs.get("tenant_id")

    async def execute(self, **kwargs: Any) -> str:
        table = kwargs.get("table_name", "").strip()
        if not table:
            return "Error: 'table_name' is required."

        if not self._db:
            return "Error: Database connection not available."

        # Split schema.table
        parts = table.split(".")
        if len(parts) == 2:
            schema, tbl = parts
        else:
            schema, tbl = "public", parts[0]

        try:
            result = await self._db.execute(
                text("""
                    SELECT
                        column_name,
                        data_type,
                        is_nullable,
                        column_default,
                        character_maximum_length
                    FROM information_schema.columns
                    WHERE table_schema = :schema AND table_name = :table
                    ORDER BY ordinal_position
                """),
                {"schema": schema, "table": tbl},
            )
            columns = result.all()

            if not columns:
                return f"Table '{schema}.{tbl}' not found."

            # Get primary key info
            pk_result = await self._db.execute(
                text("""
                    SELECT kcu.column_name
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                        ON tc.constraint_name = kcu.constraint_name
                        AND tc.table_schema = kcu.table_schema
                    WHERE tc.table_schema = :schema
                        AND tc.table_name = :table
                        AND tc.constraint_type = 'PRIMARY KEY'
                """),
                {"schema": schema, "table": tbl},
            )
            pk_cols = {r[0] for r in pk_result.all()}

            lines = [f"Table: {schema}.{tbl}\n"]
            lines.append(f"{'Column':<30} {'Type':<20} {'Null':<6} {'Default':<20} {'PK'}")
            lines.append("-" * 80)

            for col in columns:
                name = col[0]
                dtype = col[1] or ""
                nullable = "YES" if col[2] == "YES" else "NO"
                default = str(col[3] or "")[:20]
                pk = "✓" if name in pk_cols else ""
                lines.append(
                    f"{name:<30} {dtype:<20} {nullable:<6} {default:<20} {pk}"
                )

            return "\n".join(lines)

        except Exception as e:
            return f"Error describing table: {e}"
