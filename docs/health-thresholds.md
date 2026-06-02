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

## Part 3 — Activity score & catalog ranking

Cards are ordered by a combined rank that blends two independently-computed pieces:

- **Documentation completeness** (`quality_score`, 0-100) — computed in
  `scripts/generate_catalog_data.py` and shown as the 5-dot "information depth" indicator. This is
  the primary driver and is unchanged by the health signal.
- **Activity** (`activity_score`, 0-100 or `null`) — computed weekly here in `health_check.py` and
  written into each `health.json` entry. It rewards projects that are actively maintained and used.

### `activity_score`

A weighted blend of two components, scaled to 0-100. It is `null` (not 0) when the entry exposes no
activity signal, so the ranking can stay neutral for those entries rather than penalising them.

- **Recency** (weight 0.6): `stable_archive` scores a fixed `0.6` (durable and citable, but not
  "fresh"); an `archived` GitHub repo scores `0`; otherwise it decays linearly from `1.0` (updated
  today) to `0` at `ACTIVITY_ZERO_DAYS` (730 days / ~2 years), using the freshest of GitHub last
  commit and Hugging Face last-modified.
- **Popularity** (weight 0.4): `log10(max(downloads, stars) + 1) / POP_LOG_FULL`, so ~10,000
  Hugging Face downloads or GitHub stars saturates to `1.0`. GitHub `stars` is read from the same
  API call as `pushed_at` / `archived`.

When only one component is available (e.g. a GitHub repo with no stars, or an archive), the score
uses just that component.

### Combined rank (`src/utils/ranking.js`)

```
rank = quality_score
       - UNAVAILABLE_PENALTY (20)                          if availability == "unavailable"
       + (activity_score / 100) * ACTIVITY_WEIGHT (40)     if activity_score is not null
```

`ACTIVITY_WEIGHT = 40` lets activity contribute up to ~30% of the 0-140 range, so a very active
project can rank above a better-documented but inactive one. Availability is the only signal that
*demotes* an entry, because it is the one signal comparable across every host. **By design, activity
only ever boosts entries where GitHub / Hugging Face expose the data; the absence of activity data
is never a penalty**, so datasets on Zenodo, Dataverse, Kaggle, or plain servers are not pushed down
merely for their host. The 5-dot indicator continues to reflect `quality_score` only.

## Tuning

Availability/context thresholds live as constants at the top of `scripts/health_check.py`
(`RECENT_DAYS`, `STALE_DAYS`, `_ACCESS_RESTRICTED`, `_UNRELIABLE_404_HOSTS`). The activity-score
shape lives alongside them (`ACTIVITY_ZERO_DAYS`, `ARCHIVE_RECENCY`, `POP_LOG_FULL`), and the
ranking weights (`ACTIVITY_WEIGHT`, `UNAVAILABLE_PENALTY`) live in `src/utils/ranking.js`. Update
the code and this document together.
