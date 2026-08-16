"""phase7_documents

Revision ID: 3635da773fa4
Revises: c2fa8c618622
Create Date: 2026-08-16 05:29:20.121527

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '3635da773fa4'
down_revision: Union[str, Sequence[str], None] = 'c2fa8c618622'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # 1. document_uploads
    op.create_table('document_uploads',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('file_hash', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=1024), nullable=False),
        sa.Column('format', sa.String(length=50), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_uploads_file_hash'), 'document_uploads', ['file_hash'], unique=False)
    op.create_index(op.f('ix_document_uploads_tenant_id'), 'document_uploads', ['tenant_id'], unique=False)

    # 2. document_extractions
    op.create_table('document_extractions',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('document_upload_id', sa.UUID(), nullable=False),
        sa.Column('supplier_cnpj_candidate', sa.String(length=50), nullable=True),
        sa.Column('supplier_name_candidate', sa.String(length=255), nullable=True),
        sa.Column('invoice_number_candidate', sa.String(length=100), nullable=True),
        sa.Column('total_amount_candidate', sa.Numeric(precision=24, scale=12), nullable=True),
        sa.Column('issue_date_candidate', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_upload_id'], ['document_uploads.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_upload_id')
    )
    op.create_index(op.f('ix_document_extractions_tenant_id'), 'document_extractions', ['tenant_id'], unique=False)

    # 3. document_extraction_lines
    op.create_table('document_extraction_lines',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('tenant_id', sa.UUID(), nullable=False),
        sa.Column('document_extraction_id', sa.UUID(), nullable=False),
        sa.Column('raw_description', sa.String(length=255), nullable=True),
        sa.Column('raw_code', sa.String(length=100), nullable=True),
        sa.Column('raw_quantity', sa.Numeric(precision=24, scale=12), nullable=True),
        sa.Column('raw_uom', sa.String(length=50), nullable=True),
        sa.Column('raw_unit_price', sa.Numeric(precision=24, scale=12), nullable=True),
        sa.Column('normalized_sku_id', sa.UUID(), nullable=True),
        sa.Column('confidence_score', sa.Numeric(precision=5, scale=4), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['tenant_id'], ['tenants.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_extraction_id'], ['document_extractions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['normalized_sku_id'], ['skus.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_document_extraction_lines_tenant_id'), 'document_extraction_lines', ['tenant_id'], unique=False)
    op.create_index(op.f('ix_document_extraction_lines_document_extraction_id'), 'document_extraction_lines', ['document_extraction_id'], unique=False)

    # RLS Policies
    op.execute("ALTER TABLE document_uploads ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE document_uploads FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY tenant_isolation_policy ON document_uploads USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid) WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)")

    op.execute("ALTER TABLE document_extractions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE document_extractions FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY tenant_isolation_policy ON document_extractions USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid) WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)")

    op.execute("ALTER TABLE document_extraction_lines ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE document_extraction_lines FORCE ROW LEVEL SECURITY")
    op.execute("CREATE POLICY tenant_isolation_policy ON document_extraction_lines USING (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid) WITH CHECK (tenant_id = NULLIF(current_setting('app.current_tenant_id', true), '')::uuid)")

    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON document_uploads, document_extractions, document_extraction_lines TO ksfoodops_app")


def downgrade() -> None:
    """Downgrade schema."""
    op.execute("REVOKE SELECT, INSERT, UPDATE, DELETE ON document_uploads, document_extractions, document_extraction_lines FROM ksfoodops_app")
    op.drop_table('document_extraction_lines')
    op.drop_table('document_extractions')
    op.drop_table('document_uploads')
