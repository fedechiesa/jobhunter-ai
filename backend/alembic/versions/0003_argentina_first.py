"""Argentina evidence and optional structured profile; preserve all historical rows."""

import sqlalchemy as sa

from alembic import op

revision = "0003_argentina_first"
down_revision = "2e57c63bd9b7"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("job_postings", sa.Column("location_details", sa.Text(), nullable=True))
    op.add_column(
        "job_sources", sa.Column("next_allowed_at", sa.DateTime(timezone=True), nullable=True)
    )
    op.add_column(
        "job_sources",
        sa.Column("consecutive_failures", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column("candidate_profiles", sa.Column("professional", sa.JSON(), nullable=True))
    op.add_column(
        "job_postings",
        sa.Column("country", sa.String(20), nullable=False, server_default="unknown"),
    )
    op.add_column(
        "job_postings",
        sa.Column("compatibility", sa.String(30), nullable=False, server_default="review_needed"),
    )
    op.add_column(
        "job_postings", sa.Column("assessment", sa.JSON(), nullable=False, server_default="{}")
    )
    op.create_index("ix_job_postings_compatibility", "job_postings", ["compatibility"])


def downgrade():
    op.drop_column("job_postings", "location_details")
    op.drop_column("job_sources", "consecutive_failures")
    op.drop_column("job_sources", "next_allowed_at")
    op.drop_index("ix_job_postings_compatibility", table_name="job_postings")
    for column in ("assessment", "compatibility", "country"):
        op.drop_column("job_postings", column)
    op.drop_column("candidate_profiles", "professional")
