# Ecosystem: related catalogs and sourcing lists

The Fair Forward catalog covers projects our programme funded. Others are building repositories
that cover AI for development more broadly, and several of them already list some of the same
projects we do. The world does not need the same catalog a dozen times over.

This file is the inventory that comes before any exchange: every repository and source we know
of, what it holds, and whether it can be read by a machine. That last field is the one that
matters for consolidation. A source with an API or a file in a public repo can be synced; a source
that only renders in a browser has to be handled some other way.

Two sections, because two different things are listed here. **Catalogs and repositories** are
possible sync partners. **Sourcing lists and portfolios** are not catalogs at all; they are lists
of organisations from which use cases can be found, useful for filling gaps rather than for
mirroring.

To add a source, see [Adding a source](#adding-a-source) at the bottom.

Last verified: 2026-07-29. Every URL below was checked on that date.

---

## Catalogs and repositories

| Source | Holds | Geography | Machine access |
|---|---|---|---|
| [FAIR Forward Data Catalog](#fair-forward-data-catalog) | datasets, use cases | Global Majority | static JSON API |
| [Lacuna Fund catalog](#lacuna-fund-catalog) | datasets, use cases | Global Majority | Excel in public repo |
| [Lacuna Fund sector pages](#lacuna-fund-sector-pages) | datasets | Global Majority | none found |
| [DPGA registry](#digital-public-goods-alliance-registry) | AI systems, data, software, content | global | JSON in public repo |
| [Global Center on AI Governance, AI Use Cases](#global-center-on-ai-governance-ai-use-cases) | use cases | Africa | none found |
| [Open Data Africa, datasets](#open-data-africa-datasets) | datasets | Africa | CSV in public repo |
| [Open Data Africa, Use Case Explorer](#open-data-africa-use-case-explorer) | use cases | Africa | CSV in public repo |
| [African AI Atlas, Lanfrica Labs](#african-ai-atlas-lanfrica-labs) | datasets, models, papers, tools | Africa | none found |
| [AI Impact Commons](#ai-impact-commons) | impact stories | global | none found |
| [Mozilla Data Collective](#mozilla-data-collective) | datasets | global | none found |
| [Source Cooperative](#source-cooperative) | datasets | global | data proxy, no catalog API |
| [World Bank AI Repository](#world-bank-ai-repository) | use cases | global | none found |
| [The Social Good Hub](#the-social-good-hub) | use cases | global, Africa-weighted | none found |
| [Upcoming](#upcoming) | announced, nothing public yet | Africa, global | not yet applicable |

### FAIR Forward Data Catalog

- **URL:** https://fair-forward.github.io/datasets/
- **Holds:** datasets and use cases, one record per project
- **Geography:** Global Majority countries, mainly the seven FAIR Forward partner countries
- **Openness:** all open source, curated
- **Machine access:** static JSON API at https://fair-forward.github.io/datasets/api/v1/, no key, no rate limit, content-hash versioned
- **Operator / funders:** GIZ FAIR Forward, funded by BMZ and the Gates Foundation

Ours. The API is the surface other catalogs mirror from, and the reason we can ask others for the
same. See the API section in [README.md](README.md).

### Lacuna Fund catalog

- **URL:** https://www.dsfsi.co.za/lacunafund-datasets/
- **Holds:** roughly 70 datasets and use cases, with more in the pipeline
- **Geography:** Africa, Asia, South America
- **Openness:** almost all open
- **Machine access:** `docs/data_catalog.xlsx` in https://github.com/dsfsi/lacunafund-datasets
- **Operator / funders:** DSFSI, MERID and FAIR Forward; Lacuna Fund is funded by google.org, IDRC, Rockefeller Foundation, BMZ and Wellcome Trust

Built on the same pipeline as this repository, which makes it the easiest sync target of the set:
the schemas are close relatives rather than strangers.

### Lacuna Fund sector pages

- **URL:** https://lacunafund.org/datasets/
- **Holds:** dataset descriptions grouped by sector (language, agriculture, health, climate)
- **Geography:** Global Majority
- **Openness:** open
- **Machine access:** none found
- **Operator / funders:** Lacuna Fund

The older descriptions on the Lacuna Fund website itself. Kept separate from the catalog above
because it is a different surface with different coverage, not a copy.

### Digital Public Goods Alliance registry

- **URL:** https://www.digitalpublicgoods.net/registry
- **Holds:** verified digital public goods across four categories, of which Open AI System is the
  relevant one
- **Geography:** global
- **Openness:** open by definition; entries must meet the DPG Standard, and AI systems must have
  open training data
- **Machine access:** one JSON file per entry in https://github.com/DPGAlliance/publicgoods-candidates
  (`digitalpublicgoods/` for verified DPGs, `nominees/` for candidates), with a published schema
- **Operator / funders:** Digital Public Goods Alliance, UN-endorsed

Systems only, not datasets, and a high bar to clear. Narrow but the best-structured registry here:
a documented schema and a review process behind every record.

### Global Center on AI Governance, AI Use Cases

- **URL:** https://www.globalcenter.ai/aorai/use-cases
- **Holds:** use cases of responsible African AI innovation
- **Geography:** Africa
- **Openness:** mixed; open source is not a criterion
- **Machine access:** none found
- **Operator / funders:** Global Center on AI Governance, under the African Observatory on
  Responsible AI

Curated around responsibility rather than openness, which makes it a complement to our catalog
rather than an overlap.

### Open Data Africa, datasets

- **URL:** https://open-data-africa.github.io/datasets.html
- **Holds:** open datasets across agriculture, health, language and climate
- **Geography:** Africa
- **Openness:** mostly open, majority Creative Commons
- **Machine access:** `datasets/catalog.csv` in https://github.com/open-data-africa/open-data-africa.github.io, plus an Excel mirror
- **Operator / funders:** GIZ

Built by GIZ Africa to measure the maturity of the open-source AI landscape. All Fair Forward
datasets are already included, and `scripts/export_to_open_data_africa.py` in this repository is
what puts them there.

### Open Data Africa, Use Case Explorer

- **URL:** https://open-data-africa.github.io/use-cases.html
- **Holds:** use cases showing how the datasets are applied
- **Geography:** Africa
- **Openness:** mostly open
- **Machine access:** same repository and CSV as above
- **Operator / funders:** GIZ

The use-case half of the same platform. All Fair Forward use cases are included.

### African AI Atlas, Lanfrica Labs

- **URL:** https://lanfrica.com/en/atlas
- **Holds:** datasets, models, papers, policies and tools, connected to each other
- **Geography:** Africa
- **Openness:** mixed, leaning open; originally focused on NLP
- **Machine access:** none found; documentation at https://docs.lanfrica.com/
- **Operator / funders:** Lanfrica Labs, non-profit

Filter the Atlas to tools and applications for the use-case view. The connections between
resources are the distinctive part: a dataset links to the models and papers built on it.

### AI Impact Commons

- **URL:** https://www.aiimpactcommons.global/
- **Holds:** 80+ impact stories across 30+ countries and five sectors
- **Geography:** global, with a stated Global South emphasis
- **Openness:** mixed; documented outcomes matter more than open licences
- **Machine access:** none found
- **Operator / funders:** working group of the India AI Impact Summit 2026, chaired by India, the
  Netherlands and Indonesia, with philanthropies and foundations submitting entries

Organised around evidence of impact rather than around the asset, so its records answer a
different question than ours do. Impact stories are at `/impact-stories`.

### Mozilla Data Collective

- **URL:** https://mozilladatacollective.com/datasets
- **Holds:** 600+ curated datasets from 190+ organisations, across 300+ languages
- **Geography:** global, strong low-resource language coverage
- **Openness:** open, shared on terms set by each data community
- **Machine access:** none found
- **Operator / funders:** Mozilla Data Collective, a mission-locked company incubated by the Mozilla
  Foundation

Where several of the foundational open language datasets now live, including Common Voice. Closest
in spirit to the data-foundation half of our catalog.

### Source Cooperative

- **URL:** https://source.coop/
- **Holds:** data products, mainly geospatial
- **Geography:** global
- **Openness:** mainly open
- **Machine access:** no documented catalog API; data is served through a proxy at
  https://data.source.coop/ and the platform is open source at https://github.com/source-cooperative
- **Operator / funders:** Source Cooperative (Radiant Earth)

A hosting platform as much as a catalog: publishers put the data itself there, not just a link to
it. Relevant if we ever need somewhere to host assets rather than point at them.

### World Bank AI Repository

- **URL:** https://airepository.worldbank.org/
- **Holds:** 100+ real-world AI use cases from 65+ countries
- **Geography:** global
- **Openness:** mixed; implemented or actively piloted, open source is not a criterion
- **Machine access:** none found; the site blocks automated requests
- **Operator / funders:** World Bank Group with other multilateral development banks

Cross-sectoral and aimed at replication by governments. Individual records sit under `/use-case/`.

### The Social Good Hub

- **URL:** https://www.thesocialgoodhub.ai/
- **Holds:** AI use cases from organisations working on social impact; in beta, targeting 400+ use
  cases from 400+ organisations, with a stable release stated for October 2026
- **Geography:** global, with nearly half of appearances in Sub-Saharan Africa
- **Openness:** mixed; around 40 entries are marked ready for reuse with open code
- **Machine access:** none found
- **Operator / funders:** IDinsight, supported by google.org

Deliberately excludes internal productivity tools and enabler projects such as training datasets
and AI literacy work, so its scope is narrower than ours by design. Its own sourcing note is where
most of the next section comes from.

### Upcoming

- **Funders collaborative synchronisation of repositories.** Announced, no public surface yet.
  This is the effort the rest of this file is preparation for.
- **African Union repository of African AI innovations.** Reported as planned, no public surface
  yet.

---

## Sourcing lists and portfolios

Not catalogs. Lists of organisations that can be mined for use cases, useful when a gap needs
filling. Most of these come from the Social Good Hub's own sourcing note, shared with us.

- **AWS IMAGINE Grant winners, 2024 and 2025.**
  https://aws.amazon.com/blogs/publicsector/announcing-the-2024-2025-aws-imagine-grant-winners/
- **data.org, AI to Accelerate Inclusion Challenge.**
  https://data.org/our-work/challenges/artificial-intelligence-to-accelerate-inclusion-challenge/
- **data.org, Activate AI Economic Opportunity Challenge.**
  https://data.org/our-work/challenges/activate-ai-economic-opportunity-challenge/
- **Patrick J. McGovern Foundation portfolio.**
  https://learn.mcgovern.org/18e70021ed8c8027ba0fc4032bc0c33e?v=18e70021ed8c80318234000c85e4dce8
- **ITU AI for Good innovations.** https://www.itu.int/hub/publication/t-ai4g-ai4good-2025-1/
- **FastForward accelerator directory,** filtered to the AI/ML tag.
  https://www.ffwd.org/directory?tech=AI%3BML&page=1 The broadest of these lists and the least
  filtered; entries need checking for a genuine AI deployment.
- **Community Health Worker AI Solutions Database,** compiled by Nate Miller. Organisations
  working with frontline health workers in low- and middle-income countries.
  https://nate-miller.beehiiv.com/p/updated-mapping-of-ai-in-chw-programs-6e1f
- **Funder portfolios.** google.org, the Gates Foundation and The Agency Fund each hold portfolios
  of AI-linked grantees that are shared privately and have no public listing. Reachable only by
  asking the funder.

---

## Adding a source

New catalogs and repositories go in the first section, with a row in the summary table and a block
below it. The block is a bulleted list of the same six fields, in the same order, followed by a
note of one or two lines saying what the source is and how it relates to our catalog:

```markdown
### Name

- **URL:**
- **Holds:**
- **Geography:**
- **Openness:**
- **Machine access:**
- **Operator / funders:**

Note.
```

The fields are a list rather than plain lines because GitHub renders single newlines inside a
paragraph as spaces, which would run the six fields together. Lists of organisations rather than
of projects go in the second section as a single bullet.

Two rules worth keeping. A URL goes in only after it has been opened and confirmed to be the right
page; if it cannot be confirmed, write `URL to confirm` rather than a guess. And **Machine access**
records only what was actually found, not what a site of that kind usually has, because that field
is what any future sync will be planned against. Update the "Last verified" date at the top when
you re-check the list.
