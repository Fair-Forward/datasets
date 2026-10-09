# Health signal and open-source health: threshold rules

Each catalog entry carries a health signal, recomputed weekly by `scripts/health_check.py` (GitHub
Action: `.github/workflows/health_check.yml`) and written to `public/data/health.json` and
`docs/data/health.json`. The signal is designed to *inform* people evaluating an asset, not to judge
maintainers. Its parts are independent.

The checks look only at an entry's **dataset links** and **use-case / model / app links**
(`dataset_links` + `usecase_links`). Additional resources and hosted documents are not checked.

## Part 1: Availability (always shown)

Availability is the one signal that is comparable across every host: does a link resolve?

- **Available** (`available`): at least one in-scope link is reachable.
- **Link unavailable** (`unavailable`): no in-scope link is reachable, as of the last check.

To avoid putting false statements on the site, "unavailable" is deliberately conservative. We
only count a link as genuinely unreachable on an *unambiguous* failure:

- Connection / DNS / timeout errors, or
- HTTP `404` / `410` on a normal host, or
- HTTP `5xx` server errors.

We do **not** mark a link unavailable for statuses that mean "exists but blocks automated
requests": `401, 403, 405, 406, 409, 429` (auth walls, bot detection, rate limits). These work in
a real browser. Likewise, a `404` from hosts known to bot-block dataset pages (currently
`kaggle.com`) is treated as "exists", not "gone". Specific dead links are still recorded per entry
in `broken_links`, so partial breakage is visible even when the entry overall is `available`.

## Part 2: Context tag (optional, only where the host exposes it)

The context tag is read only from platforms that publish a maintenance signal. Standalone servers
have no readable signal and get no tag: we make no recency claim we cannot back up.

- **Stable archive** (`stable_archive`): a link points at a DOI archive (Zenodo, Harvard
  Dataverse). These are intentionally frozen and permanently citable, so this is a *positive*
  signal. It takes precedence over the recency tags.
- **Recently updated** (`recently_updated`): the freshest change across all of the entry's GitHub
  repositories and Hugging Face assets is within the last **12 months** (`< 365 days`). For GitHub
  the change is the **last commit by a person on the default branch** (bot commits do not count),
  not the last push, which also moves for other branches. For Hugging Face it is `lastModified`.
- **No recent updates** (`no_recent_updates`): the freshest change is older than **18 months**
  (`> 547 days`), or every dated asset is an archived GitHub repository. An archived repository no
  longer hides a Hugging Face dataset that changed recently.
- **(no tag)**: the 12-18 month band is intentionally left untagged (a normal gap, no nagging),
  as are entries whose hosts expose no activity signal.

## Part 3: Activity score and catalog ranking

Cards are ordered by a combined rank that blends two independently computed pieces:

- **Documentation completeness** (`quality_score`, 0-100): computed in
  `scripts/generate_catalog_data.py` and shown as the 5-dot "information depth" indicator. This is
  the primary driver and is unchanged by the health signal.
- **Activity** (`activity_score`, 0-100 or `null`): computed weekly in `health_check.py` and
  written into each `health.json` entry. It rewards projects that are actively maintained and used.
  It is never shown as a score.

### `activity_score`

A weighted blend of two components, scaled to 0-100. It is `null` (not 0) when the entry exposes no
activity signal, so the ranking can stay neutral for those entries rather than penalising them.

- **Recency** (weight 0.6): `stable_archive` scores a fixed `0.6` (durable and citable, but not
  "fresh"); archived GitHub repositories alone score `0`; otherwise it decays linearly from `1.0`
  (changed on the run day) to `0` at `ACTIVITY_ZERO_DAYS` (730 days, about 2 years), using the
  freshest change across all of the entry's assets (Part 2).
- **Popularity** (weight 0.4): `log10(max(downloads, stars) + 1) / POP_LOG_FULL`, so about 10,000
  Hugging Face downloads (last 30 days) or GitHub stars saturates to `1.0`. The largest value across
  all of the entry's assets counts.

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

## Part 4: Open-source health (CHAOSS metric definitions)

Where an entry links a GitHub repository, a Hugging Face model, dataset or space, or a Zenodo
record, the weekly check reads public activity data for **every** such asset and reports facts using
metric definitions from [CHAOSS](https://chaoss.community/) (Community Health Analytics in Open
Source Software, a Linux Foundation project). It uses the definitions, not CHAOSS software, and
reports facts, never scores or rankings. The facts live in each entry's `oss` block
(`health.json` has `schema_version: 2`).

| Detail panel row | CHAOSS metric | What is counted | Sources |
|---|---|---|---|
| Last change | [Activity Dates and Times](https://chaoss.community/?p=3444) | Date of the latest human commit on the default branch, Hugging Face `lastModified`, latest Zenodo version (dates only, no times) | GitHub, Hugging Face, Zenodo |
| Releases | [Release Frequency](https://chaoss.community/?p=4765) | GitHub releases (drafts excluded) and Zenodo versions in the window, in total, and the latest | GitHub, Zenodo |
| Contributors | [Contributors](https://chaoss.community/?p=3467) | People with commits, all time and active in the window | GitHub, Hugging Face |
| Absence factor | [Contributor Absence Factor](https://chaoss.community/?p=3944) | Smallest number of people who made half of all commits | GitHub, Hugging Face |
| Reuse | [Technical Fork](https://chaoss.community/?p=3431), [Project Popularity](https://chaoss.community/?p=3573), [Number of Downloads](https://chaoss.community/?p=4466) | Forks and stars; Hugging Face downloads (last 30 days and all time) and likes; Zenodo downloads and views across all versions | GitHub, Hugging Face, Zenodo |
| License at source | [Licenses Declared](https://chaoss.community/?p=3963) | SPDX id declared by the source (GitHub detection, Hugging Face card, Zenodo metadata) | GitHub, Hugging Face, Zenodo |
| Response time | [Time to First Response](https://chaoss.community/?p=3448) | Median time to the first reply from someone other than the author on outside issues and pull requests | GitHub |
| Pull request closure | [Change Request Closure Ratio](https://chaoss.community/?p=4834) | Outside pull requests opened in the window and closed (merged or not) by the time of measurement | GitHub |

Response time, pull request closure, absence factor and release frequency together form the CHAOSS
[Starter Project Health](https://chaoss.community/kb/metrics-model-starter-project-health/) model.

Rules:

- **Window**: the `WINDOW_DAYS` (365) ending with the run date ("in the last 12 months").
- **People** are counted per platform and combined across a project's assets on that platform, so a
  person counts once; platforms are never summed together. Bots are excluded (CHAOSS
  [Bot Activity](https://chaoss.community/?p=3465): accounts marked as bots plus `BOT_LOGINS`).
  The absence factor uses all-time commits.
- **Outside** means a GitHub `author_association` other than `OWNER`, `MEMBER` or `COLLABORATOR`.
- **Response time** counts a comment or pull request review by someone other than the author and not
  a bot. It reports the lower median; an unanswered item counts its age at measurement as a lower
  bound. It is computed only with at least `MIN_OUTSIDE_ITEMS` (5) outside issues and pull requests
  in the window, pooled across the project's repositories; the newest `MAX_RESPONSE_ITEMS` (30) per
  repository are read.
- **Pull request closure** needs at least `MIN_OUTSIDE_CHANGE_REQUESTS` (5) outside pull requests.
- **Downloads** are counts the platforms report, not unique users. Hugging Face `downloads` is a
  rolling 30-day count; Zenodo counts cover all versions of a record.
- **Gaps are named, never shown as 0.** Each `oss.gaps` item has a reason: `too_few_items`,
  `github_only`, `no_releases_on_platform`, `archive_record`, `gated`, `unreadable`,
  `empty_repository` or `no_human_commits`.
- **Private repositories are refused** even when the token running the check could read them, so a
  local run with a personal token publishes nothing a visitor could not see. Only the statuses a host
  uses for a missing or non-public asset count as "unreadable" (GitHub 404, 410, 451; Hugging Face
  also 401 and 403); bad credentials, a bare 403 or a malformed request fail the run instead and
  fall under carry-forward.
- **Dates after the run day are ignored.** Commit and publication dates come from people's clocks;
  a date in the future never becomes the last change.
- **Forks**: a fork's original repository is named only when an organisation owns it; personal
  account names the catalogue does not list are not published.
- **Carry-forward**: when a source cannot be reached (network errors, rate limits, the request
  budget), the project keeps its previous `oss` block with its own `measured_at` for up to
  `CARRY_FORWARD_MAX_DAYS` (28), provided it covers the same assets. When most sources fail and a
  project would lose its measurement, the run stops without writing.
- **Privacy**: `health.json` holds counts and dates only. Account names are used in memory to count
  people once and are never written to a file or a log; `validate_health()` refuses to write any
  identity field or anything that looks like an email address.
- **Opt-out**: partners can ask for their project to be left out (CHAOSS recommends offering this).
  Add its id to `OPT_OUT_IDS` in `health_check.py`; its links are still checked.
- **Comparison**: CHAOSS advises against comparing projects with each other. Each entry's
  `compare` flags (`open_asset`, `measured`, `changed_12m`, `several_contributors`) are decided once
  in Python for counting by SDG without names; SDGs with fewer than `MIN_GROUP` (5) measured
  projects show coverage only. A named comparison exists only in the private report written by
  `scripts/health_report.py`, which refuses to write inside this repository.

## Tuning

Thresholds and the metric list live in `scripts/chaoss_metrics.py` (`WINDOW_DAYS`, `RECENT_DAYS`,
`STALE_DAYS`, `ACTIVITY_ZERO_DAYS`, `ARCHIVE_RECENCY`, `POP_LOG_FULL`, `ABSENCE_SHARE`,
`MIN_OUTSIDE_ITEMS`, `MIN_OUTSIDE_CHANGE_REQUESTS`, `MAX_RESPONSE_ITEMS`, `MIN_GROUP`,
`CARRY_FORWARD_MAX_DAYS`, `BOT_LOGINS`, `CHAOSS_METRICS`). Availability rules
(`_ACCESS_RESTRICTED`, `_UNRELIABLE_404_HOSTS`) and `OPT_OUT_IDS` live in
`scripts/health_check.py`, the ranking weights (`ACTIVITY_WEIGHT`, `UNAVAILABLE_PENALTY`) in
`src/utils/ranking.js`. Update the code and this document together.

Tests: `python -m unittest discover -s scripts/tests -t scripts` (the weekly workflow runs them
before the check) and `npm test`.
