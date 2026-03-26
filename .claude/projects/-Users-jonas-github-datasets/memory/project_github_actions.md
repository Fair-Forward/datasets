---
name: GitHub Actions for non-technical users
description: Non-technical team members should be able to build and sync the site via GitHub Actions without running Python locally
type: project
---

The full build pipeline should be accessible to non-technical people via GitHub Actions (workflow_dispatch). The existing workflow at `.github/workflows/update_from_google_sheets.yml` provides this. Any new build steps (validation, write-back notes) must also work in the CI environment.

**Why:** Team members who edit the Google Sheet need to trigger rebuilds without a local Python setup.
**How to apply:** Ensure all build scripts work in the GitHub Actions runner, and keep the workflow file updated when scripts are renamed or new steps are added.
