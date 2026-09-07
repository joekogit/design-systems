# Design Template Library — Design Spec

**Date:** 2026-09-06
**Status:** Approved (phase 1 build)

## Purpose

A browsable reference library rendering one complex, responsive, mobile-optimised showcase page for
each design system in the `design-md` skill (74 `DESIGN.md` files at
`~/.claude/skills/design-md/references/*.md`). Used to choose and lift a design language when
starting client projects.

## Success criteria

1. Every generated page is a **single self-contained HTML file** — inline CSS and JS, no relative
   dependencies — so it can be copied into any project unchanged.
2. Pages are structurally rich enough (14 sections) to actually represent a design language, not
   just its palette.
3. Any two pages are visibly *different in structure*, not only in colour.
4. Each page carries a spec appendix that makes it useful as a reference: copyable tokens, type
   scale, component zoo.
5. An index page makes 74 designs findable in seconds.
6. Meets ui-ux-pro-max standards; verified at 375 / 768 / 1024 / 1440px.

## Non-goals

- Reproducing brand logos, wordmarks, proprietary fonts, or marketing copy. Design *language* only.
- A JS framework, bundler, or package manager. Plain HTML/CSS/JS.
- Pixel-cloning any real website.

## Architecture

    awesome-design/
    ├── build.py                 # composes skeleton + tokens + content -> standalone page
    ├── index.html               # generated library navigator
    ├── shared/
    │   ├── skeleton.html        # section markup with variant slots + {{placeholders}}
    │   ├── base.css             # structural layer; every value is var(--token)
    │   ├── page.js              # mobile nav, scroll reveal, copy-token, spec tabs
    │   └── images.json          # 83 verified Unsplash ids, category-tagged
    ├── src/
    │   ├── <slug>.css           # the design: full token set + component overrides
    │   └── <slug>.json          # the content: copy, section variants, icons, image ids
    ├── designs/<slug>.html      # GENERATED — never hand-edited
    └── docs/superpowers/specs/

### Build model

`build.py` reads a `src/<slug>.{css,json}` pair, injects content into `shared/skeleton.html`,
inlines `shared/base.css` + `src/<slug>.css` + `shared/page.js`, and writes
`designs/<slug>.html`. Rebuilding all pages after a skeleton change is one command.

### Anti-sameness mechanism

The JSON selects **structural variants** per section, emitted as classes on the section element:

| Section | Variants |
|---|---|
| nav      | `bar`, `floating-pill`, `minimal`, `chrome`, `sidebar` |
| hero     | `split`, `centered`, `full-bleed`, `product-frame`, `terminal` |
| features | `grid`, `bento`, `list`, `numbered` |
| cards    | `bordered`, `elevated`, `flat`, `image-top` |
| gallery  | `masonry`, `filmstrip`, `grid`, `feature-left` |

`base.css` gives each variant a workable default layout; `src/<slug>.css` is free to restructure
grids, type scale, radii, shadows, and imagery treatment on top. This is what prevents 74 pages from
reading as 74 recolours.

## Page structure (14 sections)

1. Library bar — persistent "back to library" strip, design name, category
2. Nav
3. Hero
4. Logo marquee (social proof)
5. Feature grid — 6 Phosphor icons
6. Showcase A — image / copy split
7. Showcase B — reversed, with checklist
8. Metrics band — 4 figures
9. Image gallery
10. Testimonial — quote + portrait
11. Pricing — 3 tiers, one featured
12. FAQ — native `<details>` accordion
13. CTA band
14. Footer + **design spec appendix**: click-to-copy colour swatches for every token, type-scale
    specimen, spacing / radii / shadow scales, motion curves, component zoo (buttons in all states,
    inputs, badges, tabs, toggles, table, alerts)

## Index page

Search box, category filter chips, and a card grid. Each card is a **CSS-rendered mini-preview**
using that design's own canvas, surface, accent and type treatment — readable at a glance without
screenshots. Sort by category, name, or light/dark.

## Assets

- **Icons:** Phosphor via `https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.2/src/<weight>/style.css`.
  All six weights verified. Weight is chosen per design (`thin` for Apple, `bold` for Nike,
  `fill` for Spotify).
- **Images:** `https://images.unsplash.com/photo-<id>?w=<n>&q=80&auto=format&fit=crop`.
  83 category-tagged ids verified returning 200. `source.unsplash.com` is discontinued — never use it.
- Images carry real alt text, `loading="lazy"`, explicit width/height, and `w=` srcset variants.

## Standards (ui-ux-pro-max)

44px minimum touch targets; visible `:focus-visible` rings; `aria-label` on icon-only buttons;
descriptive alt text; `prefers-reduced-motion` honoured; 16px minimum mobile body text; no
horizontal scroll; no emoji used as iconography; transitions 150–300ms on transform/opacity only;
contrast >= 4.5:1 for body text in every design.

## Phase 1 — 10 designs

`linear.app`, `stripe`, `apple`, `vercel`, `spotify`, `nike`, `wired`, `notion`, `supabase`,
`nintendo-2001`.

Chosen for maximum spread: dark minimal, light gradient, premium light, monochrome, vibrant dark,
photo-led, editorial serif, warm minimal, developer dark, and retro chrome. `nintendo-2001` is a
deliberate stress test of how far the shared skeleton can be pushed.

## Deployment

**Undecided — must be confirmed with the user before any push.** Likely target is
`https://github.com/joekogit/client-sandbox`. The architecture is already compatible with GitHub
Pages: absolute CDN URLs, and the only relative links are `index.html` -> `designs/*.html`, which
resolve correctly under a project subpath.
