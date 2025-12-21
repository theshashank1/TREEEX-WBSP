# Information Architecture

This document defines the structure, organization, and standards for the TREEEX-WBSP project documentation.

## Goals

- **Clarity:** Ensure developers can quickly find what they need.
- **Consistency:** Maintain a uniform style and structure across all documents.
- **Maintainability:** Keep documentation aligned with the codebase.
- **Completeness:** Cover all aspects of the system from setup to production.

## Documentation Structure

The documentation is organized into the following hierarchy:

### 1. Root Level (Project Overview)
- **`README.md`**: The entry point. Provides a high-level overview, key features, quick start summary, and links to detailed documentation.
- **`CONTRIBUTING.md`**: Guidelines for contributors, including code style, PR process, and commit conventions.
- **`LICENSE`**: Project license.
- **`SECURITY.md`**: Security policy and vulnerability reporting process.

### 2. Core Documentation (`docs/`)
Detailed guides and references located in the `docs/` directory.

- **Getting Started**
  - **`docs/SETUP.md`**: Comprehensive local development setup guide. Covers prerequisites, environment variables, dependencies, and running the application locally.
  - **`docs/DEPLOYMENT.md`**: Production deployment guide covering server setup, Docker deployment, environment configuration, and monitoring.

- **Guides**
  - **`docs/USAGE.md`**: Practical guide on using the tool. Focuses on workflows (e.g., "How to send a message", "How to create a campaign").
  - **`docs/BEST_PRACTICES.md`**: Recommendations for security, performance, logging, and error handling in production.
  - **`docs/FRONTEND_GUIDE.md`**: Guide for frontend integration.
  - **`docs/TESTING.md`**: Testing strategies, running tests, writing tests, and CI/CD integration.
  - **`docs/TROUBLESHOOTING.md`**: Common issues, error messages, debugging tips, and FAQ.

- **Technical Reference**
  - **`docs/ARCHITECTURE.md`**: High-level system design, detailed component interactions, data flow diagrams (Mermaid), technology stack, and architectural decision records (ADRs).
  - **`docs/API_REFERENCE.md`**: (Auto-generated) Complete API specification derived from OpenAPI schema.
  - **`docs/DATABASE_SCHEMA.md`**: Current database schema, entity relationships, and indexing strategy.
  - **`docs/DATABASE_CHANGES.md`**: Chronological log of database schema changes and migrations.
  - **`docs/ENVIRONMENT_VARIABLES.md`**: Complete reference of all environment variables, their purposes, and default values.

- **Meta**
  - **`docs/INFORMATION_ARCHITECTURE.md`**: This document.
  - **`docs/CHANGELOG.md`**: Version history and release notes following semantic versioning.

### 3. Supporting Resources

- **`docs/diagrams/`**: Directory for complex Mermaid diagram source files and exported images.
- **`docs/templates/`**: Document templates (e.g., ADR template, bug report template).
- **`docs/examples/`**: Code examples and sample configurations.

## Formatting Standards

### File Naming
- Use `UPPER_CASE.md` for major documentation files to make them stand out.
- Use descriptive names that clearly indicate content (e.g., `DATABASE_SCHEMA.md` not `DB.md`).

### Document Structure
- **Front Matter**: Start each document with a brief description and last updated date.
- **Table of Contents**: Include a TOC for documents longer than 3 sections (use `## Table of Contents`).
- **Headings**:
  - Use sentence case (e.g., "Getting started", "Configuration options").
  - Use H1 (`#`) only for the document title.
  - Create logical hierarchy with H2-H4; avoid H5-H6.

### Content Formatting
- **Code Blocks**: Always specify the language for syntax highlighting:
```python
  # Good
  def example():
      pass
```
- **Commands**: Use `bash` for shell commands:
```bash
  npm install
  python manage.py runserver
```
- **File Paths**: Use inline code for paths: `src/main.py`
- **Links**:
  - Use relative paths for internal links: `[Setup Guide](./SETUP.md)`
  - Use descriptive link text, not "click here"
- **Lists**:
  - Use `-` for unordered lists (not `*` or `+`)
  - Use `1.` for ordered lists
  - Maintain consistent indentation (2 spaces)
- **Diagrams**: Use Mermaid for diagrams where possible for easy maintenance and version control.
- **Tables**: Use tables for structured comparisons or reference data.

### Style Guidelines
- **Tone**: Professional but approachable; avoid jargon where possible.
- **Voice**: Use second person ("you") in guides; use third person in reference docs.
- **Tense**: Use present tense (e.g., "This function returns" not "This function will return").
- **Examples**: Provide concrete examples for abstract concepts.
- **Warnings**: Use blockquotes for important notes:
```markdown
  > **Warning:** This action cannot be undone.
```

## Maintenance

### Regular Updates
- **API Docs**: Run `python docs/generate_docs.py` after modifying API routes or Pydantic models to regenerate `API_REFERENCE.md`.
- **Database Schema**: Update `DATABASE_SCHEMA.md` after migrations; log changes in `DATABASE_CHANGES.md`.
- **Changelog**: Update `CHANGELOG.md` with every release following [Keep a Changelog](https://keepachangelog.com/) format.
- **Review**: Review documentation changes in every Pull Request.

### When to Update Which Document

| Change Type | Documents to Update |
|-------------|-------------------|
| New API endpoint | `API_REFERENCE.md` (auto), `USAGE.md` (if user-facing) |
| New feature | `README.md`, `CHANGELOG.md`, `USAGE.md` |
| Database migration | `DATABASE_SCHEMA.md`, `DATABASE_CHANGES.md` |
| Configuration change | `SETUP.md`, `ENVIRONMENT_VARIABLES.md` |
| Architecture decision | `ARCHITECTURE.md` (add ADR) |
| Bug fix | `CHANGELOG.md`, `TROUBLESHOOTING.md` (if relevant) |
| Deployment process | `DEPLOYMENT.md` |
| Testing approach | `TESTING.md` |

### Documentation Versioning
- Documentation tracks the `main` branch by default.
- For major version releases, consider tagging documentation snapshots.
- Use version badges in README to indicate which version docs describe.

### Quality Checks
Before merging documentation changes:
- [ ] All links work (internal and external)
- [ ] Code examples are tested and work
- [ ] Formatting is consistent with standards
- [ ] No spelling or grammar errors
- [ ] Screenshots/diagrams are up-to-date
- [ ] Table of contents is updated (if applicable)

## Documentation Templates

### Architectural Decision Record (ADR)
```markdown
# ADR-XXX: [Title]

**Date:** YYYY-MM-DD
**Status:** [Proposed | Accepted | Deprecated | Superseded]

## Context
[What is the issue we're facing?]

## Decision
[What decision did we make?]

## Consequences
[What are the positive and negative outcomes?]
```

### Bug Report Template
Link to `.github/ISSUE_TEMPLATE/bug_report.md` for consistency.

## Tools and Automation

- **MkDocs** (optional): Consider using MkDocs for a searchable documentation site.
- **Link Checker**: Set up automated link checking in CI/CD.
- **Spell Checker**: Consider integrating spell checking tools.
- **Documentation Coverage**: Track which modules/features lack documentation.

---

**Last Updated:** 2025-12-21
**Maintained By:** SHASHANK
