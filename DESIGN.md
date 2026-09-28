---
name: FAIR Forward Data Catalog
description: Reusable, open AI building blocks for global development challenges, built by local partners.
colors:
  paper: "#ffffff"
  paper-2: "#f4f6fa"
  paper-3: "#eaedf4"
  ink: "#10173e"
  ink-2: "#3f4660"
  ink-3: "#5c6278"
  ink-faint: "#8d92a2"
  hairline: "#e0e3eb"
  hairline-strong: "#c8ccd8"
  press-ink: "#2a3486"
  press-ink-deep: "#1b216d"
  press-ink-soft: "#cacde1"
  spot: "#0c815a"
  spot-deep: "#006d49"
  spot-pressed: "#005a3c"
  ember: "#c08a3e"
  viz-1: "#e8ecf9"
  viz-2: "#b2bde0"
  viz-3: "#808ec4"
  viz-4: "#5261a5"
  viz-5: "#2a3486"
  map-land: "#e6e9f0"
  map-land-hover: "#dde1ea"
  map-border: "#d5d9e4"
  success: "#1e8347"
  warning: "#a15b00"
  danger: "#c8352a"
  info: "#2f5fa8"
  purple: "#6b4fa0"
  cyan: "#0f7c8c"
  overlay: "rgba(16, 23, 62, 0.28)"
  shadow-tint: "rgba(16, 23, 62, 0.45)"
  plate-dot: "#000000"
  plate-blank: "#b8b8b8"
typography:
  display:
    fontFamily: "Hanken Grotesk, system-ui, -apple-system, sans-serif"
    fontSize: "3.25rem"
    fontWeight: 600
    lineHeight: 1.08
    letterSpacing: "-0.024em"
  display-md:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "2.6rem"
    fontWeight: 600
    lineHeight: 1.08
  display-sm:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "2.25rem"
    fontWeight: 600
    lineHeight: 1.1
  display-xs:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "2rem"
    fontWeight: 600
    lineHeight: 1.1
  figure:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "2.5rem"
    fontWeight: 600
    lineHeight: 1
    letterSpacing: "-0.02em"
  figure-sm:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "2rem"
    fontWeight: 600
    lineHeight: 1
  title:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "3rem"
    fontWeight: 600
    lineHeight: 1.05
    letterSpacing: "-0.02em"
  headline:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "2.4rem"
    fontWeight: 600
    lineHeight: 1.1
    letterSpacing: "-0.016em"
  statement:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "1.875rem"
    fontWeight: 500
    lineHeight: 1.2
  section:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "1.75rem"
    fontWeight: 600
    lineHeight: 1.15
    letterSpacing: "-0.01em"
  subsection:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "1.45rem"
    fontWeight: 600
    lineHeight: 1.2
  entry:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "1.3rem"
    fontWeight: 600
    lineHeight: 1.22
  body-large:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "1.375rem"
    fontWeight: 400
    lineHeight: 1.55
  body:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.6
  ui:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "1rem"
    fontWeight: 500
    lineHeight: 1.4
  meta:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "0.9375rem"
    fontWeight: 400
    lineHeight: 1.45
  label:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 500
    lineHeight: 1.3
  caption:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 400
    lineHeight: 1.3
  code:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
    fontSize: "0.88em"
    fontWeight: 400
rounded:
  none: "0"
  dot: "50%"
spacing:
  "1": "0.25rem"
  "2": "0.5rem"
  "3": "0.75rem"
  "4": "1rem"
  "5": "1.25rem"
  "6": "1.5rem"
  "8": "2rem"
  "10": "2.5rem"
  "12": "3rem"
  "16": "4rem"
components:
  riso-print:
    underprintOpacity: 0.72
    keyOpacity: 0.8
    keyInk: "{colors.press-ink}"
    screen: "4px dots, 45 degrees"
    rounded: "{rounded.none}"
  figures-line:
    numbers: "{typography.figure}"
    labels: "{typography.body}, on the number's baseline"
    separation: "space only, no rules"
  button-primary:
    backgroundColor: "{colors.spot}"
    textColor: "{colors.paper}"
    rounded: "{rounded.none}"
    padding: "0.85rem 1.5rem"
  button-primary-hover:
    backgroundColor: "{colors.spot-deep}"
  link-quiet:
    textColor: "{colors.ink}"
    decoration: "underline, 35% ink, solid on hover"
  tab-active:
    textColor: "{colors.ink}"
    indicator: "2px {colors.spot} underline"
  select:
    backgroundColor: "{colors.paper-2}"
    hover: "{colors.paper-3}"
    border: "none"
    rounded: "{rounded.none}"
  input-search:
    backgroundColor: "{colors.paper-2}"
    border: "none at rest"
    focus: "paper fill, ink border + 2px {colors.spot} outline"
    rounded: "{rounded.none}"
---

# Design System: FAIR Forward Data Catalog

## 1. Overview

**Creative North Star: "The Open Press"**

The catalogue reads as an index printed on a community risograph press: white stock, one navy ink for type and the key plate of every picture, photographs pulled as two-colour prints, and a single emerald spot colour reserved for everything a reader can act on. The press is the brand's own: its navy is the FAIR Forward logo ink (`#0a0050`), opened up slightly into the press ink (`#2a3486`) for printing pictures.

The riso poster that seeded this direction ("window seat": layered inks, a halftone screen, calm) gives the system its signature, **the riso print**: every project photo is printed as a soft colour underprint with a navy halftone key overprinted on it, so a grid of mismatched stock photographs becomes one coherent printed run while each photo keeps its own colour. The header is deliberately plain: the title, a lead, the search, and one line of figures. No rules, no boxes, no motion.

The system serves a task first. A practitioner arrives to find a dataset, model or use case they can reuse, and the interface gets out of the way: one typeface, legible sizes, square and quiet controls, the shortest path from search to source. The header gives funders and newcomers a little more air and the catalogue's totals at a glance, never a pitch. The direction explicitly rejects the gradient-hero SaaS pitch, the metric-tile row, aid-agency stock imagery shown raw, the grey bureaucratic data portal, neon "AI" spectacle, and the generic generated-page look of rounded white cards with soft shadows.

**Key characteristics:**
- White paper, navy ink, one emerald spot colour, one warm ember.
- Pictures printed, not pasted: two-plate riso prints with a halftone key.
- One typeface (Hanken Grotesk) from display to caption; weight and size carry hierarchy.
- Square corners on surfaces and controls; only dots are round.
- Flat surfaces separated by hairlines; shadows only on things that float.
- Magnitudes print as halftone, areas as screens of the press ink.

## 2. Colors

A printer's palette: paper, a navy ink in a few strengths, the press ink for pictures and data, one spot colour for action, one warm ember.

### Paper and ink
- **Paper** (`#ffffff`): the only page ground.
- **Paper 2** (`#f4f6fa`) / **Paper 3** (`#eaedf4`): grouped regions (detail-panel rail, map sea, skeletons, hover fills). A trace of the ink's hue, never warm.
- **Ink** (`#10173e`): body text and headings, 17:1 on paper. Navy, not black: the whole page is printed in one ink.
- **Ink 2** (`#3f4660`, 9.3:1): secondary text. **Ink 3** (`#5c6278`, 6:1): meta, captions, labels, placeholders. Ink 3 is the floor for any text.
- **Ink faint** (`#8d92a2`, 3.1:1): non-text marks only (empty dots, dividers). Never text.
- **Hairline** (`#e0e3eb`) / **Hairline strong** (`#c8ccd8`): rules, control edges, list separators.

### Press ink
- **Press ink** (`#2a3486`): the key plate of every riso print, the depth and maturity dots, halftone bars, the fullest map screen. Deep variant `#1b216d` for map borders; soft screen `#cacde1` for empty marks.
- **Screens** (`#e8ecf9`, `#b2bde0`, `#808ec4`, `#5261a5`, `#2a3486`): even steps in OKLCH lightness at hue 272, for choropleths and the open places in the maturity chart. Ink text on the first three, white on the last two.

### Spot
- **Emerald** (`#0c815a`, 4.9:1): primary buttons, the current tab and nav item (as a 2px underline), destination links in the detail panel, focus rings, the country you are about to open on the map. Deep (`#006d49`) on hover, `#005a3c` when pressed.

### Ember
- **Ember** (`#c08a3e`): "Catalyzed by" attribution. One meaning, never decoration.

### Categorical and status
- **SDG colours** are the official UN palette, used only as small square swatches and in the SDG charts. They are data, not brand.
- **Status**: success `#1e8347`, warning `#a15b00`, danger `#c8352a` (all 4.5:1 or better on paper). Link health stays unpunitive: filled dot when available, hollow when not.

### Named rules
**The One Spot Rule.** Emerald means "you can act on this": the one primary action, the current selection, focus, and outbound destination links. It is never a fill for decoration, a chart colour, or an image tint.

**The Press Ink Rule.** The press ink is a material, not a signal. It prints pictures and data; no button, link or state uses it.

**The Single Ember Rule.** Gold carries one meaning (attribution) in one or two places. It is never promoted to a second accent.

**The Paper Rule.** The ground is white. Grouped regions take Paper 2. No cream, sand or warm band anywhere; warmth lives in the photographs.

## 3. Typography

**Family:** Hanken Grotesk (400 to 800), with `system-ui, -apple-system, sans-serif` fallback, loaded from Google Fonts. It carries every role; display text is the same face at heavier weight and tighter tracking.

### Hierarchy
Display sizes are tokens in `tokens.css` (`--type-*`); working sizes use the `--text-*` scale. The desktop root is 12px (an intentional 80% scale), so rem values render smaller there.

- **Display** (600, 3.25rem, line-height 1.08, tracking -0.024em): the catalogue title in the hero; steps down to 2.6rem on tablets, 2.25rem on phones and 2rem on small phones (`--type-display-md/sm/xs`).
- **Title** (600, 3rem): page titles (Insights).
- **Headline** (600, 2.4rem): the detail panel's project title.
- **Figure** (600, 2.5rem, tracking -0.02em, tabular): the catalogue's totals in the header and on Insights, each on the baseline of its label; 2rem on phones.
- **Statement** (500, 1.875rem): lead figures such as the SDG count.
- **Section** (600, 1.75rem): section headlines, the results count, dialog titles.
- **Subsection** (600, 1.45rem): sections inside the detail panel.
- **Entry** (600, 1.3rem, 3-line clamp): project titles on entries.
- **Body** (400, ~1.0625rem, line-height 1.6), **body large** (1.375rem) for ledes; prose capped near 46rem.
- **UI / meta / label / caption** (1rem to 0.8125rem): controls, metadata, chips. Sentence case throughout.

### Named rules
**The One Voice Rule.** Hanken Grotesk is the whole typographic system. No second family for "editorial" flavour, no mono for labels (code blocks keep a system monospace).

**The No-Eyebrow Rule.** No tiny uppercase tracked kickers above sections. Small labels are sentence case at label size.

**The Figures Rule.** Counts use tabular figures. Totals are a single line: each number on the baseline of a plain sentence-case label, separated by space alone; no rules, tiles, icons, colour accents or count-up animation, and never so large that the header outweighs the catalogue.

## 4. Elevation

Flat by default. Surfaces are separated by hairlines and by Paper 2, not by shadow. A shadow means "this floats above the page" and appears only on the detail panel (`-18px 0 48px -12px`), dialogs, the map tooltip and the country popover (`0 14px 32px -14px`), all tinted with the ink (`rgba(16, 23, 62, ...)`). Overlays behind floating layers are a flat ink wash (`rgba(16, 23, 62, 0.28)`), never a blur.

## 5. Components

### Riso print (signature)
`RisoPrint.jsx` + `.riso` in `main.css`, pure CSS. Two plates: the photo as a colour underprint (72% opacity, saturate 1.3, 1px blur, 1px off-register) and a navy key plate overprinted with `multiply` at 80%. The key is a real amplitude-modulated halftone: the photo in grey sits under a 45-degree dot screen (4px) at half strength, and `contrast(12)` on the plate thresholds the sum, so dots grow with the darkness beneath. When a print is about to open (hover or keyboard focus on its entry), it develops: the underprint rises to full strength and the key falls to 30%, bringing the photo close to how it was taken. Without a photo, the plate prints an even tint (a `#b8b8b8` plate). Black and white inside the plate (`#000000` dots, white paper) are the thresholding mechanism, never displayed: the ink layer turns them into press ink and paper. Prints are decorative (`aria-hidden`), lazy-loaded, and both plates share one request.

### Header
`CatalogHeader.jsx`. The title, the lead, the search as a filled Paper 2 field, and one line of figures (projects, datasets, pilots and use cases, countries) at figure size, each on the baseline of its label and separated by space alone. No rules, boxes, links or motion; Insights is reached from the top navigation. On phones the figures fall into a 2 by 2 grid. Insights repeats the line under its title.

Countries are counted by ISO code (`count_countries` in `scripts/utils.py`, the same rule the public API uses): regional and global scopes such as "East Africa" and "Global" stay filterable but are not countries, and the pipeline lists them as `filters.regions` so the live results count leaves them out too. The results line breaks the counts down only once a filter narrows the catalogue; unfiltered, it would repeat the header.

### Entries
Not boxed cards: a print, then the entry. Country and documentation depth (five press-ink dots) above a 3-line title and a 2-line description, type tags as hairline-bordered squares, and a footer rule with the SDG (square swatch, a filter button) and the license. The whole entry is one click target via the stretched title link; the title underlines on hover and the entry takes a spot outline on keyboard focus.

### Controls
- **View tabs** (All items / Datasets / Use cases, and Insights' section tabs): text tabs, the current one in ink with a 2px emerald underline.
- **Selects**: native selects, squared and filled (Paper 2, Paper 3 on hover), no border, a drawn chevron, sized to their current value.
- **Search**: a square filled field (Paper 2), no border at rest; on focus it turns white with an ink edge and an emerald ring. Filtering is live; Enter jumps to the results and moves focus to the live results count.
- **Buttons**: the square emerald button is reserved for a surface's one primary action (the retry on a failed load, the map's "View all projects"). Everything else is a quiet underlined link or a square hairline icon button (close, share, map zoom).
- **Active filters**: square Paper 2 chips with a remove mark.

### Detail panel
A 76rem sheet sliding in from the right over an ink wash (the one sheet with a real shadow). Narrative column: place, headline title, SDG swatches, contact, lede, and section headings as real `h2`s. Rail (Paper 2): the print, then the destination: dataset and model links as emerald rows between hairlines, then facts rows, link health, the maturity stepper in press-ink dots, and the organisations with square role swatches (press ink for Powered by, ember for Catalyzed by, ink 3 for Financed by).

### Data visualisation
Project maturity: a snapshot, never a funnel. Five cumulative columns (Datasets, Models+, Pilots+, Use cases+, Business model) each hold every project as one dot in the same place: press ink where the project reached the stage within the programme, the soft screen where the work stays open for others to build on. So every column stands the same height and no stage reads as projects lost. Above the later columns the open places run on as a fading screen, because reuse by others is not counted. Three text tabs re-form the same dots: what projects reached, the Lacuna Fund projects (the rest recede), and reuse by others (the open places ringed). Lacuna Fund projects are only shown, never described as funded for the dataset alone: some proposals included use-case building. A dot names its project and opens it, lighting the project up in all five columns in the spot colour; a column's count links to the catalogue's maturity filter, which returns exactly its inked dots. World map: land in paper grey, project countries in press-ink screens, emerald outline for the country you can open. SDG distribution: bars printed as a halftone screen of the press ink, re-inked emerald on hover, counts just past the bar end.

## 6. Motion

150 to 320ms, ease-out-quint (`cubic-bezier(0.22, 1, 0.36, 1)`), never bounce. Motion conveys state: a print developing on hover, the panel sliding in, dialogs and popovers settling, bars growing once when a chart first renders. Nothing moves on its own. `prefers-reduced-motion` collapses every duration.

## 7. Do's and Don'ts

### Do:
- **Do** print every project picture through `RisoPrint`; never show a raw stock photo in the grid.
- **Do** keep emerald to action, current selection, focus and destinations (The One Spot Rule).
- **Do** keep the page white and flat, with hairlines and Paper 2 for structure.
- **Do** carry hierarchy with Hanken Grotesk's weight and size alone.
- **Do** set totals as plain large figures with sentence-case labels, and count countries by ISO code, never by distinct strings.
- **Do** keep text at Ink 3 (`#5c6278`) or darker, visible focus, keyboard reach, and reduced-motion fallbacks.

### Don't:
- **Don't** build a SaaS pitch: no gradient hero, no metric tiles or cards around the figures, no count-up animations.
- **Don't** round surfaces or controls; only dots are round.
- **Don't** put a shadow on a resting surface, blur an overlay, or use glassmorphism.
- **Don't** use the press ink or the ember as action colours, or emerald as decoration.
- **Don't** add a second typeface, a mono label style, or uppercase tracked eyebrows.
- **Don't** use `border-left`/`border-right` colour stripes, gradient text, or a warm (cream, sand, beige) ground.
