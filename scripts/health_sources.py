"""Read public activity data from GitHub, Hugging Face, Zenodo and doi.org.

ApiClient wraps one host: a request budget per run, polite spacing, retries with backoff for
server and network errors, and waits on the hosts' rate-limit headers. Fetchers turn one asset into
a record of public facts (dates, counts, licences) plus in-memory working data.

Privacy: account names and emails are needed only to count each person once. They live in the
`people` maps a fetcher returns, which health_check.py combines per project and discards. They are
never written to a file or a log. Private repositories are refused even when a token can see them,
so a local run with a personal token publishes nothing a public visitor could not see.
"""
import re
import time

import requests

from chaoss_metrics import (INSIDE_ASSOCIATIONS, MAX_RESPONSE_ITEMS, identity_key, is_bot,
                            merge_people, normalise_licenses, parse_ts, release_summary)
from health_assets import classify_url

GITHUB_API = 'https://api.github.com'
HF_API = 'https://huggingface.co/api'
ZENODO_API = 'https://zenodo.org/api'
DOI_HANDLES = 'https://doi.org/api/handles'

# Failures worth carrying a previous measurement over; "unavailable" is a lasting fact instead.
TRANSIENT = frozenset({'failed', 'budget', 'rate_limited'})

_LINK_NEXT = re.compile(r'<([^>]+)>\s*;\s*rel="?next"?', re.I)


class SourceError(Exception):
    """kind: unavailable (missing, private, auth wall), failed, budget or rate_limited."""

    def __init__(self, kind, status=None, detail=''):
        text = kind + (f' ({status})' if status else '') + (f': {detail}' if detail else '')
        super().__init__(text)
        self.kind = kind
        self.status = status


def _header(headers, name):
    if not headers:
        return None
    for key, value in headers.items():
        if key.lower() == name:
            return value
    return None


def _next_link(headers):
    match = _LINK_NEXT.search(_header(headers, 'link') or '')
    return match.group(1) if match else None


class ApiClient:
    """GET JSON from one host within a request budget, retrying what is worth retrying."""

    def __init__(self, name, headers=None, budget=100, min_interval=0.0, max_wait=120, retries=3,
                 timeout=(5, 20), session=None, sleep=time.sleep, clock=time.time):
        self.name = name
        self.headers = dict(headers or {})
        self.budget = budget
        self.min_interval = min_interval
        self.max_wait = max_wait
        self.retries = retries
        self.timeout = timeout
        self.session = session or requests.Session()
        self.sleep = sleep
        self.clock = clock
        self.used = 0
        self._last = None

    def _rate_limit_wait(self, headers):
        """Seconds the host asks us to wait, or None when the response is not a rate limit."""
        retry_after = _header(headers, 'retry-after')
        if retry_after is not None:
            try:
                return max(0.0, float(retry_after))
            except ValueError:
                pass
        if _header(headers, 'x-ratelimit-remaining') == '0':
            try:
                return max(0.0, float(_header(headers, 'x-ratelimit-reset')) - self.clock()) + 1
            except (TypeError, ValueError):
                pass
        policy = _header(headers, 'ratelimit')  # Hugging Face: '"api";r=<remaining>;t=<seconds>'
        if policy:
            remaining, reset = re.search(r'\br=(\d+)', policy), re.search(r'\bt=(\d+)', policy)
            if remaining and reset and int(remaining.group(1)) == 0:
                return float(reset.group(1)) + 1
        return None

    def _retry(self, attempt, kind, status=None):
        """Back off before the next attempt, or raise once the retries are spent."""
        if attempt > self.retries:
            raise SourceError(kind, status)
        self.sleep(2 ** attempt)

    def get_json(self, url, params=None):
        """(data, headers) for a 2xx response; data is None for 204. Raises SourceError."""
        attempt = 0
        while True:
            if self.used >= self.budget:
                raise SourceError('budget', detail=self.name)
            if self.min_interval and self._last is not None:
                wait = self.min_interval - (self.clock() - self._last)
                if wait > 0:
                    self.sleep(wait)
            self.used += 1
            self._last = self.clock()
            try:
                resp = self.session.get(url, params=params, headers=self.headers, timeout=self.timeout)
            except requests.exceptions.RequestException:
                attempt += 1
                self._retry(attempt, 'failed')
                continue
            status = resp.status_code
            if status == 204:
                return None, resp.headers
            if 200 <= status < 300:
                try:
                    return resp.json(), resp.headers
                except ValueError:
                    raise SourceError('failed', status, 'invalid JSON')
            if status in (401, 403, 429):
                wait = self._rate_limit_wait(resp.headers)
                if wait is not None:
                    attempt += 1
                    if wait > self.max_wait or attempt > self.retries:
                        raise SourceError('rate_limited', status)
                    self.sleep(wait)
                    continue
                if status == 429:
                    attempt += 1
                    self._retry(attempt, 'rate_limited', status)
                    continue
                raise SourceError('unavailable', status)
            if status >= 500:
                attempt += 1
                self._retry(attempt, 'failed', status)
                continue
            raise SourceError('unavailable', status)

    def paginate(self, url, params=None, max_pages=5, stop=None):
        """(items, complete) across pages linked by rel="next". complete is False when the
        listing was cut at max_pages; stop(page) ends the listing early as complete."""
        items, pages, next_url, next_params = [], 0, url, params
        while next_url and pages < max_pages:
            data, headers = self.get_json(next_url, next_params)
            pages += 1
            page = data if isinstance(data, list) else []
            items.extend(page)
            if stop and page and stop(page):
                return items, True
            next_url, next_params = _next_link(headers), None
        return items, next_url is None


def _day(value):
    parsed = parse_ts(value)
    return parsed.date().isoformat() if parsed else None


def _iso(moment):
    return moment.strftime('%Y-%m-%dT%H:%M:%SZ')


def _result(record, people=None, response_items=None, outside_prs=None):
    return {'record': record, 'people': people, 'response_items': response_items or [],
            'outside_prs': outside_prs or []}


def _human_commit(commit):
    author = commit.get('author') or {}
    meta = (commit.get('commit') or {}).get('author') or {}
    if is_bot(author.get('login'), author.get('type'), meta.get('email'), meta.get('name')):
        return None
    return identity_key(author.get('login'), meta.get('email'), meta.get('name')) or 'n:unknown'


def _committed_at(commit):
    return parse_ts(((commit.get('commit') or {}).get('committer') or {}).get('date'))


def _listing(gh, url):
    """A list endpoint's first page, or [] when it cannot be read (counted as no reply)."""
    try:
        data, _ = gh.get_json(url, {'per_page': 100})
    except SourceError as err:
        if err.kind != 'unavailable':
            raise
        return []
    return data if isinstance(data, list) else []


def _first_reply(gh, base, item):
    """When someone other than the author (and not a bot) first replied, or None."""
    author = (item.get('user') or {}).get('login')
    replies = []
    if item.get('comments'):
        for comment in _listing(gh, f"{base}/issues/{item['number']}/comments"):
            user = comment.get('user') or {}
            if user.get('login') != author and not is_bot(user.get('login'), user.get('type')):
                replies.append(parse_ts(comment.get('created_at')))
                break
    if item.get('pull_request'):
        for review in _listing(gh, f"{base}/pulls/{item['number']}/reviews"):
            user = review.get('user') or {}
            if (user.get('login') != author and not is_bot(user.get('login'), user.get('type'))
                    and review.get('submitted_at')):
                replies.append(parse_ts(review['submitted_at']))
                break
    replies = [moment for moment in replies if moment]
    return min(replies) if replies else None


def fetch_github_repo(gh, owner, repo, window):
    """CHAOSS facts for one public GitHub repository within the measurement window."""
    start, end = window
    data, _ = gh.get_json(f'{GITHUB_API}/repos/{owner}/{repo}')
    if not isinstance(data, dict):
        raise SourceError('failed', detail='unexpected repository response')
    if data.get('private') or data.get('visibility', 'public') != 'public':
        raise SourceError('unavailable', detail='not public')
    full = data.get('full_name') or f'{owner}/{repo}'
    base = f'{GITHUB_API}/repos/{full}'
    branch = data.get('default_branch') or 'main'
    record = {
        'platform': 'github', 'id': full,
        'renamed_from': f'{owner}/{repo}' if full.lower() != f'{owner}/{repo}'.lower() else None,
        'fork_of': (data.get('parent') or {}).get('full_name') if data.get('fork') else None,
        'archived': bool(data.get('archived')),
        'forks': data.get('forks_count'), 'stars': data.get('stargazers_count'),
        'license': normalise_licenses((data.get('license') or {}).get('spdx_id'), 'github'),
        'last_change_at': None, 'gaps': [],
    }

    # Commits on the default branch in the window: who was active, and the last human change.
    try:
        commits, _ = gh.paginate(f'{base}/commits',
                                 {'sha': branch, 'since': _iso(start), 'per_page': 100}, max_pages=10)
    except SourceError as err:
        if err.status == 409:  # GitHub answers 409 for a repository without commits
            record['gaps'].append({'metric': 'last_change', 'reason': 'empty_repository'})
            return _result(record)
        raise
    active, last_human = {}, None
    for commit in commits:
        key = _human_commit(commit)
        if key is None:
            continue
        active[key] = active.get(key, 0) + 1
        moment = _committed_at(commit)
        if moment and (last_human is None or moment > last_human):
            last_human = moment
    if last_human is None:
        # Nobody committed in the window: read the newest page of history once.
        recent, _ = gh.get_json(f'{base}/commits', {'sha': branch, 'per_page': 30})
        recent = recent or []
        human = [c for c in recent if _human_commit(c) is not None]
        dates = [m for m in (_committed_at(c) for c in (human or recent)) if m]
        last_human = max(dates) if dates else None
    record['last_change_at'] = last_human.date().isoformat() if last_human else None

    # All-time contributors, bots removed; anonymous ones count by email.
    contributors, _ = gh.paginate(f'{base}/contributors', {'anon': 1, 'per_page': 100}, max_pages=5)
    all_time = {}
    for person in contributors:
        if person.get('type') == 'Anonymous':
            if is_bot(email=person.get('email'), name=person.get('name')):
                continue
            key = identity_key(email=person.get('email'), name=person.get('name'))
        else:
            if is_bot(person.get('login'), person.get('type')):
                continue
            key = identity_key(login=person.get('login'))
        if key:
            all_time[key] = all_time.get(key, 0) + int(person.get('contributions') or 0)
    people = merge_people(all_time, active)
    record.update({'contributors_total': people['total'], 'contributors_active': people['active'],
                   'absence_factor': people['absence_factor']})

    releases, _ = gh.paginate(f'{base}/releases', {'per_page': 100}, max_pages=3)
    summary = release_summary([r.get('published_at') for r in releases if not r.get('draft')], start, end)
    record.update({'releases_in_window': summary['in_window'], 'releases_total': summary['total'],
                   'latest_release_at': summary['latest_at']})

    # Issues and pull requests opened in the window by people outside the project.
    def older_than_window(page):
        created = parse_ts(page[-1].get('created_at'))
        return created is not None and created < start

    try:
        items, _ = gh.paginate(f'{base}/issues', {'state': 'all', 'sort': 'created', 'direction': 'desc',
                                                  'per_page': 100}, max_pages=5, stop=older_than_window)
    except SourceError as err:
        if err.kind != 'unavailable':
            raise
        items = []  # no issue tracker
    outside = []
    for item in items:
        created = parse_ts(item.get('created_at'))
        user = item.get('user') or {}
        if (created is not None and start <= created < end
                and item.get('author_association') not in INSIDE_ASSOCIATIONS
                and not is_bot(user.get('login'), user.get('type'))):
            outside.append(item)
    outside_prs = [{'created_at': parse_ts(i['created_at']), 'closed_at': parse_ts(i.get('closed_at'))}
                   for i in outside if i.get('pull_request')]
    record.update({'outside_items': len(outside), 'outside_change_requests': len(outside_prs)})
    # Replies are read for every outside item (newest first) so a project can pool its repositories
    # before the Time to First Response minimum applies.
    response_items = [{'created_at': parse_ts(item['created_at']), 'first_reply_at': _first_reply(gh, base, item)}
                      for item in outside[:MAX_RESPONSE_ITEMS]]

    # Community files. GitHub has no community profile for forks.
    record['files'] = None
    if not data.get('fork'):
        try:
            profile, _ = gh.get_json(f'{base}/community/profile')
            files = (profile or {}).get('files') or {}
            record['files'] = {name: bool(files.get(name)) for name in ('readme', 'contributing', 'code_of_conduct')}
        except SourceError as err:
            if err.kind != 'unavailable':
                raise

    return _result(record, {'all_time': all_time, 'active': active}, response_items, outside_prs)


_HF_EXPAND = ('private', 'gated', 'disabled', 'likes', 'lastModified', 'createdAt', 'cardData')
_HF_DOWNLOADS = ('downloads', 'downloadsAllTime')


def fetch_hf_asset(hf, kind, repo_id, window):
    """CHAOSS facts for one public Hugging Face model, dataset or space."""
    start, end = window
    fields = _HF_EXPAND + (() if kind == 'spaces' else _HF_DOWNLOADS)
    data, _ = hf.get_json(f'{HF_API}/{kind}/{repo_id}', [('expand[]', field) for field in fields])
    if not isinstance(data, dict):
        raise SourceError('failed', detail='unexpected repository response')
    if data.get('private') or data.get('disabled'):
        raise SourceError('unavailable', detail='not public')
    current = data.get('id') or repo_id
    record = {
        'platform': 'huggingface', 'kind': kind, 'id': current,
        'renamed_from': repo_id if current.lower() != repo_id.lower() else None,
        'gated': data.get('gated') or False,
        'last_change_at': _day(data.get('lastModified')), 'created_at': _day(data.get('createdAt')),
        'likes': data.get('likes'), 'downloads_30d': data.get('downloads'),
        'downloads_all_time': data.get('downloadsAllTime'),
        'license': normalise_licenses((data.get('cardData') or {}).get('license'), 'huggingface'),
        'contributors_total': None, 'contributors_active': None, 'absence_factor': None,
        'discussions': None, 'gaps': [],
    }
    people = None
    try:
        commits, _ = hf.paginate(f'{HF_API}/{kind}/{current}/commits/main', max_pages=10)
    except SourceError as err:
        if err.kind != 'unavailable':
            raise
        reason = 'gated' if record['gated'] else 'unreadable'
        record['gaps'].append({'metric': 'contributors', 'reason': reason})
    else:
        all_time, active = {}, {}
        for commit in commits:
            moment = parse_ts(commit.get('date'))
            for author in commit.get('authors') or []:
                user = author.get('user')
                if not user or is_bot(login=user):
                    continue
                key = identity_key(login=user)
                all_time[key] = all_time.get(key, 0) + 1
                if moment and start <= moment < end:
                    active[key] = active.get(key, 0) + 1
        summary = merge_people(all_time, active)
        record.update({'contributors_total': summary['total'], 'contributors_active': summary['active'],
                       'absence_factor': summary['absence_factor']})
        people = {'all_time': all_time, 'active': active}
    try:
        discussions, _ = hf.get_json(f'{HF_API}/{kind}/{current}/discussions')
        if isinstance(discussions, dict):
            record['discussions'] = {'total': discussions.get('count'),
                                     'closed': discussions.get('numClosedDiscussions')}
    except SourceError as err:
        if err.kind != 'unavailable':
            raise
    return _result(record, people)


def fetch_zenodo_record(zen, record_id, window):
    """Facts for one Zenodo record: versions (release frequency), downloads and views across all
    versions, licence. A record has no commit or issue history, so no people metrics."""
    start, end = window
    data, _ = zen.get_json(f'{ZENODO_API}/records/{record_id}')
    if not isinstance(data, dict):
        raise SourceError('failed', detail='unexpected record response')
    meta = data.get('metadata') or {}
    stats = data.get('stats') or {}
    relation = ((meta.get('relations') or {}).get('version') or [{}])[0] or {}

    dates, page, size = [], 1, 25
    try:
        while page <= 8:
            body, _ = zen.get_json(f'{ZENODO_API}/records/{record_id}/versions', {'size': size, 'page': page})
            hits = ((body or {}).get('hits') or {}).get('hits') or []
            dates.extend((h.get('metadata') or {}).get('publication_date') or h.get('created') for h in hits)
            total = ((body or {}).get('hits') or {}).get('total') or 0
            total = total.get('value', 0) if isinstance(total, dict) else total
            if len(hits) < size or page * size >= total:
                break
            page += 1
    except SourceError as err:
        if err.kind != 'unavailable':
            raise
        # No versions listing: the record's own date and version count still stand.
        dates = [meta.get('publication_date')]
    summary = release_summary(dates, start, end)
    latest = (relation.get('last_child') or {}).get('pid_value')
    record = {
        'platform': 'zenodo', 'id': str(record_id),
        'concept_id': str(data['conceptrecid']) if data.get('conceptrecid') else None,
        'linked_is_latest': relation.get('is_last'),
        'latest_id': str(latest) if latest else None,
        'versions_total': max(summary['total'], relation.get('count') or 0),
        'versions_in_window': summary['in_window'],
        'last_change_at': summary['latest_at'] or _day(meta.get('publication_date')),
        'downloads_all_time': stats.get('downloads'), 'views_all_time': stats.get('views'),
        'license': normalise_licenses((meta.get('license') or {}).get('id'), 'zenodo'),
        'resource_type': (meta.get('resource_type') or {}).get('type'),
        'access_right': meta.get('access_right'),
        'gaps': [],
    }
    return _result(record)


def resolve_doi(client, doi):
    """classify_url() of the URL a DOI points to, with that url added; None if it has none."""
    body, _ = client.get_json(f'{DOI_HANDLES}/{doi}')
    for value in (body or {}).get('values') or []:
        if value.get('type') == 'URL':
            url = (value.get('data') or {}).get('value')
            if url:
                return dict(classify_url(url), url=url)
    return None
