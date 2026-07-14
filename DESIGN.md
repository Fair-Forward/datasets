---
name: FAIR Forward Data Catalog
description: Reusable, open AI building blocks for global development challenges, built by local partners.
colors:
  primary: "#0c815a"
  primary-light: "#17a673"
  canvas: "#f6f7f7"
  card: "#ffffff"
  surface-cool: "#f4f6f6"
  surface-inset: "#f8fafc"
  ink: "#141a1f"
  ink-secondary: "#48505a"
  ink-muted: "#5f6873"
  ink-faint: "#9aa2ac"
  border: "#e3e6e8"
  border-soft: "#e7e9eb"
  border-light: "#eef0f1"
  gold: "#c08a3e"
  success: "#1f9d57"
  warning: "#f59e0b"
  danger: "#ef4444"
  info: "#3b82f6"
typography:
  display:
    fontFamily: "Hanken Grotesk, system-ui, -apple-system, sans-serif"
    fontSize: "2.75rem"
    fontWeight: 500
    lineHeight: 1.1
    letterSpacing: "-0.015em"
  headline:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "1.7rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "-0.01em"
  title:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "1.1875rem"
    fontWeight: 600
    lineHeight: 1.3
    letterSpacing: "normal"
  body:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "1.0625rem"
    fontWeight: 400
    lineHeight: 1.65
    letterSpacing: "normal"
  label:
    fontFamily: "Hanken Grotesk, system-ui, sans-serif"
    fontSize: "0.8125rem"
    fontWeight: 500
    lineHeight: 1.3
    letterSpacing: "normal"
rounded:
  sm: "6px"
  md: "10px"
  card: "14px"
  lg: "16px"
  xl: "20px"
  pill: "999px"
spacing:
  "1": "4px"
  "2": "8px"
  "3": "12px"
  "4": "16px"
  "5": "20px"
  "6": "24px"
  "8": "32px"
  "10": "40px"
  "12": "48px"
  "16": "64px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.card}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    padding: "0.375rem 0.625rem"
  button-primary-hover:
    backgroundColor: "{colors.primary-light}"
    textColor: "{colors.card}"
  button-secondary:
    backgroundColor: "rgba(13, 138, 95, 0.08)"
    textColor: "{colors.primary}"
    rounded: "{rounded.md}"
    padding: "0.375rem 0.625rem"
  button-view-details:
    backgroundColor: "{colors.card}"
    textColor: "{colors.ink-secondary}"
    rounded: "{rounded.md}"
    padding: "0.375rem 0.5rem"
  chip:
    backgroundColor: "{colors.card}"
    textColor: "{colors.ink-secondary}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "0.2rem 0.5rem"
  card:
    backgroundColor: "{colors.card}"
    rounded: "{rounded.card}"
    padding: "1.05rem 1.1rem"
  input-search:
    backgroundColor: "{colors.surface-cool}"
    textColor: "{colors.ink}"
    rounded: "{rounded.card}"
    padding: "0.9rem 1.1rem"
  nav-link:
    textColor: "{colors.ink-secondary}"
    rounded: "{rounded.pill}"
    padding: "0.45rem 1.05rem"
  nav-link-active:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.card}"
    rounded: "{rounded.pill}"
    padding: "0.45rem 1.05rem"
  filter-segment-active:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.card}"
    rounded: "{rounded.sm}"
    padding: "0.4rem 0.9rem"
---

# Design System: FAIR Forward Data Catalog

## 1. Overview

**Creative North Star: "The Open Greenhouse"**

This is a bright, cultivated, growing space. A greenhouse is airy and light-filled by design, and every plant inside is credited to the hands that grew it. That is the whole system in one image: a near-white cool canvas (`#f6f7f7`) that reads as daylight, pure-white cards that hold each project like a labelled specimen, and a living emerald (`#0c815a`) reserved for the things that are alive on the page: actions, current selection, the growth of the collection. Optimism here is quiet. Nothing glows, nothing shouts; the work takes root and speaks for itself.

The system serves a task first. A practitioner arrives to find a dataset or use case they can reuse, and the interface's job is to get out of the way: legible type, generous light, a fast path from search to source. But the same surface has to make a serious impression on funders and newcomers, so the hero and stats strip are allowed a little more air and confidence than the working rows below them. It restrains itself deliberately. It rejects the gradient-hero SaaS pitch, the NGO stock-photo appeal, the gray bureaucratic data-portal grid, the neon sci-fi "AI" aesthetic, and above all the generic generated-page look: dense default boxes, stock fonts, cookie-cutter widgets. Distinction is grown through craft and light, never assembled from defaults.

Warmth lives in a single kept ember: the gold (`#c08a3e`) that marks the "Catalyzed by" attribution and the sustainable endpoint of the maturity pipeline. Everything else is cool, clean, and calm.

**Key Characteristics:**
- Cool white-based canvas; pure-white cards float on whisper-grey daylight.
- One living emerald for action and life; used sparingly, never decoratively.
- A single humanist sans (Hanken Grotesk) doing all the work, from display to label.
- Soft, low-opacity shadows; depth by light, not by weight.
- Gold as the one warm accent, earned by a single meaning (attribution / sustained impact).

## 2. Colors

A cool, daylight palette: near-white surfaces, near-black cool ink, one saturated emerald that carries every living element, and a single warm gold held in reserve.

### Primary
- **Greenhouse Emerald** (`#0c815a`): the one living color. Primary buttons, active nav pills, the active filter segment, current selection, focus rings, links, the "is-primary" stat, and the deep end of the data-viz ramp. It appears on a small fraction of any screen on purpose; its rarity is what makes it read as "alive."
- **Sprout Emerald** (`#17a673`): the lighter partner. Primary-button hover, gradient partners, input focus borders. Never a resting fill on its own.

### Secondary
- **Catalyst Gold** (`#c08a3e`): the single warm ember. Reserved for the "Catalyzed by" attribution dot and the sustainable-business endpoint of the maturity pipeline. It carries exactly one meaning; do not spend it on decoration.

### Neutral
- **Daylight Canvas** (`#f6f7f7`): the page background. Cool whisper-grey, explicitly not warm. This is the air of the greenhouse.
- **Specimen White** (`#ffffff`): card, header, and nav surfaces. Pure white, floating a step above the canvas.
- **Cool Inset** (`#f4f6f6`) / **Field Inset** (`#f8fafc`): recessed surfaces, the hero search well, filter-bar controls, rails.
- **Cool Ink** (`#141a1f`): primary text and display titles. Near-black with a cool cast, never pure `#000`.
- **Secondary Ink** (`#48505a`): body-secondary text, view-details labels, subtitle.
- **Muted Ink** (`#5f6873`): muted labels and metadata.
- **Faint Ink** (`#9aa2ac`): placeholder text, eyebrow meta, faint captions. Reserved for genuinely tertiary information; never body copy.
- **Hairlines** (`#e3e6e8` border / `#e7e9eb` soft / `#eef0f1` light): the three-step border ramp. Card edges, chip strokes, inner dividers. Structure is drawn with light hairlines, not shadow.

### Named Rules
**The One Living Color Rule.** Emerald is the only saturated color allowed to carry meaning, and only for action, selection, state, and the growth of the collection. If emerald is being used to decorate, it is being misused. Target: emerald on roughly 10% or less of any resting screen.

**The Single Ember Rule.** Gold means one thing (attribution / sustained impact) and appears in one or two places. It is never promoted to a second accent, never used for a button, never used for emphasis.

## 3. Typography

**Display / Body / Label Font:** Hanken Grotesk (with `system-ui, -apple-system, sans-serif` fallback), loaded at weights 400/500/600/700/800.

**Character:** One humanist sans does everything. There is no serif and no mono in this direction; the older editorial pairing was retired in favor of a single clean voice that reads as calm competence at every size. Contrast comes from weight and scale, not from mixing families. A humanist sans keeps the tone approachable (open, inviting) while staying crisp enough to feel trustworthy.

### Hierarchy
- **Display** (500, 2.75rem, line-height 1.1, letter-spacing -0.015em): the hero H1 only. Confident but not shouting; capped well below a marketing-scale headline.
- **Headline** (600, 1.7rem, letter-spacing -0.01em): stat-strip values and major section titles.
- **Title** (600, ~1.1875rem): card titles and panel subheads.
- **Body** (400, ~1.0625rem, line-height 1.65): running copy and the hero subtitle (which runs slightly larger and lighter at line-height 1.55). Prose columns capped at 44rem so lines stay in the 65-75ch comfort zone.
- **Label** (500, ~0.8125rem): chips, nav, meta, and small UI. Sentence case, not tracked-out uppercase eyebrows.

### Named Rules
**The One Voice Rule.** Hanken Grotesk is the whole typographic system. Do not introduce a second family for "editorial" flavor, a mono for "technical" labels, or a display serif for headings. Weight and size carry the hierarchy.

**The No-Eyebrow Rule.** No tiny uppercase letter-spaced kickers stacked above every section. Labels are sentence case. Hierarchy is size and weight, not decoration.

## 4. Elevation

Depth is conveyed by **light, not weight**. Surfaces are near-flat, layered by value (canvas -> white card -> emerald action) and separated by hairline borders. Shadows are soft and very low-opacity (alpha 0.04-0.08); they exist to lift a card a hair off the daylight and to respond to hover, not to build heavy 2014-app drop shadows.

### Shadow Vocabulary
- **Rest** (`--shadow-sm`, `0 1px 3px rgba(0,0,0,0.04)`): the resting card lift. Barely there.
- **Hover** (`--shadow-lg`, `0 8px 24px rgba(0,0,0,0.08)`): paired with a 2px upward translate on card hover. The card rises toward the light.
- **Focus** (`--shadow-focus`, `0 0 0 3px rgba(13,138,95,0.15)`): the emerald focus ring on inputs and interactive wells.
- **Panel** (`--shadow-panel`, `-12px 0 40px rgba(20,26,31,0.10)`): the one deliberately larger shadow, cast by the detail panel as it slides in over the catalog.

### Named Rules
**The Daylight Rule.** If a shadow is dark enough to notice as gray, it is too dark. Depth is a whisper. The one exception is the sliding detail panel, which is allowed a real shadow because it genuinely floats above everything else.

## 5. Components

### Buttons
- **Shape:** gently rounded, 10px radius (`--radius-md`); compact padding (`0.375rem 0.625rem`), label-weight text.
- **Primary:** emerald fill (`#0c815a`), white text, a faint emerald-tinted shadow (`0 2px 4px rgba(13,138,95,0.15)`). Hover lifts to Sprout Emerald (`#17a673`) with a slightly stronger tint shadow. Transition ~200ms ease-out.
- **Secondary:** emerald tint fill (`rgba(13,138,95,0.08)`), emerald text. Hover deepens the tint to `0.12`. No border.
- **View details (tertiary):** white fill, secondary-ink text, 1px border. Hover swaps to the canvas background with emerald text.

### Chips
- **Data-type chips:** pill (`--radius-pill`), white background, hairline border, label type (~0.8125rem, weight 500), tight padding (`0.2rem 0.5rem`). Quiet by default.
- **SDG badge:** pill overlay on the card image, semi-opaque white with a small backdrop blur, emerald text, a colored SDG dot. The only place backdrop-blur is sanctioned, because it sits over photography.

### Cards
- **Corner style:** 14px radius (`--radius-card`).
- **Background:** Specimen White on the Daylight Canvas.
- **Border:** 1px soft hairline (`#e7e9eb`), deepening to `--border` on hover.
- **Shadow strategy:** Rest shadow at rest; on hover, translateY(-2px) plus the Hover shadow (see Elevation). The card rises toward the light.
- **Internal padding:** `1.05rem 1.1rem`; image header ~10.5rem with a soft-fade gradient into the body, or an emerald-tinted gradient placeholder when no image exists.
- **Nesting:** cards are never nested. A card is a leaf.

### Inputs / Fields
- **Hero search:** a recessed Cool Inset well, 1.5px hairline border, ~14px radius, roomy padding (`0.9rem 1.1rem`), body-large text. Focus-within lights the border emerald and adds the emerald focus ring.
- **Filter selects / search box:** inset Field surface (`#f8fafc`), 10px radius, transparent border at rest, rest shadow. Focus shifts the border to Sprout Emerald and adds the focus ring.
- **Placeholder:** Faint Ink (`#9aa2ac`).

### Navigation
- **Style:** pill nav links, weight 600, on the white top bar. Active link is a solid emerald pill with white text; hover on an inactive link tints the text emerald and adds a light-grey pill background.
- **Filter segmented control:** a `#eceff0` track holding pill-less segments; the active segment is a solid emerald block with white text at 6px radius. One segmented control, consistent everywhere.

### Detail Panel (signature component)
A wide (76rem) panel that slides in from the right over the catalog, carrying the full project narrative: description, data/model characteristics, links, documents. It is the one surface allowed a real shadow (`--shadow-panel`) and the primary place the "asset is the destination" principle pays off, ending in the outbound links and downloads.

## 6. Do's and Don'ts

### Do:
- **Do** keep emerald (`#0c815a`) rare and meaningful: action, selection, state, focus, and the growth of the collection. Aim for it on 10% or less of any resting screen.
- **Do** build structure with hairline borders and value layering (canvas -> white -> emerald), and keep shadows a barely-there whisper.
- **Do** carry the whole type system on Hanken Grotesk; express hierarchy through weight and size.
- **Do** credit the makers visibly: provenance, authorship, and the "Catalyzed by" gold ember are features, not footnotes.
- **Do** give the hero and stats strip a little more air and confidence than the working rows, so the showcase impresses without stealing from the task.
- **Do** hold body text to at least 4.5:1 contrast, keep visible emerald focus rings, and preserve reduced-motion and keyboard support.

### Don't:
- **Don't** build a corporate SaaS pitch: no gradient hero, no big-number hero-metric template, no buy-now landing framing. This is a public good, not a product for sale.
- **Don't** use aid-org stock imagery, beneficiary photos, or savior/charity framing.
- **Don't** slip into the dense bureaucratic data-portal look: gray government tables, cramped rows, no hierarchy.
- **Don't** chase the trendy AI aesthetic: no neon-on-black, glowing orbs, or sci-fi spectacle. The AI here is practical infrastructure.
- **Don't** ship the generic generated-page look: over-dense default boxes, stock fonts, and cookie-cutter buttons/widgets/card grids. If it reads as assembled-from-defaults, rebuild it.
- **Don't** promote gold to a second accent, use a `border-left` colored stripe as an accent, apply gradient text, or use glassmorphism anywhere except the SDG badge over photography.
- **Don't** warm the canvas. The background is cool whisper-grey by decision; no cream, sand, paper, or beige.
- **Don't** nest cards, or introduce a second type family or a tracked-out uppercase eyebrow above sections.
