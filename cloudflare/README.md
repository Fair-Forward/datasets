# Cloudflare Worker: website update trigger

This Worker lets external partners rebuild the website without a GitHub account.
The public page at `public/trigger.html` (served at
`https://fair-forward.github.io/datasets/trigger.html`) POSTs to this Worker,
which holds a GitHub token server-side and dispatches the
`update_from_google_sheets.yml` workflow.

```
trigger.html  ->  Cloudflare Worker  ->  GitHub API  ->  workflow run
                  (holds GITHUB_TOKEN)
```

The token lives in the Worker's encrypted secrets, never in the page source — a
token committed to this public repo would be auto-revoked by GitHub.

## Files

- `trigger-worker.js` — the Worker source (source of truth; paste into Cloudflare if redeploying)

## Deploy / redeploy

1. [dash.cloudflare.com](https://dash.cloudflare.com) -> **Workers & Pages** -> **Create** -> **Create Worker** -> **Start with Hello World!**
2. Name it `datasets-trigger`, **Deploy**, then **Edit code**
3. Paste the contents of `trigger-worker.js`, **Deploy**
4. Add the token secret (see below)

Do not use the "Connect to Git" / repo-import flow — it tries to build the whole
site as a Worker and fails. This is a single standalone script.

## The token secret

The Worker needs a secret named `GITHUB_TOKEN`:

- In the Worker dashboard -> **Settings** -> **Variables and secrets** -> **Add**
- Type: **Secret**, Name: `GITHUB_TOKEN`
- Value: a GitHub **fine-grained PAT** with:
  - Resource owner: `Fair-Forward`
  - Repository access: **Only select repositories** -> `Fair-Forward/datasets`
  - Permissions: **Actions** -> **Read and write**

Secret changes take effect on the next request; no redeploy needed.

Because `Fair-Forward` is an org, a new token may show as **pending** until an org
owner approves it (org **Settings -> Personal access tokens -> Pending requests**).

## Token rotation

Fine-grained PATs expire. When the token expires or is revoked, the trigger page
shows **"Failed to trigger update: Bad credentials"**. To fix:

1. Generate a fresh fine-grained PAT (same settings as above)
2. Update the `GITHUB_TOKEN` secret in the Worker (pencil icon next to the secret)
3. No redeploy needed

## Verify it works

```bash
curl -s -X POST https://datasets-trigger.jonas-nothnagel.workers.dev
# expected: {"ok":true}
```

A `{"ok":true}` response means the token is valid and the workflow was dispatched;
check the [Actions tab](https://github.com/Fair-Forward/datasets/actions) for the run.
`{"ok":false,"message":"Bad credentials"}` means the token needs rotating.
