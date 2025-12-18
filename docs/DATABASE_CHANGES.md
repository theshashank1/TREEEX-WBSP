# Database Schema Changes Documentation

This document outlines any database schema changes made as part of the media endpoints integration.

## Version: v1.6 (Current)

### Schema Status: **NO CHANGES**

This implementation uses the existing database schema v1.6 without any modifications. All tables and relationships remain as defined in the original schema.

### Tables Used

The following existing tables are utilized by the new API endpoints:

#### Contacts API (`/api/contacts`)
- Uses: `contacts` table (existing)
- Operations: CRUD operations, import from CSV/Excel
- No schema changes required

#### Media API (`/api/media`)
- Uses: `media_files` table (existing)
- Operations: Upload, download, SAS URL generation
- No schema changes required

#### Messages API (`/api/messages`)
- Uses: `messages` table (existing)
- Uses: `media_files` table for media attachments
- Uses: `phone_numbers` table for sender information
- No schema changes required

#### Campaigns API (`/api/campaigns`)
- Uses: `campaigns` table (existing)
- Uses: `campaign_messages` table (existing)
- Supports broadcast/bulk messaging functionality
- No schema changes required

### Notes

1. **Broadcast Functionality**: The existing `campaigns` table already provides all the functionality needed for broadcast messaging (scheduled sends, audience tracking, delivery stats).

2. **Media Storage**: The `media_files` table stores metadata; actual files are stored in Azure Blob Storage with workspace-scoped paths (`{workspace_id}/{uuid}_{filename}`).

3. **Contact Import**: CSV and Excel imports are supported. Required column: `phone` (E.164 format). Optional columns: `name`, `labels/tags`.

### Future Considerations

If additional features are needed that require schema changes, they should be:
1. Documented here first
2. Added to the dbdiagram.io schema
3. Reviewed before implementation
