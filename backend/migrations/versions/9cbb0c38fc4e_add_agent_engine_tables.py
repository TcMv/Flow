"""Add agent engine tables: llm_keys, agent_sessions, agent_messages."""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "9cbb0c38fc4e"
down_revision: Union[str, None] = "36882084eaf8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Apply migration."""
    # llm_keys — encrypted LLM provider credentials per tenant
    op.create_table('llm_keys',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('provider', sa.String(length=32), nullable=False,
                  comment='openai / anthropic / azure / custom'),
        sa.Column('api_key_encrypted', sa.Text(), nullable=False,
                  comment='Fernet-encrypted API key'),
        sa.Column('base_url', sa.String(length=512), nullable=True,
                  comment='Base URL for custom/self-hosted providers'),
        sa.Column('model_name', sa.String(length=128), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # agent_sessions — persisted conversation sessions
    op.create_table('agent_sessions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=True,
                  comment='Auto-generated title from first user message'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # agent_messages — individual messages within a session
    op.create_table('agent_messages',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('session_id', sa.UUID(), nullable=False),
        sa.Column('role', sa.String(length=16), nullable=False,
                  comment='user / assistant / tool'),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('tool_calls', sa.Text(), nullable=True,
                  comment='JSON-encoded tool call metadata (if any)'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['session_id'], ['agent_sessions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Revert migration."""
    op.drop_table('agent_messages')
    op.drop_table('agent_sessions')
    op.drop_table('llm_keys')
