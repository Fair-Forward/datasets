# Security

This document explains the safety measures that protect the Fair Forward Data Catalog from accidental or malicious changes. The goal is to keep the project fully open and collaborative while preventing bad updates from reaching the live website unnoticed.

## How the data pipeline works

The website's content comes from a Google Sheet. When someone clicks "Run workflow" in the GitHub Actions tab, the pipeline:

1. Fetches the latest data from the Google Sheet
2. Converts it into JSON files the website can read
3. Builds the website
4. Publishes the result

This means anyone who can edit the Google Sheet can influence what appears on the website. The security layers below ensure that influence is visible and reversible.

## Security layers

### 1. Change detection

Every time the pipeline runs, it compares the new data against what is currently live on the website. It produces a summary like:

```
Projects: 72 -> 70 (-2, -2.8%)

Removed (2):
- Dataset A
- Dataset B

Added (1):
- Dataset C
```

If more than 5% of projects were removed, the update is flagged as suspicious. This catches bulk deletions -- whether accidental (someone cleared rows by mistake) or intentional (vandalism).

**Technical detail**: The script `scripts/diff_catalog.py` compares `docs/data/catalog.json` (current live version) against `public/data/catalog.json` (newly generated). It runs inside the build pipeline, after data generation but before the website is compiled.

### 2. Pull request gating

The pipeline no longer pushes changes directly to the live website. Instead, it creates a Pull Request (PR) on GitHub:

- **Normal updates**: The PR is created and automatically merged. The experience is the same as before -- click "Run workflow", wait, and the site updates. The PR just provides a paper trail of what changed.
- **Flagged updates** (>5% of projects removed): The PR is created but NOT merged. Its title starts with `[REVIEW NEEDED]`. Someone with repository access must look at the PR, confirm the changes are intentional, and click "Merge pull request."

If someone fixes the Google Sheet and runs the workflow again, the old flagged PR is automatically closed and replaced with the new one.

**For non-technical team members**: If your workflow run shows a yellow warning instead of a green checkmark, ask a team member with GitHub access to review and merge the PR. You can find open PRs at the repository's "Pull requests" tab.

### 3. Easy rollback

If a bad update makes it to the live site, there is a one-click undo:

1. Go to the GitHub Actions tab
2. Select "Revert Last Sheet Update"
3. Click "Run workflow"

This reverts the website to its state before the most recent sheet update. The Google Sheet itself is not affected -- someone still needs to fix the data there, then run the normal update workflow again.

Alternatively, any merged PR on GitHub has a "Revert" button that creates a new PR to undo those specific changes.

### 4. Google Sheet protections

The Google Sheet's header rows (rows 1-2) are protected. These rows define the column structure that the pipeline depends on. If they were changed or deleted, the pipeline could break or produce incorrect data.

The rest of the sheet remains fully editable by anyone with the link. Version history is enabled, so any changes to the sheet can be traced and undone within Google Sheets itself.

### 5. Content security

The pipeline includes defenses against content injection (someone putting malicious code in a sheet cell):

- **URL validation**: Only `http://` and `https://` links are accepted. Dangerous URL types (`javascript:`, `data:`, etc.) are blocked at the data extraction level in `scripts/utils.py`.
- **HTML sanitization**: The website uses ReactMarkdown to render text content, which strips HTML tags by default. Raw HTML in sheet cells appears as plain text, not executable code.
- **Content Security Policy (CSP)**: The website's HTML includes a CSP header that tells browsers to only run scripts from the website's own domain. Even if malicious content somehow made it through all other layers, the browser would block it from executing.
- **Backups**: Every pipeline run creates a timestamped CSV backup of the raw sheet data in `data_sources/google_sheets_backup/`.

## What to do if something goes wrong

| Situation | Action |
|-----------|--------|
| You see `[REVIEW NEEDED]` on a PR | Check whether the removed projects were intentional. If yes, merge the PR. If not, close the PR and fix the sheet. |
| The website shows wrong or missing data | Use the "Revert Last Sheet Update" workflow in GitHub Actions, then fix the Google Sheet and re-run the normal update workflow. |
| Someone made unauthorized changes to the sheet | Use Google Sheets version history (File > Version history) to restore a previous version, then re-run the update workflow. |
| The pipeline fails or produces errors | Check the GitHub Actions run log for error messages. Common causes: column headers were renamed (the pipeline uses fuzzy matching but has limits), or the sheet structure changed significantly. |

## Branch protection settings

The `main` branch requires pull requests before merging and has auto-merge enabled. This means:

- No one (including GitHub Actions) can push directly to `main`
- Safe automated updates merge immediately via auto-merge
- Flagged updates require a human to click "Merge"

These settings are configured in the GitHub repository settings under "Branches > Branch protection rules."
