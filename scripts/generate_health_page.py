"""Write the CHAOSS methodology page: public/chaoss/index.html.

The detail panel's "CHAOSS metrics" block and the Insights view link here. The page names
CHAOSS, says which CHAOSS metric each row follows and links its definition, and states the
thresholds, coverage and limits of the measurement. Thresholds come from chaoss_metrics.py and coverage
counts from catalog.json, so the page cannot state a rule or a number the collector does not apply;
it depends on nothing else, so re-running it without data changes writes the same bytes. The weekly
health.json figures never appear here.

Vite copies the page into docs/ with the rest of public/; build.py runs this before the Vite build.

Usage:
    python scripts/generate_health_page.py
"""
import argparse
import json
import os
import re
from string import Template

import chaoss_metrics as cm
from health_assets import MEASURED_PLATFORMS, OPEN_HOSTS, discover_assets, host_counts
from static_page import STATIC_PAGE_CSS
from utils import ANALYTICS, CSP, FONT_HREF, QUALITY_SCORE_MAX, SITE_BASE

CATALOG_PATH = os.path.join('public', 'data', 'catalog.json')
OUTPUT_PATH = os.path.join('public', 'chaoss', 'index.html')
WORKFLOW_PATH = os.path.join('.github', 'workflows', 'health_check.yml')
RANKING_PATH = os.path.join('src', 'utils', 'ranking.js')
PAGE_PATH = 'chaoss/'

PRACTITIONER_GUIDE_URL = 'https://chaoss.community/practitioner-guide-introduction/'
CONTACT_EMAIL = 'jonas.nothnagel@gmail.com'  # the catalogue's public contact (src/components/Footer.jsx)
RANKING_CONSTANTS = ('ACTIVITY_WEIGHT', 'UNAVAILABLE_PENALTY')

# How the coverage line names the open hosts not measured yet; organisation pages are grouped.
UNMEASURED_HOST_NAMES = {'kaggle': 'Kaggle', 'dataverse': 'Harvard Dataverse', 'figshare': 'figshare',
                         'gitlab': 'GitLab', 'doi_other': 'records behind other DOIs'}
ORG_PAGE_HOSTS = {'huggingface_org': 'Hugging Face', 'github_org': 'GitHub'}

# What each panel row counts, naming the platform where it is not every one; {absence_pct} comes
# from the code.
METRIC_TEXT = {
    'last_change': 'Latest commit by a person (GitHub), update (Hugging Face) or version (Zenodo).',
    'releases': 'GitHub releases and Zenodo versions: last 12 months, total, latest.',
    'contributors': 'People with commits on GitHub or Hugging Face, all time and in the last 12 months.',
    'absence_factor': 'Fewest people who made at least {absence_pct}% of all commits.',
    'forks': 'GitHub forks.',
    'popularity': 'GitHub stars, Hugging Face likes, views on Zenodo.',
    'downloads': 'Hugging Face and Zenodo downloads, as each platform counts them.',
    'license': "Licence declared at the source; it can differ from the catalogue's.",
    'first_response': 'Median time to a first reply on outside GitHub issues and pull requests from the last 12 months.',
    'change_request_closure': 'Outside pull requests from the last 12 months that are now closed.',
}

PAGE_CSS = """  .metrics td:first-child { font-family: var(--sans); font-size: .8125rem; font-weight: 600; white-space: nowrap; }
  .metrics td { font-size: .8125rem; }
  ul.points { margin: 0; padding-left: 1.15rem; max-width: var(--measure); }
  ul.points li { color: var(--ink-2); margin: 0 0 .45rem; }
  ul.points li:last-child { margin-bottom: 0; }
"""

PAGE = Template("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<meta name="description" content="How the FAIR Forward catalog measures the CHAOSS metrics shown for each project: definitions, thresholds, coverage and limits.">
<meta http-equiv="Content-Security-Policy" content="$csp">
$analytics
<link rel="canonical" href="${base}${page_path}">
<title>Community Health (CHAOSS metrics) - FAIR Forward Data Catalog</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="$font_href" rel="stylesheet">
<style>
$style$page_style</style>
</head>
<body>
<div class="masthead"><div class="masthead-in">
  <a href="../" aria-label="FAIR Forward catalog home"><img src="../img/ff_official.png" alt="FAIR Forward"></a>
  <a class="back" href="../">Back to the catalog</a>
</div></div>

<main class="wrap"><div class="stack">

  <header class="prose">
    <h1>Community Health (CHAOSS metrics)</h1>
    <p class="standfirst">Each project's panel shows CHAOSS metrics for its repositories, models and records on
    GitHub, Hugging Face and Zenodo, measured from public data. The definitions come from
    <a href="$chaoss_home">CHAOSS</a>, the Linux Foundation's Community Health Analytics in Open Source Software
    project, which does not review or endorse this catalogue.</p>
  </header>

  <section>
    <h2>Metrics</h2>
    <div class="scroll"><table class="metrics">
      <thead><tr><th>In the panel</th><th>CHAOSS metric</th><th>Counted</th></tr></thead>
      <tbody>
$metric_rows
      </tbody>
    </table></div>
    <p class="prose">Metrics without enough data are listed as not measurable, never as 0.</p>
  </section>

  <hr>

  <section>
    <h2>Rules</h2>
    <ul class="points">
      <li>"Last 12 months" means the $window_days days up to the day of measurement.</li>
      <li>Response time needs at least $min_items outside issues and pull requests, pull request closure at
      least $min_prs outside pull requests. Outside: anyone but the owner, organisation members and
      collaborators.</li>
      <li>Bots are left out of people counts, response times, pull request closure and the last change
      on GitHub (<a href="$bot_url">Bot Activity</a>).</li>
      <li>Measured $schedule_text. If a source cannot be read, a project can keep its previous measurement
      for up to $carry_days days.</li>
    </ul>
  </section>

  <hr>

  <section>
    <h2>Coverage</h2>
    <p class="prose">$coverage_sentence Not counted: private or gated content, non-default branches, work
    outside repositories.</p>
  </section>

  <hr>

  <section>
    <h2>Use in the catalogue</h2>
    <p class="prose">The default order adds up to $activity_weight points for recent changes, stars and
    downloads to a documentation score of up to $quality_max; a project whose links all failed at the last
    check loses $unavailable_penalty points. Insights compares SDGs, not projects, as
    <a href="$guide_url">CHAOSS advises</a>, and shows figures only for an SDG with at least
    $min_group measured projects.</p>
  </section>

  <hr>

  <section>
    <h2>Privacy and corrections</h2>
    <p class="prose">Only counts and dates are published, never contributors' names, usernames or email
    addresses; private repositories are skipped. To correct a value or leave a project out,
    <a href="https://github.com/Fair-Forward/datasets/issues/new">open an issue</a> or write to
    <a href="mailto:$contact">$contact</a>.</p>
  </section>

  <hr>

  <footer>
    <p>Fair Forward, Artificial Intelligence for All. A project by GIZ.
    <a href="${base}api/">API</a>. <a href="${base}privacy/">Privacy</a>.</p>
  </footer>

</div></main>
</body>
</html>
""")


def coverage(catalog):
    """How many projects link a measurable asset, the distinct assets per platform, and for projects
    that link only open hosts we do not measure, how many link each of those hosts."""
    projects = [p for p in catalog.get('projects', []) if p.get('id')]
    keys = {'github': set(), 'huggingface': set(), 'zenodo': set()}
    other_hosts = {}
    measurable = other_open = 0
    for project in projects:
        assets = discover_assets(project)
        for asset in assets:
            keys[asset['platform']].add(asset['key'])
        if assets:
            measurable += 1
            continue
        hosts = [host for host in host_counts(project) if host in OPEN_HOSTS]
        if hosts:
            other_open += 1
            for host in hosts:
                other_hosts[host] = other_hosts.get(host, 0) + 1
    return {'projects': len(projects), 'measurable': measurable, 'github': len(keys['github']),
            'huggingface': len(keys['huggingface']), 'zenodo': len(keys['zenodo']), 'other_open': other_open,
            'other_hosts': other_hosts}


def ranking_weights(ranking_text):
    """The activity boost and availability penalty the catalogue's default order applies, read from
    ranking.js, so the page states the weights the site sorts by."""
    weights = {}
    for name in RANKING_CONSTANTS:
        match = re.search(rf'export const {name} = (\d+)\b', ranking_text)
        if not match:
            raise ValueError(f'{RANKING_PATH} no longer sets {name} to a whole number; '
                             f'update ranking_weights and the page together')
        weights[name] = int(match.group(1))
    return weights


def check_schedule(workflow_text):
    """The page states SCHEDULE_TEXT; refuse to publish it when the workflow runs on any other cron."""
    crons = [cron.strip() for cron in re.findall(r"cron:\s*['\"]([^'\"]+)['\"]", workflow_text)]
    found = crons[0] if len(crons) == 1 else (crons or None)
    if found != cm.SCHEDULE:
        raise ValueError(f'{WORKFLOW_PATH} runs on {found!r}, but the page states "{cm.SCHEDULE_TEXT}" '
                         f'({cm.SCHEDULE}); update chaoss_metrics.SCHEDULE and SCHEDULE_TEXT together')


def _count(n, one, many):
    return f'{n:,} {one if n == 1 else many}'


def _join(items, word):
    return items[0] if len(items) == 1 else f"{', '.join(items[:-1])} {word} {items[-1]}"


def _metric_rows():
    rows = []
    for metric in cm.CHAOSS_METRICS:
        counted = METRIC_TEXT[metric['key']].replace('{absence_pct}', str(round(cm.ABSENCE_SHARE * 100)))
        rows.append(f'        <tr><td>{metric["label"]}</td>'
                    f'<td><a href="{metric["url"]}">{metric["chaoss"]}</a></td>'
                    f'<td class="note">{counted}</td></tr>')
    return '\n'.join(rows)


def _coverage_sentence(counts):
    return (f"{counts['measurable']} of {counts['projects']} projects link measured assets in their dataset "
            f"or use-case links: "
            f"{_count(counts['github'], 'GitHub repository', 'GitHub repositories')}, "
            f"{_count(counts['huggingface'], 'Hugging Face model, dataset or space', 'Hugging Face models, datasets or spaces')} "
            f"and {_count(counts['zenodo'], 'Zenodo record', 'Zenodo records')}."
            f"{_unmeasured_sentence(counts)}")


def _unmeasured_sentence(counts):
    """Names the hosts behind the projects that cannot be measured yet, most linked first."""
    if not counts['other_open']:
        return ''
    hosts = sorted(counts['other_hosts'].items(), key=lambda item: (-item[1], item[0]))
    names = [UNMEASURED_HOST_NAMES[host] for host, _ in hosts if host in UNMEASURED_HOST_NAMES]
    orgs = [ORG_PAGE_HOSTS[host] for host, _ in hosts if host in ORG_PAGE_HOSTS]
    if orgs:
        names.append(f"organisation pages on {_join(orgs, 'or')}")
    return (f" {_count(counts['other_open'], 'more project links', 'more projects link')} only to pages not "
            f"measured yet: {_join(names, 'and')}.")


def render_page(catalog, workflow_text, ranking_text):
    check_schedule(workflow_text)
    weights = ranking_weights(ranking_text)
    return PAGE.substitute(
        style=STATIC_PAGE_CSS,
        page_style=PAGE_CSS,
        base=SITE_BASE,
        page_path=PAGE_PATH,
        csp=CSP,
        analytics=ANALYTICS,
        font_href=FONT_HREF,
        chaoss_home=cm.CHAOSS_HOME,
        bot_url=cm.BOT_ACTIVITY_URL,
        guide_url=PRACTITIONER_GUIDE_URL,
        metric_rows=_metric_rows(),
        coverage_sentence=_coverage_sentence(coverage(catalog)),
        window_days=cm.WINDOW_DAYS,
        min_items=cm.MIN_OUTSIDE_ITEMS,
        min_prs=cm.MIN_OUTSIDE_CHANGE_REQUESTS,
        min_group=cm.MIN_GROUP,
        quality_max=QUALITY_SCORE_MAX,
        activity_weight=weights['ACTIVITY_WEIGHT'],
        unavailable_penalty=weights['UNAVAILABLE_PENALTY'],
        schedule_text=cm.SCHEDULE_TEXT,
        carry_days=cm.CARRY_FORWARD_MAX_DAYS,
        contact=CONTACT_EMAIL,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description='Write the CHAOSS methodology page.')
    parser.add_argument('--catalog', default=CATALOG_PATH)
    parser.add_argument('--output', default=OUTPUT_PATH)
    parser.add_argument('--workflow', default=WORKFLOW_PATH)
    parser.add_argument('--ranking', default=RANKING_PATH)
    args = parser.parse_args(argv)
    with open(args.catalog, encoding='utf-8') as f:
        catalog = json.load(f)
    with open(args.workflow, encoding='utf-8') as f:
        workflow_text = f.read()
    with open(args.ranking, encoding='utf-8') as f:
        ranking_text = f.read()
    page = render_page(catalog, workflow_text, ranking_text)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w', encoding='utf-8') as f:
        f.write(page)
    print(f'Wrote {args.output}')


if __name__ == '__main__':
    main()
