"""Initial schema – all tables for Call Intelligence Platform.

Revision ID: 001
Revises: None
Create Date: 2026-03-02

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import JSONB

# revision identifiers, used by Alembic.
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── shops ────────────────────────────────────────────────────────────
    op.create_table(
        "shops",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("shop_code", sa.String(50), unique=True, nullable=False, index=True),
        sa.Column("phone_number", sa.String(20)),
        sa.Column("timezone", sa.String(50), server_default="America/New_York"),
        sa.Column("business_hours", JSONB, server_default="{}"),
        sa.Column("address", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # ── users ────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("shop_id", sa.Integer(), sa.ForeignKey("shops.id"), nullable=False),
        sa.Column("email", sa.String(255), unique=True, nullable=False, index=True),
        sa.Column("api_key", sa.String(255), nullable=False, index=True),
        sa.Column("role", sa.String(20), server_default="viewer"),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # ── calls ────────────────────────────────────────────────────────────
    op.create_table(
        "calls",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("shop_id", sa.Integer(), sa.ForeignKey("shops.id"), nullable=False),
        sa.Column("twilio_call_sid", sa.String(64), unique=True, index=True),
        sa.Column("direction", sa.String(10), nullable=False),
        sa.Column("status", sa.String(20), server_default="initiated"),
        sa.Column("from_number", sa.String(20)),
        sa.Column("to_number", sa.String(20)),
        sa.Column("caller_name", sa.String(255)),
        sa.Column("start_time", sa.DateTime()),
        sa.Column("end_time", sa.DateTime()),
        sa.Column("duration_seconds", sa.Integer()),
        sa.Column("recording_url", sa.Text()),
        sa.Column("transcript", sa.Text()),
        sa.Column("transcript_status", sa.String(20), server_default="pending"),
        sa.Column("ai_score", sa.Float()),
        sa.Column("sentiment", sa.String(20)),
        sa.Column("caller_intent", sa.String(100)),
        sa.Column("key_points", JSONB, server_default="[]"),
        sa.Column("coaching_notes", sa.Text()),
        sa.Column("analysis_status", sa.String(20), server_default="pending"),
        sa.Column("is_new_customer", sa.String(10)),
        sa.Column("handled_by", sa.String(20)),
        sa.Column("ai_agent_language", sa.String(10)),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column(
            "updated_at",
            sa.DateTime(),
            server_default=sa.func.now(),
            onupdate=sa.func.now(),
        ),
    )

    # Composite and single-column indexes for the calls table
    op.create_index("ix_calls_shop_id_start_time", "calls", ["shop_id", "start_time"])
    op.create_index("ix_calls_status", "calls", ["status"])
    op.create_index("ix_calls_direction", "calls", ["direction"])

    # ── call_participants ────────────────────────────────────────────────
    op.create_table(
        "call_participants",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("call_id", sa.Integer(), sa.ForeignKey("calls.id"), nullable=False),
        sa.Column("speaker_label", sa.String(50)),
        sa.Column("role", sa.String(20)),
        sa.Column("utterances", JSONB, server_default="[]"),
        sa.Column("total_talk_time_seconds", sa.Float(), server_default="0.0"),
    )

    # ── phone_numbers ────────────────────────────────────────────────────
    op.create_table(
        "phone_numbers",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("shop_id", sa.Integer(), sa.ForeignKey("shops.id"), nullable=False),
        sa.Column("phone_number", sa.String(20), unique=True, nullable=False),
        sa.Column("number_type", sa.String(20), server_default="main"),
        sa.Column("lead_source", sa.String(100)),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
    )

    # ── call_metrics ─────────────────────────────────────────────────────
    op.create_table(
        "call_metrics",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("shop_id", sa.Integer(), sa.ForeignKey("shops.id"), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("total_calls", sa.Integer(), server_default="0"),
        sa.Column("inbound_calls", sa.Integer(), server_default="0"),
        sa.Column("outbound_calls", sa.Integer(), server_default="0"),
        sa.Column("missed_calls", sa.Integer(), server_default="0"),
        sa.Column("ai_handled_calls", sa.Integer(), server_default="0"),
        sa.Column("avg_duration", sa.Float(), server_default="0.0"),
        sa.Column("avg_score", sa.Float()),
        sa.Column("sentiment_distribution", JSONB, server_default="{}"),
        sa.Column("lead_source_breakdown", JSONB, server_default="{}"),
    )

    # ── playbooks ────────────────────────────────────────────────────────
    op.create_table(
        "playbooks",
        sa.Column("id", sa.Integer(), primary_key=True, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("version", sa.Integer(), server_default="1"),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("criteria", JSONB, server_default="[]"),
        sa.Column("script_template", sa.Text()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
    )

    # ── seed default playbook ────────────────────────────────────────────
    op.execute(
        """
        INSERT INTO playbooks (name, version, is_active, criteria, script_template)
        VALUES (
            'Auto Repair Scoring Rubric',
            1,
            true,
            '[
                {
                    "category": "Greeting & Professionalism",
                    "weight": 0.15,
                    "description": "Evaluate the greeting, tone, and overall professionalism throughout the call."
                },
                {
                    "category": "Needs Assessment",
                    "weight": 0.20,
                    "description": "Evaluate how well the advisor identified the customer''s vehicle issues and service needs."
                },
                {
                    "category": "Service Knowledge",
                    "weight": 0.20,
                    "description": "Evaluate the advisor''s ability to explain services, parts, and repair processes clearly."
                },
                {
                    "category": "Appointment Setting",
                    "weight": 0.20,
                    "description": "Evaluate how effectively the advisor moved toward booking an appointment."
                },
                {
                    "category": "Objection Handling",
                    "weight": 0.15,
                    "description": "Evaluate how the advisor addressed concerns about price, timing, or necessity of service."
                },
                {
                    "category": "Closing & Follow-up",
                    "weight": 0.10,
                    "description": "Evaluate how the call was wrapped up, including next steps and follow-up commitments."
                }
            ]'::jsonb,
            NULL
        );
        """
    )


def downgrade() -> None:
    op.drop_table("playbooks")
    op.drop_table("call_metrics")
    op.drop_table("phone_numbers")
    op.drop_table("call_participants")
    op.drop_index("ix_calls_direction", table_name="calls")
    op.drop_index("ix_calls_status", table_name="calls")
    op.drop_index("ix_calls_shop_id_start_time", table_name="calls")
    op.drop_table("calls")
    op.drop_table("users")
    op.drop_table("shops")
