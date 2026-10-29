"""Foundation tables and the authorized manual source."""

import sqlalchemy as sa

from alembic import op

revision = "0001_foundation"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "candidate_profiles",
        sa.Column("id", sa.Integer(), autoincrement=False, primary_key=True),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("experience_years", sa.Integer(), nullable=False),
        sa.Column("preferred_location", sa.String(200), nullable=False),
        sa.Column("prefer_remote", sa.Boolean(), nullable=False),
        sa.CheckConstraint("id = 1", name="ck_candidate_single_user"),
        sa.CheckConstraint("experience_years >= 0", name="ck_candidate_experience"),
    )
    sources = op.create_table(
        "job_sources",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(100), nullable=False, unique=True),
        sa.Column("kind", sa.String(50), nullable=False),
    )
    op.bulk_insert(sources, [{"id": 1, "name": "Manual", "kind": "manual"}])
    # Explicit seed IDs must not leave the PostgreSQL sequence behind.
    op.execute("SELECT setval(pg_get_serial_sequence('job_sources', 'id'), 1)")
    op.create_table(
        "job_postings",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("company", sa.String(200), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("location", sa.String(200), nullable=False),
        sa.Column("remote", sa.Boolean(), nullable=False),
        sa.Column("required_skills", sa.JSON(), nullable=False),
        sa.Column("experience_years", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(2048), nullable=True),
        sa.Column("source_id", sa.Integer(), sa.ForeignKey("job_sources.id"), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("experience_years >= 0", name="ck_job_experience"),
    )
    op.create_index("ix_job_postings_source_id", "job_postings", ["source_id"])
    op.create_table(
        "match_scores",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "job_id",
            sa.Integer(),
            sa.ForeignKey("job_postings.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "candidate_id", sa.Integer(), sa.ForeignKey("candidate_profiles.id"), nullable=False
        ),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("skill_score", sa.Float(), nullable=False),
        sa.Column("experience_score", sa.Float(), nullable=False),
        sa.Column("location_score", sa.Float(), nullable=False),
        sa.Column("matched_skills", sa.JSON(), nullable=False),
        sa.Column("missing_skills", sa.JSON(), nullable=False),
        sa.Column("algorithm_version", sa.String(30), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.UniqueConstraint("job_id", name="uq_match_job"),
        sa.CheckConstraint("score >= 0 AND score <= 100", name="ck_match_score_range"),
    )


def downgrade() -> None:
    op.drop_table("match_scores")
    op.drop_index("ix_job_postings_source_id", table_name="job_postings")
    op.drop_table("job_postings")
    op.drop_table("job_sources")
    op.drop_table("candidate_profiles")
