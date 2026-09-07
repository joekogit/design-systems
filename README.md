# Design Template Library

A reference library that renders each design system from the
[`design-md`](https://github.com/VoltAgent/awesome-design-md) collection as a complete,
responsive page — so you can see what a design language actually does to a pricing table, a
form field and a data table, not just to a hero.

Open `index.html` to browse. 74 systems catalogued, 25 built out so far.
Live at **https://systems.joeko.net**. See `DEPLOY.md`.

## Why this exists

`getdesign.md` already hosts a preview per system, and it is good for browsing. This library
exists for the other job — **lifting a design into a project**:

| | getdesign.md | this library |
|---|---|---|
| Depth | hero + a section or two | 14 sections, ~10,000px |
| Components | not shown | buttons in 4 states, inputs, badges, tabs, toggle, table, alerts |
| Portability | hosted page | one self-contained HTML file you copy into a project |
| Comparison | layout varies per design | identical skeleton, so only the design changes |

## Layout

```
build.py            compose skeleton + tokens + content -> standalone page
index.html          the library navigator (generated)
shared/
  skeleton.html     section markup with variant slots
  base.css          structural layer; every value is a token
  a11y.css          accessibility floor, applied AFTER the design layer
  page.js           mobile nav, reveal, copy-token, tabs
  images.json       verified Unsplash ids + accurate alt text
  index.{html,css,js}
src/
  <slug>.tokens.css derived from the design-md reference (hand-tunable)
  <slug>.css        the design's character layer
  <slug>.json       content, section variants, icons, image ids
designs/<slug>.html GENERATED — do not hand-edit
tools/audit.html    loads every page in a 375px iframe and reports a11y/layout issues
```

## Commands

```bash
python3 build.py scaffold <slug>   # derive token CSS from the design-md reference
python3 build.py page <slug>       # build one page
python3 build.py all               # build every page, then the index
python3 build.py index             # rebuild the index only
python3 build.py catalog           # list all 74 with scheme and canvas colour
```

## Adding a design

1. `python3 build.py scaffold <slug>` — writes `src/<slug>.tokens.css` from the reference's
   frontmatter. Ten of the 74 references are prose-only and produce defaults; those need the
   token block written by hand.
2. Write `src/<slug>.json` — content plus the section variants (`nav`, `hero`, `features`,
   `cards`, `gallery`). **The variants are what stop the pages looking like recolours of each
   other**, so pick them from the reference's layout notes rather than defaulting.
3. Write `src/<slug>.css` — the character layer. This is where the look actually lives.
4. `python3 build.py page <slug>` and check it in `tools/audit.html`.

## Checking your work

```bash
python3 -m http.server 8899        # the audit harness needs http, not file://
```

Then open `http://127.0.0.1:8899/tools/audit.html` and run `window.ready.then(()=>console.table(window.audit()))`.
It reports, per page: horizontal scroll, images missing alt text, computed body size,
interactive targets under 44px, and icons that fail to resolve a glyph. All twenty-five current
pages report zero on every count.

## Conventions

- Generated pages are **self-contained**: inline CSS and JS, absolute CDN URLs, no relative
  dependencies. Copy one file anywhere and it works, including from `file://`.
- `a11y.css` is concatenated last so a design can restyle the focus ring but cannot remove it,
  and cannot push a touch target below 44px or body copy below 16px on a phone.
- Alt text comes from `shared/images.json`, never from the design JSON, so a page cannot ship a
  caption that misdescribes its photo. Adding an image id that is not in the bank fails the build.
- `images.unsplash.com/photo-<id>` only. `source.unsplash.com` is discontinued.
- Phosphor encodes weight as a **class**, not a name suffix: `ph-fill ph-cpu`, never
  `ph ph-cpu-fill`. `build.py` rewrites the suffix form, derives the stylesheets each page needs
  from the icons it actually uses, and **fails the build** on an icon name that is not among the
  1,530 in `shared/phosphor-names.json`. A misspelt icon renders as nothing at all, silently.
- Content JSON must use literal UTF-8 characters, not HTML entities — most fields are escaped on
  the way out, so `&middot;` would render as text. The build rejects entities outside `hero.title`
  (the one intentionally-raw field).

## Attribution and scope

These files describe design *language* — palettes, scales, component rules — extracted from
public sites. No logos, wordmarks, proprietary fonts or brand copy are reproduced; proprietary
typefaces are substituted with licensed near-matches and the substitution is noted in each page's
spec appendix. Product names and copy on the pages are invented. Not affiliated with any brand shown.

Icons: [Phosphor](https://phosphoricons.com/). Photography: [Unsplash](https://unsplash.com/).
