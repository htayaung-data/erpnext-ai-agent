# Roles & Permissions (Safety-First)

## Roles
### Director (Human)
- Approves policies, mappings, and submissions
- Final sign-off for UAT and go-live

### ai.operator (AI Operator)
Allowed:
- Create/update masters and settings
- Create drafts (docstatus=0) for transactional docs in demo/testing

Not allowed:
- Submit/post accounting-impacting docs in production
- Use ignore_permissions

### ai.reader (AI Reader)
Allowed:
- Read-only access
- Run reports, export CSV, generate summaries
- Create File attachments (exports)

Not allowed:
- Create/update business records (masters or transactions)
