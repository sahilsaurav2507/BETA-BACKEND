"""Add email and name fields to feedback table and make some fields optional

Revision ID: add_feedback_contact_fields
Revises: [previous_revision_id]
Create Date: 2025-07-22 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_feedback_contact_fields'
down_revision = None  # Replace with actual previous revision ID
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new email and name columns with default values for existing records
    op.add_column('feedback', sa.Column('email', sa.String(length=255), nullable=False, server_default='unknown@example.com'))
    op.add_column('feedback', sa.Column('name', sa.String(length=255), nullable=False, server_default='Unknown User'))

    # Create indexes for the new columns
    op.create_index(op.f('ix_feedback_email'), 'feedback', ['email'], unique=False)

    # Make some existing columns nullable (optional fields) - using MySQL syntax
    op.alter_column('feedback', 'primary_motivation',
                    existing_type=mysql.ENUM('A', 'B', 'C', 'D'),
                    nullable=True)
    op.alter_column('feedback', 'time_consuming_part',
                    existing_type=mysql.ENUM('A', 'B', 'C', 'D'),
                    nullable=True)
    op.alter_column('feedback', 'monetization_considerations',
                    existing_type=sa.TEXT(),
                    nullable=True)
    op.alter_column('feedback', 'professional_legacy',
                    existing_type=sa.TEXT(),
                    nullable=True)

    # Remove default values after adding columns
    op.alter_column('feedback', 'email', server_default=None)
    op.alter_column('feedback', 'name', server_default=None)


def downgrade() -> None:
    # Make columns non-nullable again
    op.alter_column('feedback', 'professional_legacy',
                    existing_type=sa.TEXT(),
                    nullable=False)
    op.alter_column('feedback', 'monetization_considerations',
                    existing_type=sa.TEXT(),
                    nullable=False)
    op.alter_column('feedback', 'time_consuming_part',
                    existing_type=mysql.ENUM('A', 'B', 'C', 'D'),
                    nullable=False)
    op.alter_column('feedback', 'primary_motivation',
                    existing_type=mysql.ENUM('A', 'B', 'C', 'D'),
                    nullable=False)

    # Drop indexes and columns
    op.drop_index(op.f('ix_feedback_email'), table_name='feedback')
    op.drop_column('feedback', 'name')
    op.drop_column('feedback', 'email')
