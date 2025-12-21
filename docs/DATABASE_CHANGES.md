# 🗄️ Database Changelog

Chronological log of database schema changes.

## 🏷️ Version History

### [1.6.0] - 2024-12-21 (Current)
**Status**: Stable

#### Changes
- **No Schema Changes**. This release focuses on Documentation standardization.
- Full schema defined in [DATABASE_SCHEMA.md](DATABASE_SCHEMA.md).

---

### [1.5.0] - 2024-11-15
#### Added
- `campaigns` table foundation.
- `campaign_messages` table for tracking individual statuses.
- `templates` table updated with `category` constraints.

---

### [1.0.0] - 2024-01-01
#### Initial Release
- Core tables: `users`, `workspaces`, `phone_numbers`.
- Messaging tables: `conversations`, `messages`.
- Basic RBAC structure.
