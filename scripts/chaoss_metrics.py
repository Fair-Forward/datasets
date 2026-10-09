"""CHAOSS metric definitions and the pure maths behind the open-source health signal.

The catalogue reports facts about each project's open assets (GitHub repositories, Hugging Face
datasets and models, Zenodo records) using metric definitions from CHAOSS, the Linux Foundation's
Community Health Analytics in Open Source Software project. Only the definitions are used, not
CHAOSS software, and they are adapted where a catalogue of datasets and models needs it.

Everything here is pure: no network and no clock. health_check.py fetches and this module counts.
The public methodology page imports the same constants, so the thresholds the site states and the
ones it applies cannot drift apart. See docs/health-thresholds.md.
"""
import math
import re
from datetime import datetime, timedelta, timezone

# Measurement window and status thresholds (days).
WINDOW_DAYS = 365          # "in the last 12 months"
RECENT_DAYS = 365          # < 12 months -> recently_updated
STALE_DAYS = 547           # > 18 months -> no_recent_updates (12-18 month band stays untagged)

# Activity scoring. Feeds the catalogue's default order only; it is never shown as a score.
ACTIVITY_ZERO_DAYS = 730   # recency decays to 0 at ~2 years since the last change
ARCHIVE_RECENCY = 0.6      # stable archives: durable and citable, but not "fresh"
POP_LOG_FULL = 4           # 10^4 (=10,000) downloads/stars saturates popularity at 1.0

ABSENCE_SHARE = 0.5                 # Contributor Absence Factor: people making half the commits
MIN_OUTSIDE_ITEMS = 5               # Time to First Response needs this many outside issues/PRs
MIN_OUTSIDE_CHANGE_REQUESTS = 5     # Change Request Closure Ratio needs this many outside PRs
MAX_RESPONSE_ITEMS = 30             # newest outside items whose replies are read, per repository
MIN_GROUP = 5                       # Insights prints an SDG's upkeep figures from this many projects
CARRY_FORWARD_MAX_DAYS = 28         # an unreachable source keeps its last measurement this long

# GitHub author_association values for people inside a project; anyone else is "outside".
INSIDE_ASSOCIATIONS = frozenset({'OWNER', 'MEMBER', 'COLLABORATOR'})

# Automation accounts the platforms do not mark as bots (CHAOSS Bot Activity). Lower-case.
BOT_LOGINS = frozenset({
    'github-actions', 'dependabot', 'renovate', 'pre-commit-ci', 'allcontributors', 'imgbot',
    'codecov', 'web-flow', 'sfconvertbot', 'librarian-bot', 'parquet-converter',
})

# The weekly job's schedule, stated on the methodology page (checked against the workflow).
SCHEDULE = '0 9 * * 1'
SCHEDULE_TEXT = 'every Monday at 09:00 UTC'

CHAOSS_HOME = 'https://chaoss.community/'
STARTER_MODEL_URL = 'https://chaoss.community/kb/metrics-model-starter-project-health/'
BOT_ACTIVITY_URL = 'https://chaoss.community/?p=3465'

# Each row the detail panel prints, the CHAOSS metric it follows, and that metric's citation URL
# (the stable ?p= link each CHAOSS page names). `starter` marks the Starter Project Health model.
CHAOSS_METRICS = (
    {'key': 'last_change', 'label': 'Last change', 'chaoss': 'Activity Dates and Times',
     'url': 'https://chaoss.community/?p=3444', 'starter': False},
    {'key': 'releases', 'label': 'Releases', 'chaoss': 'Release Frequency',
     'url': 'https://chaoss.community/?p=4765', 'starter': True},
    {'key': 'contributors', 'label': 'Contributors', 'chaoss': 'Contributors',
     'url': 'https://chaoss.community/?p=3467', 'starter': False},
    {'key': 'absence_factor', 'label': 'Absence factor', 'chaoss': 'Contributor Absence Factor',
     'url': 'https://chaoss.community/?p=3944', 'starter': True},
    {'key': 'forks', 'label': 'Reuse', 'chaoss': 'Technical Fork',
     'url': 'https://chaoss.community/?p=3431', 'starter': False},
    {'key': 'popularity', 'label': 'Reuse', 'chaoss': 'Project Popularity',
     'url': 'https://chaoss.community/?p=3573', 'starter': False},
    {'key': 'downloads', 'label': 'Reuse', 'chaoss': 'Number of Downloads',
     'url': 'https://chaoss.community/?p=4466', 'starter': False},
    {'key': 'license', 'label': 'License at source', 'chaoss': 'Licenses Declared',
     'url': 'https://chaoss.community/?p=3963', 'starter': False},
    {'key': 'first_response', 'label': 'Response time', 'chaoss': 'Time to First Response',
     'url': 'https://chaoss.community/?p=3448', 'starter': True},
    {'key': 'change_request_closure', 'label': 'Pull request closure',
     'chaoss': 'Change Request Closure Ratio', 'url': 'https://chaoss.community/?p=4834',
     'starter': True},
)

# Licence ids Hugging Face and Zenodo spell in lower case, mapped to their SPDX spelling. An id
# not listed is reported as "other" with its raw value rather than guessed.
_SPDX_IDS = (
    'MIT', 'Apache-2.0', 'BSD-2-Clause', 'BSD-3-Clause', 'ISC', 'MPL-2.0', 'EPL-2.0', 'BSL-1.0',
    'Unlicense', 'GPL-2.0', 'GPL-3.0', 'LGPL-2.1', 'LGPL-3.0', 'AGPL-3.0', 'AFL-3.0',
    'Artistic-2.0', 'CC0-1.0', 'CC-BY-2.0', 'CC-BY-3.0', 'CC-BY-4.0', 'CC-BY-SA-3.0',
    'CC-BY-SA-4.0', 'CC-BY-NC-3.0', 'CC-BY-NC-4.0', 'CC-BY-NC-SA-3.0', 'CC-BY-NC-SA-4.0',
    'CC-BY-ND-4.0', 'CC-BY-NC-ND-4.0', 'ODbL-1.0', 'ODC-By-1.0', 'PDDL-1.0',
    'CDLA-Permissive-1.0', 'CDLA-Permissive-2.0', 'CDLA-Sharing-1.0',
)
SPDX_CANONICAL = {spdx.lower(): spdx for spdx in _SPDX_IDS}
SPDX_CANONICAL.update({'odbl': 'ODbL-1.0', 'odc-by': 'ODC-By-1.0', 'pddl': 'PDDL-1.0',
                       'cc-zero': 'CC0-1.0', 'cc0': 'CC0-1.0'})

_NOREPLY = re.compile(r'^(?:\d+\+)?([^@]+)@users\.noreply\.github\.com$', re.I)


def parse_ts(value):
    """Parse an ISO datetime or date (Z, offsets, date-only) to an aware UTC datetime, else None."""
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc) if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace('Z', '+00:00'))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def window_bounds(run_date):
    """(start, end) of the measurement window: the WINDOW_DAYS ending with the run day.

    end is the midnight after the run day (exclusive), so the whole run day counts.
    """
    day = parse_ts(run_date)
    end = datetime(day.year, day.month, day.day, tzinfo=timezone.utc) + timedelta(days=1)
    return end - timedelta(days=WINDOW_DAYS), end


def days_between(earlier, run_date):
    """Whole calendar days from a timestamp's date to the run date, or None if unparseable."""
    first, run = parse_ts(earlier), parse_ts(run_date)
    if first is None or run is None:
        return None
    return (run.date() - first.date()).days


def is_bot(login=None, user_type=None, email=None, name=None):
    """True for automation accounts, which CHAOSS counts apart from human activity."""
    if user_type == 'Bot':
        return True
    for text in (login, name):
        if isinstance(text, str) and text.strip():
            low = text.strip().lower()
            if low.endswith('[bot]') or low in BOT_LOGINS:
                return True
    return isinstance(email, str) and '[bot]@' in email.lower()


def identity_key(login=None, email=None, name=None):
    """A lower-cased key that counts one person once within a run. Never written to a file."""
    if isinstance(login, str) and login.strip():
        return 'u:' + login.strip().lower()
    if isinstance(email, str) and email.strip():
        match = _NOREPLY.match(email.strip())
        if match:
            return 'u:' + match.group(1).lower()
        return 'e:' + email.strip().lower()
    if isinstance(name, str) and name.strip():
        return 'n:' + name.strip().lower()
    return None


def absence_factor(counts, share=ABSENCE_SHARE):
    """CHAOSS Contributor Absence Factor: the smallest number of people making `share` of the
    contributions. None when nobody contributed."""
    values = sorted((c for c in counts if c and c > 0), reverse=True)
    total = sum(values)
    if not total:
        return None
    running = 0
    for n, value in enumerate(values, 1):
        running += value
        if running >= share * total:
            return n
    return len(values)


def merge_people(all_time, active):
    """People counts from all-time contributions plus the authors active in the window.

    The contributors endpoint can lag recent commits, so window authors it does not list yet are
    added with their window count, a lower bound.
    """
    combined = dict(all_time)
    for key, count in active.items():
        combined[key] = max(combined.get(key, 0), count)
    return {'total': len(combined), 'active': len(active),
            'absence_factor': absence_factor(combined.values())}


def first_response_summary(items, now, minimum=MIN_OUTSIDE_ITEMS):
    """CHAOSS Time to First Response over outside issues and pull requests.

    items: [{created_at, first_reply_at or None}] as aware datetimes. Returns (summary, gap).
    The lower median is reported in hours. An unanswered item counts its age at `now` as a lower
    bound; when such a bound could reorder the median, the median is flagged as a lower bound.
    """
    items = list(items)
    if len(items) < minimum:
        return None, {'metric': 'first_response', 'reason': 'too_few_items', 'count': len(items)}
    durations = []
    for entry in items:
        reply = entry.get('first_reply_at')
        until = reply if reply is not None else now
        hours = max(0.0, (until - entry['created_at']).total_seconds() / 3600)
        durations.append((hours, reply is None))
    ordered = sorted(hours for hours, _ in durations)
    median = ordered[(len(ordered) - 1) // 2]
    return {
        'items': len(items),
        'answered': sum(1 for _, unanswered in durations if not unanswered),
        'median_hours': round(median, 1),
        'median_is_lower_bound': any(unanswered and hours <= median for hours, unanswered in durations),
    }, None


def closure_summary(prs, minimum=MIN_OUTSIDE_CHANGE_REQUESTS):
    """CHAOSS Change Request Closure Ratio for outside pull requests opened in the window:
    how many were closed (merged or not) by the time of measurement. Returns (summary, gap)."""
    prs = list(prs)
    if len(prs) < minimum:
        return None, {'metric': 'change_request_closure', 'reason': 'too_few_items', 'count': len(prs)}
    return {'opened': len(prs), 'closed': sum(1 for pr in prs if pr.get('closed_at'))}, None


def release_summary(dates, start, end):
    """CHAOSS Release Frequency: releases (or archive versions) in the window, in total, latest."""
    parsed = [d for d in (parse_ts(value) for value in dates) if d is not None]
    latest = max(parsed) if parsed else None
    return {
        'in_window': sum(1 for d in parsed if start <= d < end),
        'total': len(parsed),
        'latest_at': latest.date().isoformat() if latest else None,
    }


def normalise_licenses(value, platform):
    """Licences declared at the source (CHAOSS Licenses Declared) as [{status, spdx, raw}].

    status: detected (an SPDX id), unrecognised (GitHub found a licence file it cannot match),
    other (a custom or unlisted id) or none. GitHub ids are already SPDX; Hugging Face and Zenodo
    ids are lower case and mapped. Several licences are possible on a Hugging Face card.
    """
    values = value if isinstance(value, (list, tuple)) else [value]
    out = []
    for raw in values:
        if not isinstance(raw, str) or not raw.strip():
            continue
        raw = raw.strip()
        if platform == 'github':
            if raw.upper() == 'NOASSERTION':
                out.append({'status': 'unrecognised', 'spdx': None, 'raw': raw})
            else:
                out.append({'status': 'detected', 'spdx': raw, 'raw': raw})
            continue
        spdx = SPDX_CANONICAL.get(raw.lower())
        out.append({'status': 'detected' if spdx else 'other', 'spdx': spdx, 'raw': raw})
    return out or [{'status': 'none', 'spdx': None, 'raw': None}]


def _live_days(dated, run_date):
    """Days since each dated change that is not in an archived repository."""
    days = (days_between(d.get('at'), run_date) for d in dated if not d.get('archived'))
    return [d for d in days if d is not None]


def compute_context(has_archive, dated, run_date):
    """The optional status tag. dated: [{at, archived}] across all of a project's assets.

    Archive records take precedence (frozen by design, a positive signal). Otherwise the freshest
    change outside archived repositories decides; archived repositories alone mean no recent
    updates. The 12-18 month band stays untagged.
    """
    if has_archive:
        return 'stable_archive'
    live = _live_days(dated, run_date)
    if not live:
        return 'no_recent_updates' if any(d.get('archived') for d in dated) else None
    freshest = min(live)
    if freshest < RECENT_DAYS:
        return 'recently_updated'
    if freshest > STALE_DAYS:
        return 'no_recent_updates'
    return None


def compute_activity(context, dated, popularity, run_date):
    """0-100 activity for the default order: recency (0.6) and popularity (0.4).

    popularity: GitHub stars and Hugging Face 30-day downloads across the project's assets; the
    largest counts, log-scaled. None (never 0) when nothing exposes a signal, so a project is
    never pushed down for where its data is hosted.
    """
    recency = None
    if context == 'stable_archive':
        recency = ARCHIVE_RECENCY
    else:
        live = _live_days(dated, run_date)
        if live:
            recency = max(0.0, min(1.0, 1 - min(live) / ACTIVITY_ZERO_DAYS))
        elif any(d.get('archived') for d in dated):
            recency = 0.0
    counts = [p for p in popularity if isinstance(p, int) and not isinstance(p, bool) and p >= 0]
    pop = max(0.0, min(1.0, math.log10(max(counts) + 1) / POP_LOG_FULL)) if counts else None
    parts = [(value, weight) for value, weight in ((recency, 0.6), (pop, 0.4)) if value is not None]
    if not parts:
        return None
    return round(100 * sum(v * w for v, w in parts) / sum(w for _, w in parts))
