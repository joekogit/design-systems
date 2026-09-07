"""Assemble a design's content JSON from its distinctive parts.

The scaffolding (nav link objects, metric objects, gallery item objects) has the
same shape for every design, so only the parts that actually differ are written
by hand. Import from the project root: `from tools.mkdesign import *`
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOGOS = ["Northwind", "Corva", "Tessera", "Basisplan", "Perigee", "Halyard"]


def tier(name, price, period, desc, feats, cta, featured=False, badge=None):
    t = {"name": name, "price": price, "period": period, "desc": desc,
         "features": feats, "cta": cta}
    if featured:
        t["featured"] = True
    if badge:
        t["badge"] = badge
    return t


def show(eyebrow, title, body, points, image, cta, ratio=None):
    s = {"eyebrow": eyebrow, "title": title, "body": body, "points": points,
         "image": image, "cta": cta}
    if ratio:
        s["ratio"] = ratio
    return s


def hero(eyebrow, title, sub, cta1, cta2, image, stats, ratio=0.64):
    return {"eyebrow": eyebrow, "title": title, "sub": sub, "cta1": cta1,
            "cta2": cta2, "image": image, "ratio": ratio,
            "stats": [{"v": v, "l": l} for v, l in stats]}


def fonts(display, body, mono, google):
    return {"display": display, "body": body, "mono": mono, "google": google}


def design(**k):
    d = {
        "slug": k["slug"], "name": k["name"], "category": k["cat"], "look": k["look"],
        "scheme": k["scheme"], "icon_weights": k.get("weights", ["regular"]),
        "fonts": k["fonts"], "variants": k["variants"],
        "brand": {"mark": k["mark"], "name": k["brand"]},
        "nav": {"links": [{"label": l, "href": h} for l, h in k["nav"]],
                "cta": k["cta"], "cta2": k.get("cta2", "Sign in")},
        "hero": k["hero"],
        "logo_lead": k.get("logo_lead", "Trusted by teams everywhere"),
        "logos": k.get("logos", LOGOS),
        "features": {"eyebrow": k["feat"][0], "title": k["feat"][1], "sub": k["feat"][2],
                     "items": [{"icon": i, "title": t, "body": b} for i, t, b in k["items"]]},
        "showcases": k["shows"],
        "metric_lead": k.get("metric_lead", ""),
        "metrics": [{"v": v, "l": l} for v, l in k["metrics"]],
        "gallery": {"title": k["gal"][0], "sub": k["gal"][1],
                    "items": [{"id": i, "tag": t, "ratio": r} for i, t, r in k["gal"][2]]},
        "testimonial": {"quote": k["quote"][0], "name": k["quote"][1],
                        "role": k["quote"][2], "avatar": k["quote"][3]},
        "pricing": {"title": k["price"][0], "sub": k["price"][1], "tiers": k["tiers"]},
        "faq": {"title": k["faq"][0], "items": [{"q": q, "a": a} for q, a in k["faq"][1]]},
        "cta": {"title": k["ctab"][0], "sub": k["ctab"][1], "btn1": k["ctab"][2], "btn2": k["ctab"][3]},
        "footer": {"tagline": k["foot"][0],
                   "columns": [{"title": t, "links": ls} for t, ls in k["foot"][1]],
                   "legal": k["foot"][2]},
        "specimen": k["specimen"], "notes": k["notes"],
    }
    if k.get("palette"):
        d["palette"] = k["palette"]
    path = os.path.join(ROOT, "src", k["slug"] + ".json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    return k["slug"]
