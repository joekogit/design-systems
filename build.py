#!/usr/bin/env python3
"""
Build the design template library.

Composes shared/skeleton.html + shared/base.css + src/<slug>.tokens.css
+ src/<slug>.css + src/<slug>.json  ->  designs/<slug>.html   (standalone, no deps)

Usage:
    python3 build.py scaffold <slug>   # derive tokens from the design-md reference
    python3 build.py page <slug>       # build one page
    python3 build.py all               # build every page that has a src/<slug>.json
    python3 build.py index             # build index.html
"""
import json
import os
import re
import sys
import html

ROOT = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(ROOT, "src")
SHARED = os.path.join(ROOT, "shared")
OUT = os.path.join(ROOT, "designs")
REFS = os.path.expanduser("~/.claude/skills/design-md/references")

# ---------------------------------------------------------------- tiny YAML subset


def parse_frontmatter(text):
    """Parse the restricted YAML subset used by the design-md reference files.

    Handles: 2-space nested mappings, scalar values, single/double quoted strings.
    Returns {} when the file has no frontmatter (the 10 prose-format files).
    """
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    if end == -1:
        return {}
    body = text[3:end]

    root = {}
    # stack of (indent, container)
    stack = [(-1, root)]
    for raw in body.split("\n"):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip())
        line = raw.strip()
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        key = key.strip()
        val = val.strip()

        while stack and stack[-1][0] >= indent:
            stack.pop()
        if not stack:
            stack = [(-1, root)]
        parent = stack[-1][1]

        if val == "":
            node = {}
            parent[key] = node
            stack.append((indent, node))
        else:
            val = strip_yaml_comment(val)
            if len(val) >= 2 and val[0] == val[-1] and val[0] in "\"'":
                val = val[1:-1]
            parent[key] = val
    return root


def strip_yaml_comment(val):
    """Remove a trailing ` # comment`. Must not eat the `#` of a hex colour,
    and must not cut inside a quoted string (`"#e60012"  # Nintendo Red`)."""
    if not val:
        return val
    if val[0] in "\"'":
        q = val[0]
        end = val.find(q, 1)
        if end != -1:
            return val[: end + 1]
        return val
    # unquoted: a comment is ` #` — whitespace then hash
    m = re.search(r"\s+#", val)
    return val[: m.start()].rstrip() if m else val


def read_reference(slug):
    path = os.path.join(REFS, slug + ".md")
    if not os.path.exists(path):
        return "", {}
    with open(path, encoding="utf-8") as f:
        text = f.read()
    return text, parse_frontmatter(text)


# ---------------------------------------------------------------- token resolution

# canonical name -> ordered candidate keys in the reference's `colors` map
COLOR_MAP = {
    "primary":       ["primary", "accent", "brand", "cta", "primary-500", "interactive"],
    "on-primary":    ["on-primary", "primary-foreground", "on-accent", "cta-text"],
    "primary-hover": ["primary-hover", "accent-hover", "primary-light", "brand-hover"],
    "primary-soft":  ["primary-focus", "primary-muted", "primary-subtle", "accent-soft"],
    "accent-2":      ["secondary", "accent-2", "brand-secondary", "accent-alt", "tertiary"],
    "canvas":        ["canvas", "background", "bg", "surface-0", "base", "page"],
    "surface":       ["surface-1", "surface", "card", "elevated", "surface-primary", "panel"],
    "surface-2":     ["surface-2", "surface-alt", "card-alt", "surface-secondary", "muted"],
    "surface-3":     ["surface-3", "surface-tertiary", "overlay-surface"],
    "ink":           ["ink", "text", "foreground", "text-primary", "on-background"],
    "ink-muted":     ["ink-muted", "text-secondary", "muted-foreground", "text-muted"],
    "ink-subtle":    ["ink-subtle", "text-tertiary", "subtle", "text-subtle", "ink-tertiary"],
    "hairline":      ["hairline", "border", "divider", "outline", "border-subtle"],
    "hairline-strong": ["hairline-strong", "border-strong", "border-hover", "hairline-tertiary"],
    "success":       ["semantic-success", "success", "positive", "green"],
    "warning":       ["semantic-warning", "warning", "caution", "amber"],
    "danger":        ["semantic-error", "semantic-danger", "error", "danger", "negative", "red"],
    "inverse-canvas": ["inverse-canvas", "inverse-bg", "inverse-background"],
    "inverse-ink":   ["inverse-ink", "inverse-text", "inverse-foreground"],
}

TYPE_MAP = {
    "display-xl":  ["display-xl", "display-1", "hero", "display-large", "h1", "display"],
    "display-lg":  ["display-lg", "display-2", "display-medium", "h2", "section-title"],
    "display-md":  ["display-md", "display-3", "display-small", "h3", "subsection"],
    "headline":    ["headline", "h4", "title", "heading"],
    "card-title":  ["card-title", "h5", "subtitle", "card-heading"],
    "subhead":     ["subhead", "lead", "h6", "intro"],
    "body-lg":     ["body-lg", "body-large", "lead-body"],
    "body":        ["body", "body-base", "text", "paragraph"],
    "body-sm":     ["body-sm", "body-small", "small"],
    "caption":     ["caption", "meta", "footnote", "micro"],
    "button":      ["button", "cta", "label", "button-label"],
    "eyebrow":     ["eyebrow", "overline", "kicker", "tag"],
    "mono":        ["mono", "code", "monospace"],
}

# fallback sizes when a reference omits a step entirely
TYPE_DEFAULTS = {
    "display-xl": (76, 700, 1.05, -2.4), "display-lg": (54, 700, 1.10, -1.6),
    "display-md": (38, 600, 1.18, -0.9), "headline": (28, 600, 1.22, -0.5),
    "card-title": (21, 600, 1.28, -0.3), "subhead": (20, 400, 1.42, -0.2),
    "body-lg": (18, 400, 1.55, 0.0), "body": (16, 400, 1.6, 0.0),
    "body-sm": (14, 400, 1.55, 0.0), "caption": (12, 400, 1.4, 0.0),
    "button": (15, 600, 1.2, 0.0), "eyebrow": (13, 600, 1.3, 0.6),
    "mono": (13, 400, 1.5, 0.0),
}

ROUND_DEFAULTS = {"xs": "4px", "sm": "6px", "md": "8px", "lg": "12px",
                  "xl": "16px", "xxl": "24px", "pill": "9999px"}
SPACE_DEFAULTS = {"xxs": "4px", "xs": "8px", "sm": "12px", "md": "16px", "lg": "24px",
                  "xl": "32px", "xxl": "48px", "section": "96px"}


def pick(mapping, candidates):
    for c in candidates:
        if c in mapping and mapping[c]:
            return mapping[c]
    return None


def num(val, default=0.0):
    if val is None:
        return default
    m = re.search(r"-?\d+(\.\d+)?", str(val))
    return float(m.group()) if m else default


def mobile_size(px):
    """Fluid lower bound for a desktop type size."""
    if px >= 64:
        return max(34.0, px * 0.44)
    if px >= 40:
        return max(28.0, px * 0.58)
    if px >= 28:
        return px * 0.74
    if px >= 20:
        return px * 0.88
    return px


COLOUR_OK = re.compile(
    r"^(#[0-9a-fA-F]{3,8}|rgba?\([^)]*\)|hsla?\([^)]*\)|color\([^)]*\)|var\(--[^)]*\)"
    r"|transparent|currentColor|inherit|[a-z]+)$")


def assert_colour(slug, token, value):
    """A malformed colour is a silent failure — the declaration is simply dropped
    by the browser and the page renders with an unset variable."""
    if not COLOUR_OK.match(str(value).strip()):
        raise SystemExit(
            "%s: %s has a value that is not a colour: %r\n"
            "  (a YAML inline comment or stray text probably leaked into it)"
            % (slug, token, value))


def derive_tokens(slug):
    slug_hint = slug
    """Produce the canonical token CSS block for a slug from its reference file."""
    text, fm = read_reference(slug)
    colors = fm.get("colors", {}) or {}
    typo = fm.get("typography", {}) or {}
    rounded = fm.get("rounded", {}) or {}
    spacing = fm.get("spacing", {}) or {}

    lines = []
    lines.append("/* ---- colors ---- */")
    resolved = {}
    for canon, cands in COLOR_MAP.items():
        v = pick(colors, cands)
        if v:
            resolved[canon] = v
    # sensible derivations for anything unresolved
    resolved.setdefault("canvas", "#ffffff")
    resolved.setdefault("ink", "#111111")
    resolved.setdefault("surface", resolved["canvas"])
    resolved.setdefault("surface-2", resolved["surface"])
    resolved.setdefault("surface-3", resolved["surface-2"])
    resolved.setdefault("ink-muted", resolved["ink"])
    resolved.setdefault("ink-subtle", resolved["ink-muted"])
    resolved.setdefault("hairline", "rgba(128,128,128,.28)")
    resolved.setdefault("hairline-strong", resolved["hairline"])
    resolved.setdefault("primary", resolved["ink"])
    resolved.setdefault("on-primary", resolved["canvas"])
    resolved.setdefault("primary-hover", resolved["primary"])
    resolved.setdefault("primary-soft", resolved["primary"])
    resolved.setdefault("accent-2", resolved["primary"])
    resolved.setdefault("success", "#2f9e44")
    resolved.setdefault("warning", "#f08c00")
    resolved.setdefault("danger", "#e03131")
    resolved.setdefault("inverse-canvas", resolved["ink"])
    resolved.setdefault("inverse-ink", resolved["canvas"])
    for k, v in resolved.items():
        assert_colour(slug_hint, "--c-" + k, v)
        lines.append("  --c-%s: %s;" % (k, v))

    # every raw color from the reference, for the swatch appendix
    lines.append("/* ---- raw palette (spec appendix) ---- */")
    for k, v in colors.items():
        assert_colour(slug_hint, "--raw-" + k, v)
        lines.append("  --raw-%s: %s;" % (k, v))

    lines.append("/* ---- typography ---- */")
    fams = []
    for key in ("display-xl", "body", "mono"):
        step = pick(typo, TYPE_MAP[key]) or {}
        f = step.get("fontFamily") if isinstance(step, dict) else None
        fams.append(f)
    disp_f, body_f, mono_f = fams
    lines.append('  --font-display: %s;' % font_stack(disp_f, "sans"))
    lines.append('  --font-body: %s;' % font_stack(body_f or disp_f, "sans"))
    lines.append('  --font-mono: %s;' % font_stack(mono_f, "mono"))

    for canon, cands in TYPE_MAP.items():
        step = pick(typo, cands)
        d = TYPE_DEFAULTS[canon]
        if isinstance(step, dict):
            size = num(step.get("fontSize"), d[0])
            weight = int(num(step.get("fontWeight"), d[1]))
            lh = num(step.get("lineHeight"), d[2])
            ls = num(step.get("letterSpacing"), d[3])
        else:
            size, weight, lh, ls = d
        if lh > 4:  # a px line-height
            lh = round(lh / size, 3) if size else d[2]
        m = round(mobile_size(size), 1)
        # precomputed fluid clamp: CSS cannot divide length by length
        slope = (size - m) / (1440.0 - 375.0)
        y_int = m - slope * 375.0
        fs = ("clamp(%gpx, calc(%gpx + %gvw), %gpx)" % (m, round(y_int, 3), round(slope * 100, 4), size)
              if size != m else "%gpx" % size)
        lines.append("  --t-%s: %gpx; --t-%s-m: %gpx; --fs-%s: %s;"
                     % (canon, size, canon, m, canon, fs))
        ls_em = round(ls / size, 4) if size else 0  # em keeps tracking proportional when fluid
        lines.append("  --t-%s-w: %d; --t-%s-lh: %g; --t-%s-ls: %gem;"
                     % (canon, weight, canon, lh, canon, ls_em))

    lines.append("/* ---- shape & space ---- */")
    for k, dv in ROUND_DEFAULTS.items():
        lines.append("  --r-%s: %s;" % (k, rounded.get(k, dv)))
    for k, dv in SPACE_DEFAULTS.items():
        lines.append("  --s-%s: %s;" % (k, spacing.get(k, dv)))

    return ":root{\n" + "\n".join(lines) + "\n}\n"


GENERIC_SANS = ('-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, '
                '"Helvetica Neue", Arial, sans-serif')
GENERIC_MONO = 'ui-monospace, SFMono-Regular, "SF Mono", Menlo, Consolas, monospace'


def font_stack(name, kind):
    tail = GENERIC_MONO if kind == "mono" else GENERIC_SANS
    if not name:
        return tail
    name = str(name).strip().strip('"\'')
    if not name or name.lower() in ("inherit", "system"):
        return tail
    quoted = '"%s"' % name if " " in name else name
    return "%s, %s" % (quoted, tail)


def scaffold(slug):
    css = derive_tokens(slug)
    path = os.path.join(SRC, slug + ".tokens.css")
    os.makedirs(SRC, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("/* AUTO-DERIVED from design-md/%s.md — hand-tune freely. */\n%s" % (slug, css))
    text, fm = read_reference(slug)
    kind = "frontmatter" if fm else "PROSE (no frontmatter — tokens are defaults, tune by hand)"
    print("scaffolded %s  [%s]" % (path, kind))
    return path


# ---------------------------------------------------------------- rendering helpers

E = lambda s: html.escape(str(s), quote=True)
UNSPLASH = "https://images.unsplash.com/"


_IMG_BANK = None


def bank():
    global _IMG_BANK
    if _IMG_BANK is None:
        with open(os.path.join(SHARED, "images.json"), encoding="utf-8") as f:
            _IMG_BANK = json.load(f)
    return _IMG_BANK


def img(pid, alt=None, w=1200, h=None, cls="", ratio=None, lazy=True, sizes=None):
    """Responsive Unsplash <img>. Alt text defaults to the verified bank description
    so a page can never ship a caption that misdescribes the photo."""
    entry = bank().get(pid)
    if entry is None:
        raise SystemExit("image id not in shared/images.json: %s" % pid)
    alt = alt or entry["alt"]
    base = UNSPLASH + pid
    q = "&q=80&auto=format&fit=crop"
    widths = [w // 2, w, int(w * 1.5)]
    srcset = ", ".join("%s?w=%d%s %dw" % (base, x, q, x) for x in widths)
    h = h or (int(w * ratio) if ratio else int(w * 0.66))
    return ('<img class="%s" src="%s?w=%d%s" srcset="%s" sizes="%s" '
            'width="%d" height="%d" alt="%s"%s>') % (
        cls, base, w, q, srcset, sizes or "(max-width: 760px) 100vw, 50vw",
        w, h, E(alt), ' loading="lazy" decoding="async"' if lazy else '')


PH_WEIGHTS = ("thin", "light", "bold", "fill", "duotone")


def icon_weight(name):
    """Phosphor v2 encodes weight as a CLASS, not a name suffix:
    `ph-fill ph-cpu`, never `ph ph-cpu-fill`. Split the suffix off."""
    for w in PH_WEIGHTS:
        if name.endswith("-" + w):
            return w, name[: -(len(w) + 1)]
    return "regular", name


def icon(name, cls=""):
    w, base = icon_weight(name)
    weight_cls = "ph" if w == "regular" else "ph-" + w
    return '<i class="%s %s %s" aria-hidden="true"></i>' % (weight_cls, E(base), cls)


_PH_NAMES = None


def phosphor_names():
    global _PH_NAMES
    if _PH_NAMES is None:
        with open(os.path.join(SHARED, "phosphor-names.json"), encoding="utf-8") as f:
            _PH_NAMES = set(json.load(f))
    return _PH_NAMES


def check_icons(d, slug):
    """A misspelt icon name renders as nothing at all, silently. Catch it here
    against the 1,530 names in the Phosphor regular stylesheet."""
    names = [("brand.mark", d.get("brand", {}).get("mark", ""))]
    names += [("features[%d]" % i, f.get("icon", ""))
              for i, f in enumerate(d.get("features", {}).get("items", []))]
    names += [("showcases[%d].point_icon" % i, s.get("point_icon", ""))
              for i, s in enumerate(d.get("showcases", []))]
    bad = []
    for where, n in names:
        if not n:
            continue
        base = icon_weight(n)[1]
        if base.startswith("ph-"):
            base = base[3:]
        if base not in phosphor_names():
            bad.append("%s: %s" % (where, n))
    if bad:
        raise SystemExit("%s.json — unknown Phosphor icon(s):\n  %s" % (slug, "\n  ".join(bad)))


def icons_used(d):
    """Every Phosphor weight this page needs. `regular` is always included:
    the skeleton hard-codes `ph ph-arrow-left` and friends, and page.js swaps
    in `ph ph-x` — all of which need the regular stylesheet loaded."""
    names = [d.get("brand", {}).get("mark", "")]
    names += [f.get("icon", "") for f in d.get("features", {}).get("items", [])]
    names += [s.get("point_icon", "") for s in d.get("showcases", [])]
    weights = {"regular"}
    for n in names:
        if n:
            weights.add(icon_weight(n)[0])
    return sorted(weights)


def render_nav(d):
    links = "".join('<li><a href="#%s">%s</a></li>' % (E(l.get("href", "f")), E(l["label"]))
                    for l in d["nav"]["links"])
    return links


def render_logos(d):
    return "".join('<li class="logo-item">%s</li>' % E(x) for x in d.get("logos", []))


def render_features(d):
    out = []
    for i, f in enumerate(d["features"]["items"]):
        out.append(
            '<article class="feat-card reveal" style="--i:%d">'
            '<span class="feat-ico">%s</span>'
            '<h3 class="feat-title">%s</h3>'
            '<p class="feat-body">%s</p>'
            '</article>' % (i, icon(f["icon"]), E(f["title"]), E(f["body"])))
    return "".join(out)


def render_showcases(d):
    out = []
    for i, s in enumerate(d.get("showcases", [])):
        pts = "".join('<li>%s<span>%s</span></li>' % (icon(s.get("point_icon", "ph-check")), E(p))
                      for p in s.get("points", []))
        out.append(
            '<section class="showcase %s reveal" id="showcase-%d">'
            '<div class="sc-media">%s</div>'
            '<div class="sc-copy">'
            '<p class="eyebrow">%s</p><h2 class="sc-title">%s</h2>'
            '<p class="sc-body">%s</p><ul class="sc-points">%s</ul>'
            '<a class="btn btn-ghost" href="#pricing">%s %s</a>'
            '</div></section>' % (
                "sc-rev" if i % 2 else "", i,
                img(s["image"], s.get("alt"), w=1000, ratio=s.get("ratio", 0.72)),
                E(s.get("eyebrow", "")), E(s["title"]), E(s["body"]), pts,
                E(s.get("cta", "Learn more")), icon("ph-arrow-right")))
    return "".join(out)


def render_metrics(d):
    return "".join('<div class="metric reveal" style="--i:%d"><span class="metric-v">%s</span>'
                   '<span class="metric-l">%s</span></div>' % (i, E(m["v"]), E(m["l"]))
                   for i, m in enumerate(d.get("metrics", [])))


def render_gallery(d):
    g = d.get("gallery", {})
    out = []
    for i, it in enumerate(g.get("items", [])):
        out.append('<figure class="g-item reveal" style="--i:%d">%s'
                   '<figcaption>%s</figcaption></figure>'
                   % (i, img(it["id"], it.get("alt"), w=900, ratio=it.get("ratio", 1.0)),
                      E(it.get("tag", ""))))
    return "".join(out)


def render_pricing(d):
    out = []
    for t in d["pricing"]["tiers"]:
        feats = "".join('<li>%s<span>%s</span></li>' % (icon("ph-check"), E(x))
                        for x in t["features"])
        badge = '<span class="tier-badge">%s</span>' % E(t["badge"]) if t.get("badge") else ""
        out.append(
            '<article class="tier %s reveal">%s<h3 class="tier-name">%s</h3>'
            '<p class="tier-price"><span class="tier-num">%s</span>'
            '<span class="tier-per">%s</span></p>'
            '<p class="tier-desc">%s</p><ul class="tier-feats">%s</ul>'
            '<a class="btn %s" href="#cta">%s</a></article>' % (
                "tier-feat" if t.get("featured") else "", badge, E(t["name"]),
                E(t["price"]), E(t.get("period", "")), E(t["desc"]), feats,
                "btn-primary" if t.get("featured") else "btn-secondary", E(t["cta"])))
    return "".join(out)


def render_faq(d):
    return "".join(
        '<details class="faq-item"%s><summary><span>%s</span>'
        '<span class="faq-mk">%s</span></summary><div class="faq-a"><p>%s</p></div></details>'
        % (" open" if i == 0 else "", E(f["q"]), icon("ph-plus"), E(f["a"]))
        for i, f in enumerate(d["faq"]["items"]))


def render_footer(d):
    return "".join(
        '<div class="fcol"><h4>%s</h4><ul>%s</ul></div>'
        % (E(c["title"]), "".join('<li><a href="#f">%s</a></li>' % E(l) for l in c["links"]))
        for c in d["footer"]["columns"])


# ---------------------------------------------------------------- spec appendix

TYPE_SPECIMEN = ["display-xl", "display-lg", "display-md", "headline", "card-title",
                 "subhead", "body-lg", "body", "body-sm", "caption", "button",
                 "eyebrow", "mono"]


TOKEN_DOC = re.compile(r"\*\*(.+?)\*\*\s*\(\{colors\.([A-Za-z0-9_-]+)\}\)\s*:\s*(.+)")
HEX_DOC = re.compile(r"\*\*(.+?)\*\*\s*\(`(#[0-9a-fA-F]{3,8})`\)\s*:\s*(.+)")


FM_COMMENT = re.compile(r"^\s+([A-Za-z0-9_-]+):\s*(\"[^\"]*\"|'[^']*'|\S+)\s+#\s*(.+?)\s*$")


def frontmatter_comments(slug):
    """Some references document each token as a YAML inline comment
    (`primary: "#e60012"   # Nintendo Red - racetrack logo`). That is real usage
    documentation, so keep it rather than discarding it with the comment."""
    text, _ = read_reference(slug)
    if not text.startswith("---"):
        return {}
    end = text.find("\n---", 3)
    out = {}
    for line in text[3:end if end != -1 else None].split("\n"):
        m = FM_COMMENT.match(line)
        if m:
            out[m.group(1).lower()] = m.group(3)
    return out


def colour_docs(slug):
    """Friendly name + usage note per colour, mined from the reference prose.
    Keyed by token name and by hex so both reference formats resolve."""
    text, _ = read_reference(slug)
    docs = {}
    for line in text.split("\n"):
        for rx in (TOKEN_DOC, HEX_DOC):
            m = rx.search(line)
            if m:
                label, key, note = m.group(1), m.group(2), m.group(3)
                note = re.sub(r"\{[a-z]+\.([a-z0-9-]+)\}", r"\1", note).strip().rstrip(".")
                docs[key.lower()] = (label.strip(), note)
                break
    return docs


def render_swatches(d, slug):
    """Click-to-copy swatch grid: friendly name, hex, and what it is actually for."""
    docs = colour_docs(slug)
    pal = d.get("palette")
    if not pal:
        _, fm = read_reference(slug)
        pal = [{"name": k, "value": v} for k, v in (fm.get("colors", {}) or {}).items()]
    fmc = frontmatter_comments(slug)
    for p in pal:
        doc = docs.get(p["name"].lower()) or docs.get(str(p["value"]).lower())
        if doc and not p.get("note"):
            p["label"], p["note"] = doc[0], doc[1]
        # fall back to the token's own YAML inline comment
        if not p.get("note"):
            c = fmc.get(p["name"].lower())
            if c:
                p["note"] = c
    out = []
    for p in pal:
        val = p["value"]
        note = p.get("note", "")
        out.append(
            '<button class="sw" type="button" data-copy="%s" '
            'aria-label="Copy %s, %s"%s>'
            '<span class="sw-chip" style="background:%s"></span>'
            '<span class="sw-meta"><span class="sw-name">%s</span>'
            '<span class="sw-val">%s</span>%s</span></button>'
            % (E(val), E(p.get("label", p["name"])), E(val),
               ' title="%s"' % E(note) if note else "",
               E(val), E(p.get("label", p["name"])), E(val),
               '<span class="sw-note">%s</span>' % E(note) if note else ""))
    return "".join(out)


def render_typescale(d):
    out = []
    for k in TYPE_SPECIMEN:
        out.append(
            '<div class="ts-row"><div class="ts-meta"><code>%s</code>'
            '<span class="ts-num">var(--t-%s)</span></div>'
            '<div class="ts-sample t-%s">%s</div></div>'
            % (E(k), E(k), E(k), E(d.get("specimen", "The quick brown fox")) if k.startswith("display") or k in ("headline", "card-title") else "Aa Bb Cc 0123 &mdash; the quick brown fox"))
    return "".join(out)


def render_scales():
    r = "".join('<div class="sc-chip"><span class="sc-box" style="border-radius:var(--r-%s)"></span>'
                '<code>--r-%s</code></div>' % (k, k) for k in ROUND_DEFAULTS)
    s = "".join('<div class="sp-row"><code>--s-%s</code>'
                '<span class="sp-bar" style="width:var(--s-%s)"></span></div>' % (k, k)
                for k in SPACE_DEFAULTS)
    return r, s


# ---------------------------------------------------------------- page composer

ENTITY = re.compile(r"&(?:[a-zA-Z]+|#\d+);")


def load_json(slug):
    with open(os.path.join(SRC, slug + ".json"), encoding="utf-8") as f:
        raw = f.read()
    # Most fields are HTML-escaped on the way out, so an entity here renders
    # literally ("&middot;"). Pages are UTF-8 — use the real character instead.
    # `hero.title` is intentionally raw HTML and is the one exemption.
    probe = json.loads(raw)
    title = probe.get("hero", {}).get("title", "")
    for m in ENTITY.finditer(raw):
        if m.group() not in title:
            raise SystemExit(
                "%s.json: HTML entity %s in an escaped field — use the literal character"
                % (slug, m.group()))
    return probe


def read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


PH_BASE = "https://cdn.jsdelivr.net/npm/@phosphor-icons/web@2.1.2/src/%s/style.css"


def build_page(slug):
    d = load_json(slug)
    skeleton = read(os.path.join(SHARED, "skeleton.html"))
    base_css = read(os.path.join(SHARED, "base.css"))
    tokens_css = read(os.path.join(SRC, slug + ".tokens.css"))
    design_css = read(os.path.join(SRC, slug + ".css"))
    page_js = read(os.path.join(SHARED, "page.js"))
    a11y_css = read(os.path.join(SHARED, "a11y.css"))

    fonts = d.get("fonts", {})
    font_override = ""
    if fonts:
        decl = []
        for k, var in (("display", "--font-display"), ("body", "--font-body"),
                       ("mono", "--font-mono")):
            if fonts.get(k):
                decl.append("  %s: %s;" % (var, fonts[k]))
        if decl:
            font_override = ":root{\n" + "\n".join(decl) + "\n}\n"

    # derived from the icons actually used, so a page can never reference a
    # weight whose stylesheet it forgot to load
    check_icons(d, slug)
    weights = sorted(set(icons_used(d)) | set(d.get("icon_weights", [])) | {"regular"})
    head_links = ['<link rel="stylesheet" href="%s">' % (PH_BASE % w) for w in weights]
    if fonts.get("google"):
        head_links.insert(0, '<link rel="preconnect" href="https://fonts.googleapis.com">'
                             '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
                             '<link rel="stylesheet" href="%s">' % fonts["google"])

    radii, spaces = render_scales()
    hero = d["hero"]
    hero_img = img(hero["image"], hero.get("alt"), w=1400, ratio=hero.get("ratio", 0.7),
                   lazy=False, sizes="(max-width: 900px) 100vw, 60vw") if hero.get("image") else ""
    t = d["testimonial"]

    repl = {
        "TITLE": "%s — Design Template" % d["name"],
        "DESC": "%s design language, rendered as a complete responsive page template." % d["name"],
        "HEAD_LINKS": "".join(head_links),
        # a11y last: the design layer may restyle it but cannot undercut it
        "CSS": (base_css + "\n" + tokens_css + "\n" + font_override + "\n"
                + design_css + "\n" + a11y_css),
        "JS": page_js,
        "SLUG": d["slug"], "NAME": d["name"], "CATEGORY": d["category"], "LOOK": d["look"],
        "SCHEME": d.get("scheme", "dark"),
        "V_NAV": d["variants"].get("nav", "bar"),
        "V_HERO": d["variants"].get("hero", "split"),
        "V_FEAT": d["variants"].get("features", "grid"),
        "V_CARD": d["variants"].get("cards", "bordered"),
        "V_GAL": d["variants"].get("gallery", "grid"),
        "BRAND_MARK": icon(d["brand"]["mark"], "brand-ico"),
        "BRAND_NAME": E(d["brand"]["name"]),
        "NAV_LINKS": render_nav(d),
        "NAV_CTA": E(d["nav"]["cta"]),
        "NAV_CTA2": E(d["nav"].get("cta2", "Sign in")),
        "HERO_EYEBROW": E(hero.get("eyebrow", "")),
        "HERO_TITLE": hero["title"],
        "HERO_SUB": E(hero["sub"]),
        "HERO_CTA1": E(hero["cta1"]), "HERO_CTA2": E(hero["cta2"]),
        "HERO_IMG": hero_img,
        "HERO_STATS": "".join('<div class="hstat"><b>%s</b><span>%s</span></div>'
                              % (E(s["v"]), E(s["l"])) for s in hero.get("stats", [])),
        "LOGO_LEAD": E(d.get("logo_lead", "Trusted by teams everywhere")),
        "LOGOS": render_logos(d),
        "FEAT_EYEBROW": E(d["features"].get("eyebrow", "")),
        "FEAT_TITLE": E(d["features"]["title"]),
        "FEAT_SUB": E(d["features"].get("sub", "")),
        "FEATURES": render_features(d),
        "SHOWCASES": render_showcases(d),
        "METRICS": render_metrics(d),
        "METRIC_LEAD": E(d.get("metric_lead", "")),
        "GAL_TITLE": E(d.get("gallery", {}).get("title", "")),
        "GAL_SUB": E(d.get("gallery", {}).get("sub", "")),
        "GALLERY": render_gallery(d),
        "QUOTE": E(t["quote"]), "Q_NAME": E(t["name"]), "Q_ROLE": E(t["role"]),
        "Q_AVATAR": img(t["avatar"], "Portrait of %s" % t["name"], w=160, ratio=1.0,
                        cls="q-av", sizes="72px"),
        "PRICE_TITLE": E(d["pricing"]["title"]), "PRICE_SUB": E(d["pricing"].get("sub", "")),
        "TIERS": render_pricing(d),
        "FAQ_TITLE": E(d["faq"]["title"]),
        "FAQS": render_faq(d),
        "CTA_TITLE": E(d["cta"]["title"]), "CTA_SUB": E(d["cta"]["sub"]),
        "CTA_B1": E(d["cta"]["btn1"]), "CTA_B2": E(d["cta"]["btn2"]),
        "FOOT_TAG": E(d["footer"]["tagline"]),
        "FOOT_COLS": render_footer(d),
        "FOOT_LEGAL": E(d["footer"]["legal"]),
        "SWATCHES": render_swatches(d, slug),
        "TYPESCALE": render_typescale(d),
        "RADII": radii, "SPACES": spaces,
        "NOTES": "".join("<li>%s</li>" % E(n) for n in d.get("notes", [])),
    }
    page = skeleton
    for k, v in repl.items():
        page = page.replace("{{%s}}" % k, str(v))
    left = re.findall(r"\{\{([A-Z_0-9]+)\}\}", page)
    if left:
        raise SystemExit("unfilled placeholders in %s: %s" % (slug, sorted(set(left))))
    os.makedirs(OUT, exist_ok=True)
    dest = os.path.join(OUT, slug + ".html")
    with open(dest, "w", encoding="utf-8") as f:
        f.write(page)
    return dest, len(page)


# ---------------------------------------------------------------- catalog + index

SKILL_MD = os.path.expanduser("~/.claude/skills/design-md/SKILL.md")


def hex_lum(h):
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    if len(h) != 6:
        return 1.0
    try:
        r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    except ValueError:
        return 1.0
    f = lambda c: c / 12.92 if c <= .03928 else ((c + .055) / 1.055) ** 2.4
    return .2126 * f(r) + .7152 * f(g) + .0722 * f(b)


def catalog():
    """All 74 designs: slug, name, category, look, preview colours, scheme."""
    md = read(SKILL_MD)
    cat, rows = None, []
    for line in md.split("\n"):
        m = re.match(r"^###\s+(.+)$", line)
        if m:
            cat = m.group(1).strip()
            continue
        m = re.match(r"^\|\s*`([^`]+)`\s*\|\s*(.+?)\s*\|$", line)
        if m and cat:
            rows.append({"slug": m.group(1), "category": cat, "look": m.group(2)})

    for r in rows:
        text, fm = read_reference(r["slug"])
        colors = fm.get("colors", {}) or {}
        if colors:
            g = lambda cands, dv: pick(colors, cands) or dv
            r["canvas"] = g(COLOR_MAP["canvas"], "#ffffff")
            r["surface"] = g(COLOR_MAP["surface"], r["canvas"])
            r["ink"] = g(COLOR_MAP["ink"], "#111111")
            r["primary"] = g(COLOR_MAP["primary"], r["ink"])
            r["hairline"] = g(COLOR_MAP["hairline"], "rgba(128,128,128,.3)")
        else:
            hexes = re.findall(r"#[0-9a-fA-F]{6}", text)
            uniq = list(dict.fromkeys(hexes))
            darks = [h for h in uniq if hex_lum(h) < .2]
            lights = [h for h in uniq if hex_lum(h) > .8]
            mids = [h for h in uniq if .2 <= hex_lum(h) <= .8]
            r["canvas"] = (darks or lights or uniq or ["#ffffff"])[0]
            dark = hex_lum(r["canvas"]) < .35
            r["surface"] = (darks[1:2] or [r["canvas"]])[0] if dark else (lights[1:2] or [r["canvas"]])[0]
            r["ink"] = (lights or ["#ffffff"])[0] if dark else (darks or ["#111111"])[0]
            r["primary"] = (mids or uniq or ["#888888"])[0]
            r["hairline"] = "rgba(128,128,128,.32)"
        r["scheme"] = "dark" if hex_lum(r["canvas"]) < .35 else "light"
        # a built design owns its display name; otherwise clean up the reference's
        jf = os.path.join(SRC, r["slug"] + ".json")
        nm = ""
        if os.path.exists(jf):
            with open(jf, encoding="utf-8") as f:
                nm = json.load(f).get("name", "")
        if not nm:
            nm = re.sub(r"[-_]?(design[-_]analysis|inspired|design[-_]system)", "", 
                        fm.get("name", ""), flags=re.I).strip(" -_")
        r["name"] = nm or r["slug"].replace(".app", "").replace(".ai", "").replace("-", " ").title()
        r["built"] = os.path.exists(os.path.join(OUT, r["slug"] + ".html"))
    return rows


def build_index():
    rows = catalog()
    cats = list(dict.fromkeys(r["category"] for r in rows))
    # built pages lead — the queued ones are a roadmap, not the product
    order = {c: i for i, c in enumerate(cats)}
    rows.sort(key=lambda r: (not r["built"], order[r["category"]], r["name"].lower()))
    built = sum(1 for r in rows if r["built"])

    chips = ['<button class="chip is-on" type="button" data-cat="all">All'
             '<span class="chip-n">%d</span></button>' % len(rows)]
    for c in cats:
        n = sum(1 for r in rows if r["category"] == c)
        chips.append('<button class="chip" type="button" data-cat="%s">%s'
                     '<span class="chip-n">%d</span></button>' % (E(c), E(c), n))

    cards = []
    for r in rows:
        href = "designs/%s.html" % r["slug"]
        tag = ('<span class="badge badge-on">Ready</span>' if r["built"]
               else '<span class="badge">Queued</span>')
        prev = (
            '<span class="pv" style="--pv-bg:%s;--pv-sf:%s;--pv-ink:%s;--pv-ac:%s;--pv-hl:%s">'
            '<span class="pv-bar"><i></i><i></i><i></i></span>'
            '<span class="pv-h"></span><span class="pv-t"></span><span class="pv-t pv-t2"></span>'
            '<span class="pv-row"><span class="pv-btn"></span><span class="pv-pill"></span></span>'
            '<span class="pv-cards"><i></i><i></i><i></i></span></span>'
        ) % (E(r["canvas"]), E(r["surface"]), E(r["ink"]), E(r["primary"]), E(r["hairline"]))
        el = "a" if r["built"] else "div"
        attrs = ' href="%s"' % href if r["built"] else ' aria-disabled="true"'
        cards.append(
            '<%s class="card%s"%s data-cat="%s" data-scheme="%s" '
            'data-q="%s">%s'
            '<span class="card-body"><span class="card-top">'
            '<span class="card-name">%s</span>%s</span>'
            '<span class="card-look">%s</span>'
            '<span class="card-foot"><code>%s</code>'
            '<span class="dots"><i style="background:%s"></i><i style="background:%s"></i>'
            '<i style="background:%s"></i></span></span></span></%s>'
            % (el, "" if r["built"] else " card-off", attrs, E(r["category"]), E(r["scheme"]),
               E((r["slug"] + " " + r["name"] + " " + r["look"] + " " + r["category"]).lower()),
               prev, E(r["name"]), tag, E(r["look"]), E(r["slug"]),
               E(r["canvas"]), E(r["primary"]), E(r["ink"]), el))

    tpl = read(os.path.join(SHARED, "index.html"))
    page = (tpl.replace("{{CHIPS}}", "".join(chips))
               .replace("{{CARDS}}", "".join(cards))
               .replace("{{TOTAL}}", str(len(rows)))
               .replace("{{BUILT}}", str(built))
               .replace("{{CATS}}", str(len(cats)))
               .replace("{{CSS}}", read(os.path.join(SHARED, "index.css")))
               .replace("{{JS}}", read(os.path.join(SHARED, "index.js"))))
    dest = os.path.join(ROOT, "index.html")
    with open(dest, "w", encoding="utf-8") as f:
        f.write(page)
    print("built index.html  (%d designs, %d ready)" % (len(rows), built))
    return dest


# ---------------------------------------------------------------- cli

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return
    cmd = sys.argv[1]
    if cmd == "scaffold":
        for s in sys.argv[2:]:
            scaffold(s)
    elif cmd == "page":
        for s in sys.argv[2:]:
            dest, n = build_page(s)
            print("built %-28s %6.1f KB" % (os.path.basename(dest), n / 1024))
    elif cmd == "all":
        slugs = sorted(f[:-5] for f in os.listdir(SRC) if f.endswith(".json"))
        for s in slugs:
            dest, n = build_page(s)
            print("built %-28s %6.1f KB" % (os.path.basename(dest), n / 1024))
        build_index()
    elif cmd == "index":
        build_index()
    elif cmd == "artifact":
        build_artifact()
    elif cmd == "catalog":
        for r in catalog():
            print("%-16s %-26s %-8s %s" % (r["slug"], r["category"][:24], r["scheme"], r["canvas"]))
    else:
        print(__doc__)



# ---------------------------------------------------------------- artifact data

def artifact_data():
    """Full token spec for all 74 designs, for the standalone shareable catalog."""
    out = []
    for r in catalog():
        text, fm = read_reference(r["slug"])
        docs = colour_docs(r["slug"])
        colors = fm.get("colors", {}) or {}
        jf = os.path.join(SRC, r["slug"] + ".json")
        pal = None
        if os.path.exists(jf):
            with open(jf, encoding="utf-8") as f:
                pal = json.load(f).get("palette")
        if pal:
            swatches = [{"n": p.get("label", p["name"]), "v": p["value"], "u": p.get("note", "")}
                        for p in pal]
        else:
            swatches = []
            for k, v in colors.items():
                d = docs.get(k.lower()) or docs.get(str(v).lower())
                swatches.append({"n": d[0] if d else k, "v": v, "u": d[1] if d else ""})

        typo = fm.get("typography", {}) or {}
        scale = []
        for canon in ("display-xl", "display-lg", "headline", "body", "caption", "button", "mono"):
            step = pick(typo, TYPE_MAP[canon])
            if isinstance(step, dict):
                scale.append({"k": canon,
                              "s": str(step.get("fontSize", "")),
                              "w": str(step.get("fontWeight", "")),
                              "f": str(step.get("fontFamily", ""))})
        rounded = fm.get("rounded", {}) or {}
        out.append({
            "slug": r["slug"], "name": r["name"], "cat": r["category"], "look": r["look"],
            "scheme": r["scheme"], "built": r["built"],
            "bg": r["canvas"], "sf": r["surface"], "ink": r["ink"],
            "ac": r["primary"], "hl": r["hairline"],
            "sw": swatches, "ty": scale,
            "rd": [{"k": k, "v": v} for k, v in rounded.items()],
        })
    return out


def build_artifact():
    data = artifact_data()
    tpl = read(os.path.join(SHARED, "artifact.html"))
    # replace the whole placeholder-plus-literal, else it emits `[...][]`
    page = tpl.replace("/*{{DATA}}*/[]", json.dumps(data, separators=(",", ":")))
    if "{{DATA}}" in page:
        raise SystemExit("artifact data placeholder not substituted")
    dest = os.path.join(ROOT, "tools", "library-artifact.html")
    with open(dest, "w", encoding="utf-8") as f:
        f.write(page)
    print("built %s (%.1f KB, %d designs)" % (dest, os.path.getsize(dest) / 1024, len(data)))
    return dest

if __name__ == "__main__":
    main()
