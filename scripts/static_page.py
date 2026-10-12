"""Styles shared by the standalone pages the build writes beside the app: the API guide
(/api/) and the open-source health methodology (/open-source-health/).

Both pages own their <head> and inline these rules, so they live here once and cannot drift.
The rules mirror the Open Press tokens in src/styles/tokens.css.
"""

STATIC_PAGE_CSS = """  :root {
    --canvas: #ffffff; --card: #ffffff; --surface: #f4f6fa;
    --primary: #0c815a; --gold: #c08a3e;
    --ink: #10173e; --ink-2: #3f4660; --ink-muted: #5c6278; --ink-faint: #5c6278;
    --border: #e0e3eb; --border-light: #e0e3eb;
    --shadow: none;
    --sans: 'Hanken Grotesk', system-ui, -apple-system, sans-serif;
    --mono: ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, monospace;
    --measure: 68ch;
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--canvas); color: var(--ink); font-family: var(--sans);
    font-size: 15px; line-height: 1.65; -webkit-font-smoothing: antialiased; }
  .masthead { border-bottom: 1px solid var(--border-light); background: var(--card); }
  .masthead-in { max-width: 82ch; margin: 0 auto; padding: .85rem 1.5rem;
    display: flex; align-items: center; justify-content: space-between; gap: 1rem; }
  .masthead img { height: 26px; width: auto; display: block; }
  .back { font-size: .875rem; font-weight: 600; color: var(--primary); text-decoration: none; }
  .back:hover { text-decoration: underline; }
  .wrap { max-width: 82ch; margin: 0 auto; padding: 3rem 1.5rem 5rem; }
  .stack { display: flex; flex-direction: column; gap: 2.75rem; }
  .prose { max-width: var(--measure); }
  .eyebrow { font-size: .9375rem; font-weight: 600; color: var(--ink-muted); margin: 0 0 .6rem; }
  h1 { font-size: 2.4rem; font-weight: 600; letter-spacing: -.02em; line-height: 1.12;
    text-wrap: balance; margin: 0 0 .75rem; }
  .standfirst { font-size: 1.0625rem; color: var(--ink-2); margin: 0; max-width: var(--measure); }
  h2 { font-size: 1.4rem; font-weight: 600; letter-spacing: -.01em; line-height: 1.2; text-wrap: balance; margin: 0 0 .5rem; }
  h3 { font-size: .9375rem; font-weight: 600; margin: 0 0 .3rem; }
  p { color: var(--ink-2); margin: 0 0 .75rem; }
  p:last-child { margin-bottom: 0; }
  strong { color: var(--ink); font-weight: 600; }
  a { color: var(--primary); text-underline-offset: 2px; }
  a:focus-visible { outline: 2px solid var(--primary); outline-offset: 3px; }
  section { display: flex; flex-direction: column; gap: .85rem; }
  hr { height: 1px; background: var(--border-light); border: 0; margin: 0; }
  code { font-family: var(--mono); font-size: .855em; background: var(--surface);
    border: 1px solid var(--border-light); padding: .1em .35em; }
  pre { font-family: var(--mono); font-size: .8125rem; line-height: 1.7; background: var(--card);
    border: 1px solid var(--border); padding: 1rem 1.15rem;
    overflow-x: auto; box-shadow: var(--shadow); margin: 0; }
  pre code { background: none; border: 0; padding: 0; font-size: inherit; }
  .c-key { color: var(--primary); } .c-com { color: var(--ink-faint); font-style: italic; }
  .c-str { color: var(--gold); }
  .endpoint { display: flex; align-items: center; gap: .75rem; flex-wrap: wrap; background: var(--card);
    border: 1px solid var(--border); padding: .85rem 1.1rem; box-shadow: var(--shadow); }
  .method { font-family: var(--mono); font-size: .7rem; font-weight: 600; letter-spacing: .06em;
    color: var(--primary); border: 1px solid var(--primary); padding: .1rem .4rem; }
  .endpoint a { font-family: var(--mono); font-size: .8125rem; word-break: break-all; color: var(--ink); }
  .scroll { overflow-x: auto; border: 1px solid var(--border); box-shadow: var(--shadow); }
  table { border-collapse: collapse; width: 100%; background: var(--card); font-size: .8125rem; }
  th, td { text-align: left; padding: .6rem .85rem; border-bottom: 1px solid var(--border-light); vertical-align: top; }
  th { font-size: .8125rem; color: var(--ink-muted); font-weight: 600; white-space: nowrap; background: var(--surface); }
  tr:last-child td { border-bottom: 0; }
  td:first-child { font-family: var(--mono); font-size: .8125rem; color: var(--ink); white-space: nowrap; }
  td.note { color: var(--ink-muted); }
  td.num { font-variant-numeric: tabular-nums; white-space: nowrap; }
  .notes { display: flex; flex-direction: column; max-width: var(--measure); }
  .note-item { padding: 1rem 0; border-top: 1px solid var(--border-light);
    display: flex; flex-direction: column; gap: .15rem; }
  .note-item:first-child { border-top: 0; padding-top: .25rem; }
  footer { color: var(--ink-faint); font-size: .8125rem; max-width: var(--measure); }
  @media (prefers-reduced-motion: reduce) { * { animation: none !important; transition: none !important; } }
"""
