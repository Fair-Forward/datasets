"""Tests for health_sources: the HTTP client and the GitHub, Hugging Face and Zenodo fetchers.

A fake session stands in for the network, so no test calls a real API. Logins and emails in the
fixtures are invented.
"""
import json
import unittest

import requests

import chaoss_metrics as cm
import health_sources as hs

WINDOW = cm.window_bounds('2026-10-08')
GH = 'https://api.github.com/repos'
HF = 'https://huggingface.co/api'
ZEN = 'https://zenodo.org/api/records'


class FakeResponse:
    def __init__(self, status=200, body=None, headers=None):
        self.status_code = status
        self._body = body
        self.headers = headers or {}

    def json(self):
        if isinstance(self._body, Exception):
            raise self._body
        return self._body


class FakeSession:
    """routes: url -> response, list of responses (served in order), or callable(url, params)."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def get(self, url, params=None, headers=None, timeout=None):
        self.calls.append((url, params))
        route = self.routes.get(url)
        if callable(route):
            return route(url, params)
        if isinstance(route, list):
            item = route.pop(0)
            if isinstance(item, Exception):
                raise item
            return item
        return route if route is not None else FakeResponse(404)


class FakeClock:
    def __init__(self, now=1_000_000.0):
        self.now = now
        self.slept = []

    def time(self):
        return self.now

    def sleep(self, seconds):
        self.slept.append(seconds)
        self.now += seconds


def client(routes, budget=100, **kw):
    clock = FakeClock()
    session = FakeSession(routes)
    api = hs.ApiClient('test', budget=budget, session=session, sleep=clock.sleep, clock=clock.time, **kw)
    return api, session, clock


class ApiClientTests(unittest.TestCase):
    def test_returns_json_and_counts_requests(self):
        api, session, _ = client({'u': FakeResponse(200, {'a': 1})})
        data, _ = api.get_json('u')
        self.assertEqual(data, {'a': 1})
        self.assertEqual(api.used, 1)

    def test_a_404_is_unavailable_without_retrying(self):
        api, session, _ = client({})
        with self.assertRaises(hs.SourceError) as ctx:
            api.get_json('missing')
        self.assertEqual((ctx.exception.kind, ctx.exception.status), ('unavailable', 404))
        self.assertEqual(len(session.calls), 1)

    def test_server_errors_are_retried_with_backoff(self):
        api, session, clock = client({'u': [FakeResponse(502), FakeResponse(502), FakeResponse(200, [1])]})
        data, _ = api.get_json('u')
        self.assertEqual(data, [1])
        self.assertEqual(clock.slept, [2, 4])

    def test_gives_up_after_the_retries_as_failed(self):
        api, session, _ = client({'u': [FakeResponse(500)] * 4})
        with self.assertRaises(hs.SourceError) as ctx:
            api.get_json('u')
        self.assertEqual(ctx.exception.kind, 'failed')
        self.assertEqual(len(session.calls), 4)

    def test_network_errors_are_retried(self):
        api, _, _ = client({'u': [requests.exceptions.ConnectionError(), FakeResponse(200, {'ok': True})]})
        self.assertEqual(api.get_json('u')[0], {'ok': True})

    def test_waits_for_a_short_github_rate_limit_reset(self):
        clock_now = 1_000_000.0
        limited = FakeResponse(403, {}, {'X-RateLimit-Remaining': '0', 'X-RateLimit-Reset': str(int(clock_now + 5))})
        api, _, clock = client({'u': [limited, FakeResponse(200, {'ok': 1})]})
        self.assertEqual(api.get_json('u')[0], {'ok': 1})
        self.assertEqual(clock.slept, [6.0])

    def test_a_long_rate_limit_wait_is_reported_not_slept(self):
        limited = FakeResponse(403, {}, {'x-ratelimit-remaining': '0', 'x-ratelimit-reset': str(int(1_000_000 + 3600))})
        api, _, clock = client({'u': [limited]})
        with self.assertRaises(hs.SourceError) as ctx:
            api.get_json('u')
        self.assertEqual(ctx.exception.kind, 'rate_limited')
        self.assertEqual(clock.slept, [])

    def test_honours_retry_after(self):
        api, _, clock = client({'u': [FakeResponse(429, {}, {'Retry-After': '3'}), FakeResponse(200, {})]})
        api.get_json('u')
        self.assertEqual(clock.slept, [3.0])

    def test_reads_the_hugging_face_ratelimit_header(self):
        api, _, clock = client({'u': [FakeResponse(429, {}, {'RateLimit': '"api";r=0;t=7'}), FakeResponse(200, {})]})
        api.get_json('u')
        self.assertEqual(clock.slept, [8.0])

    def test_auth_walls_without_rate_limit_headers_are_unavailable(self):
        api, _, _ = client({'u': FakeResponse(401, {})})
        with self.assertRaises(hs.SourceError) as ctx:
            api.get_json('u')
        self.assertEqual(ctx.exception.kind, 'unavailable')

    def test_stops_at_the_request_budget(self):
        api, _, _ = client({'u': FakeResponse(200, {})}, budget=1)
        api.get_json('u')
        with self.assertRaises(hs.SourceError) as ctx:
            api.get_json('u')
        self.assertEqual(ctx.exception.kind, 'budget')

    def test_spaces_requests_by_the_minimum_interval(self):
        api, _, clock = client({'u': FakeResponse(200, {})}, min_interval=0.5)
        api.get_json('u')
        api.get_json('u')
        self.assertEqual(clock.slept, [0.5])

    def test_no_content_returns_none(self):
        api, _, _ = client({'u': FakeResponse(204)})
        self.assertIsNone(api.get_json('u')[0])

    def test_paginate_follows_the_link_header(self):
        routes = {'p1': FakeResponse(200, [1, 2], {'Link': '<p2>; rel="next", <p2>; rel="last"'}),
                  'p2': FakeResponse(200, [3])}
        api, _, _ = client(routes)
        self.assertEqual(api.paginate('p1'), ([1, 2, 3], True))

    def test_paginate_reports_an_incomplete_listing(self):
        routes = {'p1': FakeResponse(200, [1], {'link': '<p2>; rel="next"'}), 'p2': FakeResponse(200, [2])}
        api, _, _ = client(routes)
        self.assertEqual(api.paginate('p1', max_pages=1), ([1], False))

    def test_paginate_can_stop_early(self):
        routes = {'p1': FakeResponse(200, [1, 2], {'Link': '<p2>; rel="next"'}), 'p2': FakeResponse(200, [3])}
        api, session, _ = client(routes)
        self.assertEqual(api.paginate('p1', stop=lambda page: True), ([1, 2], True))
        self.assertEqual(len(session.calls), 1)


def gh_commit(login, date, email=None, user_type='User'):
    return {'author': {'login': login, 'type': user_type} if login else None,
            'commit': {'author': {'email': email or f'{login}@example.org', 'name': login or 'anon'},
                       'committer': {'date': date}}}


def gh_item(number, created, association='NONE', login='visitor', pr=False, comments=0, closed=None):
    item = {'number': number, 'created_at': created, 'author_association': association,
            'user': {'login': login, 'type': 'User'}, 'comments': comments, 'closed_at': closed}
    if pr:
        item['pull_request'] = {'merged_at': closed}
    return item


def github_routes(**overrides):
    base = f'{GH}/New-Org/Repo'

    def commits(url, params):
        if params and params.get('since'):
            return FakeResponse(200, [gh_commit('alice', '2026-08-02T08:54:46Z'),
                                      gh_commit('dependabot[bot]', '2026-09-01T00:00:00Z', user_type='Bot'),
                                      gh_commit('bob', '2026-03-01T00:00:00Z')])
        return FakeResponse(200, [])

    routes = {
        f'{GH}/Old-Org/Repo': FakeResponse(200, {
            'full_name': 'New-Org/Repo', 'private': False, 'visibility': 'public', 'default_branch': 'main',
            'archived': False, 'fork': False, 'forks_count': 3, 'stargazers_count': 7,
            'license': {'spdx_id': 'MIT'}}),
        f'{base}/commits': commits,
        f'{base}/contributors': FakeResponse(200, [
            {'login': 'alice', 'type': 'User', 'contributions': 198},
            {'login': 'bob', 'type': 'User', 'contributions': 187},
            {'type': 'Anonymous', 'email': 'carol@example.org', 'name': 'Carol', 'contributions': 49},
            {'login': 'github-actions[bot]', 'type': 'Bot', 'contributions': 500}]),
        f'{base}/releases': FakeResponse(200, [
            {'draft': False, 'published_at': '2026-06-03T10:00:00Z'},
            {'draft': True, 'published_at': None},
            {'draft': False, 'published_at': '2024-01-01T10:00:00Z'}]),
        f'{base}/issues': FakeResponse(200, [
            gh_item(9, '2026-09-01T00:00:00Z', 'OWNER', 'alice'),
            gh_item(8, '2026-08-01T00:00:00Z', pr=True, closed='2026-08-03T00:00:00Z'),
            gh_item(7, '2026-07-01T00:00:00Z'),
            gh_item(1, '2024-01-01T00:00:00Z')]),
        f'{base}/community/profile': FakeResponse(200, {'files': {'readme': {'url': 'x'}, 'contributing': None,
                                                                  'code_of_conduct': None}}),
    }
    routes.update(overrides)
    return routes


class GithubFetchTests(unittest.TestCase):
    def fetch(self, routes):
        api, session, _ = client(routes)
        return hs.fetch_github_repo(api, 'Old-Org', 'Repo', WINDOW), session

    def test_measures_a_public_repository(self):
        result, _ = self.fetch(github_routes())
        record = result['record']
        self.assertEqual(record['id'], 'New-Org/Repo')
        self.assertEqual(record['renamed_from'], 'Old-Org/Repo')
        self.assertEqual(record['last_change_at'], '2026-08-02')
        self.assertEqual((record['contributors_total'], record['contributors_active'], record['absence_factor']), (3, 2, 2))
        self.assertEqual((record['releases_in_window'], record['releases_total'], record['latest_release_at']),
                         (1, 2, '2026-06-03'))
        self.assertEqual((record['forks'], record['stars']), (3, 7))
        self.assertEqual(record['license'], [{'status': 'detected', 'spdx': 'MIT', 'raw': 'MIT'}])
        self.assertEqual(record['files'], {'readme': True, 'contributing': False, 'code_of_conduct': False})
        self.assertEqual((record['outside_items'], record['outside_change_requests']), (2, 1))
        self.assertEqual(len(result['outside_prs']), 1)
        self.assertEqual(result['response_items'], [])

    def test_never_puts_identities_in_the_record(self):
        result, _ = self.fetch(github_routes())
        text = json.dumps(result['record'])
        for secret in ('alice', 'bob', 'carol', '@'):
            self.assertNotIn(secret, text.lower())

    def test_refuses_private_repositories(self):
        routes = github_routes(**{f'{GH}/Old-Org/Repo': FakeResponse(200, {'full_name': 'Old-Org/Repo', 'private': True})})
        with self.assertRaises(hs.SourceError) as ctx:
            self.fetch(routes)
        self.assertEqual(ctx.exception.kind, 'unavailable')

    def test_forks_skip_the_community_profile(self):
        routes = github_routes()
        routes[f'{GH}/Old-Org/Repo'] = FakeResponse(200, {'full_name': 'Old-Org/Repo', 'private': False, 'fork': True,
                                                          'parent': {'full_name': 'Upstream/Repo'},
                                                          'default_branch': 'main'})
        base = f'{GH}/Old-Org/Repo'
        for suffix in ('commits', 'contributors', 'releases', 'issues', 'community/profile'):
            routes[f'{base}/{suffix}'] = routes.pop(f'{GH}/New-Org/Repo/{suffix}')
        result, session = self.fetch(routes)
        self.assertEqual(result['record']['fork_of'], 'Upstream/Repo')
        self.assertIsNone(result['record']['files'])
        self.assertNotIn(f'{base}/community/profile', [url for url, _ in session.calls])

    def test_last_change_falls_back_to_history_when_only_bots_committed_recently(self):
        def commits(url, params):
            if params.get('since'):
                return FakeResponse(200, [gh_commit('dependabot[bot]', '2026-09-01T00:00:00Z', user_type='Bot')])
            return FakeResponse(200, [gh_commit('renovate[bot]', '2026-09-01T00:00:00Z', user_type='Bot'),
                                      gh_commit('alice', '2022-01-19T00:00:00Z')])
        result, _ = self.fetch(github_routes(**{f'{GH}/New-Org/Repo/commits': commits}))
        self.assertEqual(result['record']['last_change_at'], '2022-01-19')
        self.assertEqual(result['record']['contributors_active'], 0)

    def test_reads_first_replies_once_there_are_enough_outside_items(self):
        base = f'{GH}/New-Org/Repo'
        items = [gh_item(n, f'2026-09-0{n}T00:00:00Z', comments=2) for n in range(1, 6)]
        routes = github_routes(**{f'{base}/issues': FakeResponse(200, items)})
        for n in range(1, 6):
            routes[f'{base}/issues/{n}/comments'] = FakeResponse(200, [
                {'user': {'login': 'visitor', 'type': 'User'}, 'created_at': f'2026-09-0{n}T01:00:00Z'},
                {'user': {'login': 'stale[bot]', 'type': 'Bot'}, 'created_at': f'2026-09-0{n}T02:00:00Z'},
                {'user': {'login': 'alice', 'type': 'User'}, 'created_at': f'2026-09-0{n}T05:00:00Z'}])
        result, _ = self.fetch(routes)
        replies = [(i['first_reply_at'] - i['created_at']).total_seconds() / 3600 for i in result['response_items']]
        self.assertEqual(replies, [5.0] * 5)

    def test_an_empty_repository_is_a_named_gap(self):
        routes = github_routes(**{f'{GH}/New-Org/Repo/commits': FakeResponse(409, {})})
        result, _ = self.fetch(routes)
        self.assertIn({'metric': 'last_change', 'reason': 'empty_repository'}, result['record']['gaps'])
        self.assertIsNone(result['record']['last_change_at'])


def hf_routes(**overrides):
    routes = {
        f'{HF}/datasets/Old/ds': FakeResponse(200, {
            'id': 'New/ds', 'private': False, 'gated': False, 'disabled': False, 'downloads': 64,
            'downloadsAllTime': 2155, 'likes': 3, 'lastModified': '2026-07-30T12:00:00.000Z',
            'createdAt': '2023-05-17T00:00:00.000Z', 'cardData': {'license': 'cc-by-sa-4.0'}}),
        f'{HF}/datasets/New/ds/commits/main': FakeResponse(200, [
            {'date': '2026-07-30T12:00:00Z', 'authors': [{'user': 'alice'}]},
            {'date': '2026-01-01T12:00:00Z', 'authors': [{'user': 'parquet-converter'}]},
            {'date': '2024-01-01T12:00:00Z', 'authors': [{'user': 'alice'}, {'user': 'bob'}]}]),
        f'{HF}/datasets/New/ds/discussions': FakeResponse(200, {'count': 2, 'numClosedDiscussions': 1}),
    }
    routes.update(overrides)
    return routes


class HuggingFaceFetchTests(unittest.TestCase):
    def test_measures_a_dataset(self):
        api, _, _ = client(hf_routes())
        record = hs.fetch_hf_asset(api, 'datasets', 'Old/ds', WINDOW)['record']
        self.assertEqual((record['id'], record['renamed_from']), ('New/ds', 'Old/ds'))
        self.assertEqual((record['downloads_30d'], record['downloads_all_time'], record['likes']), (64, 2155, 3))
        self.assertEqual(record['last_change_at'], '2026-07-30')
        self.assertEqual((record['contributors_total'], record['contributors_active'], record['absence_factor']), (2, 1, 1))
        self.assertEqual(record['license'][0]['spdx'], 'CC-BY-SA-4.0')
        self.assertEqual(record['discussions'], {'total': 2, 'closed': 1})
        self.assertNotIn('alice', json.dumps(record))

    def test_gated_commit_history_is_a_named_gap(self):
        routes = hf_routes(**{f'{HF}/datasets/New/ds/commits/main': FakeResponse(401, {})})
        routes[f'{HF}/datasets/Old/ds']._body['gated'] = 'auto'
        api, _, _ = client(routes)
        record = hs.fetch_hf_asset(api, 'datasets', 'Old/ds', WINDOW)['record']
        self.assertIn({'metric': 'contributors', 'reason': 'gated'}, record['gaps'])
        self.assertIsNone(record['contributors_total'])

    def test_refuses_private_repositories(self):
        routes = hf_routes()
        routes[f'{HF}/datasets/Old/ds']._body['private'] = True
        api, _, _ = client(routes)
        with self.assertRaises(hs.SourceError) as ctx:
            hs.fetch_hf_asset(api, 'datasets', 'Old/ds', WINDOW)
        self.assertEqual(ctx.exception.kind, 'unavailable')


class ZenodoFetchTests(unittest.TestCase):
    def test_measures_a_record_and_its_versions(self):
        routes = {
            f'{ZEN}/111': FakeResponse(200, {
                'id': 111, 'conceptrecid': '100', 'stats': {'downloads': 387, 'views': 2358},
                'metadata': {'license': {'id': 'cc-by-4.0'}, 'access_right': 'open', 'resource_type': {'type': 'dataset'},
                             'publication_date': '2025-01-01',
                             'relations': {'version': [{'is_last': False, 'count': 2, 'last_child': {'pid_value': '222'}}]}}}),
            f'{ZEN}/111/versions': FakeResponse(200, {'hits': {'total': 2, 'hits': [
                {'metadata': {'publication_date': '2025-01-01'}}, {'metadata': {'publication_date': '2026-07-29'}}]}}),
        }
        api, _, _ = client(routes)
        result = hs.fetch_zenodo_record(api, '111', WINDOW)
        record = result['record']
        self.assertEqual((record['concept_id'], record['linked_is_latest'], record['latest_id']), ('100', False, '222'))
        self.assertEqual((record['versions_total'], record['versions_in_window'], record['last_change_at']), (2, 1, '2026-07-29'))
        self.assertEqual((record['downloads_all_time'], record['views_all_time']), (387, 2358))
        self.assertEqual(record['license'][0]['spdx'], 'CC-BY-4.0')
        self.assertIsNone(result['people'])


    def test_falls_back_to_the_record_when_the_versions_listing_is_missing(self):
        routes = {
            f'{ZEN}/333': FakeResponse(200, {
                'id': 333, 'conceptrecid': '300', 'stats': {'downloads': 5, 'views': 9},
                'metadata': {'license': {'id': 'cc0-1.0'}, 'publication_date': '2024-05-01',
                             'relations': {'version': [{'is_last': True, 'count': 1}]}}}),
        }
        api, _, _ = client(routes)
        record = hs.fetch_zenodo_record(api, '333', WINDOW)['record']
        self.assertEqual((record['versions_total'], record['versions_in_window'], record['last_change_at']),
                         (1, 0, '2024-05-01'))
        self.assertEqual(record['license'][0]['spdx'], 'CC0-1.0')


class DoiTests(unittest.TestCase):
    def test_resolves_a_hugging_face_doi_to_its_repository(self):
        routes = {'https://doi.org/api/handles/10.57967/hf/6491': FakeResponse(200, {'values': [
            {'type': 'HS_ADMIN', 'data': {}}, {'type': 'URL', 'data': {'value': 'https://huggingface.co/datasets/ksan26/EDADES'}}]})}
        api, _, _ = client(routes)
        info = hs.resolve_doi(api, '10.57967/hf/6491')
        self.assertEqual((info['platform'], info['kind'], info['id'], info['url']),
                         ('huggingface', 'datasets', 'ksan26/EDADES', 'https://huggingface.co/datasets/ksan26/EDADES'))


if __name__ == '__main__':
    unittest.main()
