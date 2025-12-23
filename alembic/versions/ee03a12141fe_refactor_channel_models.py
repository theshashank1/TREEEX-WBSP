"""refactor_channel_models

Revision ID: ee03a12141fe
Revises: 
Create Date: 2025-12-24 01:42:51.636825

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'ee03a12141fe'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Rename phone_numbers table to channels
    op.rename_table('phone_numbers', 'channels')
    
    # 2. Update columns in channels
    op.alter_column('channels', 'phone_number_id', new_column_name='meta_phone_number_id')
    op.alter_column('channels', 'business_id', new_column_name='meta_business_id')
    op.add_column('channels', sa.Column('meta_waba_id', sa.String(length=255), nullable=True))
    op.add_column('channels', sa.Column('name', sa.String(length=255), nullable=False, server_default='WhatsApp Channel'))
    
    # Indexes handling for channels (use IF EXISTS for safety)
    op.execute('DROP INDEX IF EXISTS idx_phone_number_id')
    op.execute('DROP INDEX IF EXISTS idx_phone_status')
    op.execute('DROP INDEX IF EXISTS idx_phone_workspace')
    op.execute('DROP INDEX IF EXISTS idx_phone_workspace_number')
    
    op.create_index('idx_channel_meta_id', 'channels', ['meta_phone_number_id'], unique=True)
    op.create_index('idx_channel_status', 'channels', ['status'], unique=False)
    op.create_index('idx_channel_workspace', 'channels', ['workspace_id'], unique=False)
    op.create_index('idx_channel_workspace_number', 'channels', ['workspace_id', 'phone_number'], unique=True)

    # 3. Create contact_channel_states
    op.create_table('contact_channel_states',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('workspace_id', sa.Uuid(), nullable=False),
    sa.Column('contact_id', sa.Uuid(), nullable=False),
    sa.Column('channel_id', sa.Uuid(), nullable=False),
    sa.Column('opt_in_status', sa.Boolean(), nullable=False, server_default='false'),
    sa.Column('opt_in_type', sa.String(length=20), nullable=True),
    sa.Column('opt_in_date', sa.DateTime(), nullable=True),
    sa.Column('blocked', sa.Boolean(), nullable=False, server_default='false'),
    sa.Column('last_message_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['channel_id'], ['channels.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['contact_id'], ['contacts.id'], ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['workspace_id'], ['workspaces.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_ccs_channel_optin', 'contact_channel_states', ['channel_id', 'opt_in_status'], unique=False)
    op.create_index('idx_ccs_contact_channel', 'contact_channel_states', ['contact_id', 'channel_id'], unique=True)
    op.create_index('idx_ccs_workspace', 'contact_channel_states', ['workspace_id'], unique=False)
    op.create_index('idx_ccs_workspace_contact', 'contact_channel_states', ['workspace_id', 'contact_id'], unique=False)

    # 4. Rename FK columns in other tables
    
    # Campaigns
    op.alter_column('campaigns', 'phone_number_id', new_column_name='channel_id')
    op.execute('ALTER TABLE campaigns DROP CONSTRAINT IF EXISTS campaigns_phone_number_id_fkey')
    op.create_foreign_key(None, 'campaigns', 'channels', ['channel_id'], ['id'], ondelete='CASCADE')
    op.execute('DROP INDEX IF EXISTS idx_campaign_phone')
    op.execute('DROP INDEX IF EXISTS idx_campaign_phone_status')
    op.create_index('idx_campaign_channel', 'campaigns', ['channel_id'], unique=False)
    op.create_index('idx_campaign_channel_status', 'campaigns', ['channel_id', 'status'], unique=False)

    # Campaign Messages
    op.alter_column('campaign_messages', 'phone_number_id', new_column_name='channel_id')
    op.execute('ALTER TABLE campaign_messages DROP CONSTRAINT IF EXISTS campaign_messages_phone_number_id_fkey')
    op.create_foreign_key(None, 'campaign_messages', 'channels', ['channel_id'], ['id'], ondelete='SET NULL')

    # Conversations
    op.alter_column('conversations', 'phone_number_id', new_column_name='channel_id')
    op.execute('ALTER TABLE conversations DROP CONSTRAINT IF EXISTS conversations_phone_number_id_fkey')
    op.create_foreign_key(None, 'conversations', 'channels', ['channel_id'], ['id'], ondelete='CASCADE')
    op.execute('DROP INDEX IF EXISTS idx_conv_workspace_contact_phone')
    op.create_index('idx_conv_workspace_contact_phone', 'conversations', ['workspace_id', 'contact_id', 'channel_id'], unique=True)

    # Messages
    op.alter_column('messages', 'phone_number_id', new_column_name='channel_id')
    op.execute('ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_phone_number_id_fkey')
    op.create_foreign_key(None, 'messages', 'channels', ['channel_id'], ['id'], ondelete='CASCADE')
    op.execute('DROP INDEX IF EXISTS idx_msg_phone_time')
    op.create_index('idx_msg_channel_time', 'messages', ['channel_id', 'created_at'], unique=False)

    # Templates
    op.alter_column('templates', 'phone_number_id', new_column_name='channel_id')
    op.execute('ALTER TABLE templates DROP CONSTRAINT IF EXISTS templates_phone_number_id_fkey')
    op.create_foreign_key(None, 'templates', 'channels', ['channel_id'], ['id'], ondelete='CASCADE')
    op.execute('DROP INDEX IF EXISTS idx_template_phone')
    op.execute('DROP INDEX IF EXISTS idx_template_phone_status')
    op.execute('DROP INDEX IF EXISTS idx_template_workspace_phone_name')
    op.create_index('idx_template_workspace_phone_name', 'templates', ['workspace_id', 'channel_id', 'name'], unique=True)
    op.create_index('idx_template_channel', 'templates', ['channel_id'], unique=False)
    op.create_index('idx_template_channel_status', 'templates', ['channel_id', 'status'], unique=False)

    # Webhook Logs
    op.alter_column('webhook_logs', 'phone_number_id', new_column_name='channel_id')
    op.execute('ALTER TABLE webhook_logs DROP CONSTRAINT IF EXISTS webhook_logs_phone_number_id_fkey')
    op.create_foreign_key(None, 'webhook_logs', 'channels', ['channel_id'], ['id'], ondelete='SET NULL')
    op.execute('DROP INDEX IF EXISTS idx_webhook_phone_time')
    op.create_index('idx_webhook_channel_time', 'webhook_logs', ['channel_id', 'received_at'], unique=False)

    # Contacts updates - use IF EXISTS for columns that might not exist
    op.execute('DROP INDEX IF EXISTS idx_contact_opted_in')
    op.execute('ALTER TABLE contacts DROP COLUMN IF EXISTS opted_in')
    op.execute('ALTER TABLE contacts DROP COLUMN IF EXISTS opt_in_source')
    op.execute('ALTER TABLE contacts DROP COLUMN IF EXISTS opt_in_date')
    
    # Source channel id
    op.add_column('contacts', sa.Column('source_channel_id', sa.Uuid(), nullable=True))
    op.create_index('idx_contact_source_channel', 'contacts', ['source_channel_id'], unique=False)
    op.create_foreign_key(None, 'contacts', 'channels', ['source_channel_id'], ['id'], ondelete='SET NULL')


def downgrade() -> None:
    # Reverse (partial implementation)
    op.execute('ALTER TABLE contacts DROP COLUMN IF EXISTS source_channel_id')
    op.drop_column('channels', 'name')
    op.drop_column('channels', 'meta_waba_id')
    op.rename_table('channels', 'phone_numbers')
    op.alter_column('phone_numbers', 'meta_phone_number_id', new_column_name='phone_number_id')
    op.alter_column('phone_numbers', 'meta_business_id', new_column_name='business_id')
    op.drop_table('contact_channel_states')
