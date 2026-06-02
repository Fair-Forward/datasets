# Health / Sustainability Signal — Threshold Rules

Each catalog entry shows a two-part health signal, recomputed weekly by
`scripts/health_check.py` (GitHub Action: `.github/workflows/health_check.yml`) and written to
`data/health.json`. The signal is designed to *inform* people evaluating an asset, not to judge
maintainers. The two parts are independent.

The checks look only at an entry's **dataset links** and **use-case / model / app links**
(`dataset_links` + `usecase_links`). Additional resources and hosted documents are not checked.

## Part 1 — Availability (always shown)

Availability is the one signal that is comparable across every host: does a link resolve?

- **Available** (`available`) — at least one in-scope link is reachable.
- **Link unavailable** (`unavailable`) — no in-scope link is reachable, as of the last check.

To avoid putting false statements on the site, "unavailable" is deliberately conservative. We
only count a link as genuinely unreachable on an *unambiguous* failure:

- Connection / DNS / timeout errors, or
- HTTP `404` / `410` on a normal host, or
- HTTP `5xx` server errors.

We do **not** mark a link unavailable for statuses that mean "exists but blocks automated
requests" — `401, 403, 405, 406, 409, 429` (auth walls, bot detection, rate limits). These work in
a real browser. Likewise, a `404` from hosts known to bot-block dataset pages (currently
`kaggle.com`) is treated as "exists", not "gone". Specific dead links are still recorded per entry
in `broken_links`, so partial breakage is visible even when the entry overall is `available`.

## Part 2 — Context tag (optional, only where the host exposes it)

The context tag is read only from platforms that publish a maintenance signal. Standalone servers
have no readable signal and get no tag — we make no recency claim we cannot back up.

- **Stable archive** (`stable_archive`) — a link points at a DOI archive (Zenodo, Harvard
  Dataverse). These are intentionally frozen and permanently citable, so this is a *positive*
  signal. It takes precedence over the recency tags.
- **Recently updated** (`recently_updated`) — GitHub last push or Hugging Face last-modified is
  within the last **12 months** (`< 365 days`).
- **No recent updates** (`no_recent_updates`) — GitHub/HF last activity is older than **18 months**
  (`> 547 days`), or the GitHub repository is flagged `archived`.
- **(no tag)** — the 12–18 month band is intentionally left untagged (a normal gap, no nagging),
  as are entries whose hosts expose no activity signal.

## Tuning

Thresholds live as constants at the top of `scripts/health_check.py` (`RECENT_DAYS`,
`STALE_DAYS`, `_ACCESS_RESTRICTED`, `_UNRELIABLE_404_HOSTS`). Update both the code and this
document together.
