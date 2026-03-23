Ship changes directly to main. Stage all changes, commit with a brief summary, and push.

Steps:
1. Run `git status` and `git diff --stat` to understand all changes
2. Run `git log --oneline -5` to match existing commit message style
3. Stage all changes with `git add -A`
4. Write a brief, lowercase commit message (match the repo style: short phrases, no period)
5. Commit and push to main

Keep the commit message short -- one line, summarizing what changed at a high level.
Do NOT ask for confirmation before pushing -- this skill is explicitly for shipping to main.
