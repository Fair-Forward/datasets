"""Write the CHAOSS methodology page: public/chaoss/index.html.

The detail panel's "CHAOSS metrics" block and the Insights view link here. The page names
CHAOSS, says which CHAOSS metric each row follows and links its definition, and states the
thresholds and blind spots of the measurement. Thresholds come from chaoss_metrics.py and coverage
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
SUNSET_GUIDE_URL = 'https://chaoss.community/practitioner-guide-sunset/'
CONTACT_EMAIL = 'jonas.nothnagel@gmail.com'  # the catalogue's public contact (src/components/Footer.jsx)
RANKING_CONSTANTS = ('ACTIVITY_WEIGHT', 'UNAVAILABLE_PENALTY')

# How the coverage line names the open hosts we do not measure yet; organisation pages are grouped.
UNMEASURED_HOST_NAMES = {'kaggle': 'Kaggle', 'dataverse': 'Harvard Dataverse', 'figshare': 'figshare',
                         'gitlab': 'GitLab', 'doi_other': 'records behind other DOIs'}
ORG_PAGE_HOSTS = {'huggingface_org': 'Hugging Face', 'github_org': 'GitHub'}

# What each panel row counts, and where it comes from, in the page's words.
WHAT_WE_COUNT = {
    'last_change': ('The date of the latest commit by a person on the default branch, the last update of a '
                    'Hugging Face model, dataset or space, and the latest version of a Zenodo record. '
                    'Dates only, no times.', 'GitHub, Hugging Face, Zenodo'),
    'releases': ('Releases on GitHub (drafts left out) and versions of a Zenodo record: how many in the last '
                 '12 months, in total, and the latest.', 'GitHub, Zenodo'),
    'contributors': ("People with commits, over all time and in the last 12 months. One person counts once "
                     "across a project's repositories on the same platform; platforms are never added "
                     "together.", 'GitHub, Hugging Face'),
    'absence_factor': ('The smallest number of people who made half of all commits.', 'GitHub, Hugging Face'),
    'forks': ('Forks of the repository.', 'GitHub'),
    'popularity': ('Stars on GitHub, likes on Hugging Face, views of a Zenodo record across all its versions.',
                   'GitHub, Hugging Face, Zenodo'),
    'downloads': ('Downloads as each platform counts them: Hugging Face in the last 30 days and over all time, '
                  'Zenodo across all versions of a record. A download is not a person.', 'Hugging Face, Zenodo'),
    'license': ('The licence the source itself declares: GitHub\'s licence detection, the Hugging Face card, '
                'the Zenodo record. It can differ from the licence recorded in this catalogue.',
                'GitHub, Hugging Face, Zenodo'),
    'first_response': ('The median time until someone other than the author replied to an issue or pull '
                       'request from outside the project.', 'GitHub'),
    'change_request_closure': ('How many pull requests from outside the project, opened in the last 12 '
                               'months, have since been closed, merged or not.', 'GitHub'),
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
<meta name="description" content="How the FAIR Forward catalog applies the metrics of CHAOSS, the Linux Foundation's Community Health Analytics in Open Source Software project, to the projects it lists.">
<meta http-equiv="Content-Security-Policy" content="$csp">
$analytics
<link rel="canonical" href="${base}${page_path}">
<title>How we apply the CHAOSS metrics - FAIR Forward Data Catalog</title>
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
    <h1>How we apply the CHAOSS metrics</h1>
    <p class="standfirst">Where a project's datasets, models or code live on GitHub, Hugging Face or Zenodo, we
    read their public activity once a week and report it with the metrics of CHAOSS, the Linux Foundation's
    Community Health Analytics in Open Source Software project. We report facts, not scores.</p>
  </header>

  <section>
    <h2>What CHAOSS is</h2>
    <div class="prose">
      <p><a href="$chaoss_home">CHAOSS</a> (Community Health Analytics in Open Source Software) is a Linux
      Foundation project that defines how to measure the health of open-source communities. We use its metric
      definitions, not its software, and adapt them where a catalogue of datasets and models needs it.
      CHAOSS does not review or endorse this catalogue.</p>
    </div>
  </section>

  <hr>

  <section>
    <h2>What we measure</h2>
    <p class="prose">Each project's panel shows these rows. A row without enough data is named under
    "Not measurable" instead of showing a zero.</p>
    <div class="scroll"><table class="metrics">
      <thead><tr><th>In the panel</th><th>CHAOSS metric</th><th>What we count</th><th>Where</th></tr></thead>
      <tbody>
$metric_rows
      </tbody>
    </table></div>
    <p class="prose">$starter_sentence the CHAOSS <a href="$starter_url">Starter Project Health</a> model.</p>
  </section>

  <hr>

  <section>
    <h2>Which links we read</h2>
    <p class="prose">We read each project's dataset links and its use-case, model and app links; additional
    resources and hosted documents are not measured. Every GitHub repository, Hugging Face model, dataset or
    space and Zenodo record among them is measured, and a Zenodo or Hugging Face DOI is followed to the record
    it names.
    $coverage_sentence</p>
  </section>

  <hr>

  <section>
    <h2>Definitions and thresholds</h2>
    <ul class="points">
      <li>"In the last 12 months" means the $window_days days up to and including the day of measurement.</li>
      <li>The absence factor is the smallest number of people who made at least $absence_pct% of all commits,
      over the whole history.</li>
      <li>"Outside" means anyone GitHub does not list as the repository's owner, a member of its organisation
      or a collaborator.</li>
      <li>Accounts marked as bots, and automation accounts we know of, are left out of every count of people,
      of the issues and pull requests behind response time and closure, and of the last change on GitHub
      (CHAOSS <a href="$bot_url">Bot Activity</a>). Platform totals such as stars and downloads, and the last
      update of a Hugging Face model, dataset or space, include their activity.</li>
      <li>Response time needs at least $min_items outside issues and pull requests in the last 12 months, and
      pull request closure at least $min_prs outside pull requests, pooled across a project's repositories.
      An unanswered item counts its age as a lower bound, so a median can read "more than".</li>
      <li>A date after the day of measurement comes from a wrong clock: it never becomes the last change or
      the latest release, though such a release still counts in the total.</li>
      <li>The catalogue's status filter calls a project recently updated when something changed in the last
      $recent_days days, and shows no recent updates after $stale_days days (about $stale_months months)
      or when every repository is archived. Zenodo and Harvard Dataverse records count as a stable
      archive: frozen on purpose, and citable.</li>
    </ul>
  </section>

  <hr>

  <section>
    <h2>What we cannot see</h2>
    <ul class="points">
      <li>Work outside a repository: meetups, data collection, training, and the shared spreadsheet behind
      this catalogue.</li>
      <li>Private or gated content, and branches other than the default one.</li>
      <li>Co-authors named only in a commit message; one person with two accounts or addresses counts
      twice.</li>
      <li>Automation accounts we do not know about, and downloads by automated systems, which the platforms
      count like any other.</li>
      <li>Members of an organisation who keep their membership private appear as outside contributors.</li>
      <li>Which commits a fork made itself: its counts include its original repository's history, and the
      panel says so.</li>
      <li>Licences stated only in prose: licence detection is mechanical.</li>
      <li>Hosts we do not measure yet, such as GitLab, Kaggle, Harvard Dataverse and figshare.</li>
    </ul>
  </section>

  <hr>

  <section>
    <h2>How to read it</h2>
    <div class="prose">
      <p>These are facts, measured the same way for every project, not scores. CHAOSS advises to "avoid using metrics to compare projects against each other when
      possible" (<a href="$guide_url">practitioner guide</a>) and notes that "informational repositories might
      not have any releases at all" (<a href="$starter_url">Starter Project Health</a>).</p>
      <p>A dataset that no longer changes can be complete: a project "might seem to be abandoned when it has
      simply stabilized and might still be widely used" (<a href="$sunset_url">CHAOSS on sunsetting</a>). Many
      research repositories are kept by one person, and an absence factor of 1 describes that rather than
      judging it. "Not measurable" means there was not enough data, not that something is wrong.</p>
      <p>The Insights page compares SDGs, never projects, and prints upkeep figures only for a goal with
      at least $min_group measured projects.</p>
      <p>The catalogue's default order does use these facts. It sorts projects by how fully they are
      documented, a score of up to $quality_max points, and adds up to $activity_weight points for activity:
      how recently a project changed (a project with a Zenodo or Harvard Dataverse record gets a fixed value
      instead) and its GitHub stars or Hugging Face downloads in the last 30 days. A very active project can
      therefore come before a better-documented but quieter one. A project none of whose links responded at
      the last check loses $unavailable_penalty points, and a project without these facts gets no boost. The
      facts never decide whether a project is listed.</p>
    </div>
  </section>

  <hr>

  <section>
    <h2>Privacy</h2>
    <p class="prose">We read only public data through public APIs and publish counts and dates, never the names,
    usernames or email addresses of contributors. Account names are used during a run only to count each person once, and are
    not stored. Private repositories are skipped even when they could be read, and a fork's original repository
    is named only when an organisation owns it.</p>
  </section>

  <hr>

  <section>
    <h2>When it runs</h2>
    <p class="prose">The check runs $schedule_text. When a source cannot be read during a run, the project
    keeps its previous measurement for up to $carry_days days, as long as it covers the same links, and the
    panel shows the date it was taken. Otherwise the panel names what could not be read.</p>
  </section>

  <hr>

  <section>
    <h2>Corrections and opting out</h2>
    <p class="prose">If a number looks wrong, or you maintain a project and would rather it did not show these
    facts, <a href="https://github.com/Fair-Forward/datasets/issues/new">open an issue on GitHub</a> or write to
    <a href="mailto:$contact">$contact</a>. We will correct it or leave the project out; its links are still
    checked.</p>
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
        counted, where = WHAT_WE_COUNT[metric['key']]
        rows.append(f'        <tr><td>{metric["label"]}</td>'
                    f'<td><a href="{metric["url"]}">{metric["chaoss"]}</a></td>'
                    f'<td class="note">{counted}</td><td class="note">{where}</td></tr>')
    return '\n'.join(rows)


def _starter_sentence():
    labels = [m['label'].lower() for m in cm.CHAOSS_METRICS if m['starter']]
    listed = _join(labels, 'and')
    return f'{listed[0].upper()}{listed[1:]} {"together form" if len(labels) > 1 else "is part of"}'


def _coverage_sentence(counts):
    return (f"The catalogue currently has {counts['measurable']} of {counts['projects']} projects with such "
            f"links: {_count(counts['github'], 'GitHub repository', 'GitHub repositories')}, "
            f"{_count(counts['huggingface'], 'Hugging Face model, dataset or space', 'Hugging Face models, datasets or spaces')} "
            f"and {_count(counts['zenodo'], 'Zenodo record', 'Zenodo records')}."
            f"{_unmeasured_sentence(counts)}")


def _unmeasured_sentence(counts):
    """Names the hosts behind the projects we cannot measure, most linked first."""
    if not counts['other_open']:
        return ''
    hosts = sorted(counts['other_hosts'].items(), key=lambda item: (-item[1], item[0]))
    names = [UNMEASURED_HOST_NAMES[host] for host, _ in hosts if host in UNMEASURED_HOST_NAMES]
    orgs = [ORG_PAGE_HOSTS[host] for host, _ in hosts if host in ORG_PAGE_HOSTS]
    if orgs:
        names.append(f"organisation pages on {_join(orgs, 'or')}")
    return (f" {_count(counts['other_open'], 'more project links', 'more projects link')} only to pages we "
            f"do not measure yet: {_join(names, 'and')}.")


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
        starter_url=cm.STARTER_MODEL_URL,
        bot_url=cm.BOT_ACTIVITY_URL,
        guide_url=PRACTITIONER_GUIDE_URL,
        sunset_url=SUNSET_GUIDE_URL,
        metric_rows=_metric_rows(),
        starter_sentence=_starter_sentence(),
        coverage_sentence=_coverage_sentence(coverage(catalog)),
        window_days=cm.WINDOW_DAYS,
        absence_pct=round(cm.ABSENCE_SHARE * 100),
        min_items=cm.MIN_OUTSIDE_ITEMS,
        min_prs=cm.MIN_OUTSIDE_CHANGE_REQUESTS,
        min_group=cm.MIN_GROUP,
        quality_max=QUALITY_SCORE_MAX,
        activity_weight=weights['ACTIVITY_WEIGHT'],
        unavailable_penalty=weights['UNAVAILABLE_PENALTY'],
        recent_days=cm.RECENT_DAYS,
        stale_days=cm.STALE_DAYS,
        stale_months=round(cm.STALE_DAYS / 30.44),
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
