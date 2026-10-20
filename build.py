"""Build methods_catalog.html from methods/*.yml, sections.yml and site.yml.

    python build.py            # validate, report translation coverage, write the page
    python build.py --check    # validate only
    python build.py --out _site/index.html   # write somewhere else (used by the GitHub Action)
    python build.py --private  # local only: also include private/methods/

One YAML file per method in methods/ (files starting with "_" are ignored, e.g. _template.yml).
private/ is git-ignored: content that must not be public yet (e.g. from a competition that is still
running). A private file with the same name as a public one replaces it in --private builds.
Sections and subsections with no methods are left out of the page.
Any language listed in site.yml can be added under `translations:` in a method file; a method
without a translation for the selected language is shown in English.
"""
import html
import json
import re
import sys
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "methods_catalog.html"
PRIVATE = "--private" in sys.argv
GRADES = ("book", "good", "brilliant")
METHOD_KEYS = {"section", "subsection", "order", "grade", "name", "description", "sketch", "code", "translations"}
TRANSLATABLE = {"name", "description", "code"}


def load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def t(value, lang):
    """Pick a language from a {lang: text} map, falling back to English."""
    if isinstance(value, dict):
        return value.get(lang) or value["en"]
    return value


def inline_md(text):
    out = markdown.markdown(text or "").strip()
    return re.sub(r"^<p>(.*)</p>$", r"\1", out, flags=re.S)


# ---------------------------------------------------------------- loading + validation
def load():
    site = load_yaml(ROOT / "site.yml")
    sections = load_yaml(ROOT / "sections.yml")
    langs = list(site["languages"])
    errors, warnings = [], []

    known = {}
    for s in sections:
        known[s["id"]] = {sub["id"] for sub in s.get("subsections", [])}

    files = {p.stem: p for p in sorted((ROOT / "methods").glob("*.yml")) if not p.name.startswith("_")}
    if PRIVATE:
        files.update({p.stem: p for p in sorted((ROOT / "private" / "methods").glob("*.yml"))
                      if not p.name.startswith("_")})
    methods = []
    for slug, path in sorted(files.items()):
        try:
            m = load_yaml(path) or {}
        except yaml.YAMLError as e:
            errors.append(f"{path.name}: invalid YAML: {e}")
            continue
        where = path.name
        for key in ("section", "grade", "name"):
            if not m.get(key):
                errors.append(f"{where}: missing required `{key}`")
        for key in set(m) - METHOD_KEYS:
            warnings.append(f"{where}: unknown key `{key}` (ignored)")
        if m.get("grade") and m["grade"] not in GRADES:
            errors.append(f"{where}: grade must be one of {GRADES}, got {m['grade']!r}")
        sec, sub = m.get("section"), m.get("subsection")
        if sec and sec not in known:
            errors.append(f"{where}: unknown section {sec!r} (see sections.yml)")
        elif sec and known[sec] and sub not in known[sec]:
            errors.append(f"{where}: section {sec!r} needs a subsection from {sorted(known[sec])}, got {sub!r}")
        elif sec and not known[sec] and sub:
            errors.append(f"{where}: section {sec!r} has no subsections, remove `subsection`")
        for lang, tr in (m.get("translations") or {}).items():
            if lang not in langs:
                errors.append(f"{where}: translation language {lang!r} is not listed in site.yml")
            for key in set(tr or {}) - TRANSLATABLE:
                errors.append(f"{where}: translations.{lang}.{key} is not translatable (allowed: {sorted(TRANSLATABLE)})")
        m["id"] = slug
        m.setdefault("order", 1000)
        methods.append(m)

    seen = {}
    for m in methods:
        key = (m.get("section"), m.get("subsection"), m["order"])
        if key in seen:
            warnings.append(f"{m['id']}.yml and {seen[key]}.yml share order {m['order']} in {key[0]}/{key[1]}")
        seen[key] = m["id"]
    return site, sections, methods, errors, warnings


def localized(m, lang):
    """Method fields in `lang`, falling back to English per method, then per field."""
    tr = (m.get("translations") or {}).get(lang) if lang != "en" else None
    fields = {k: m.get(k) for k in TRANSLATABLE}
    if tr:
        fields.update({k: v for k, v in tr.items() if v})
    fields["fallback"] = lang != "en" and not tr
    return fields


# ---------------------------------------------------------------- rendering
def render_method(m, lang, site, ids):
    f = localized(m, lang)
    ui = site["ui"]
    label = t(site["grade_labels"][m["grade"]], lang)
    name = inline_md(f["name"]).rstrip(".")
    parts = [f'<span class="badge {m["grade"]}">{html.escape(label)}</span> <strong>{name}</strong>']
    parts.append(". " + inline_md(f["description"]) if f["description"] else ".")
    if f["fallback"]:
        parts.append(f' <span class="fallback" title="{html.escape(t(ui["untranslated"], lang))}">EN</span>')
    out = [f'<div class="method" data-grade="{m["grade"]}" id="{ids(m["id"])}"><p>{"".join(parts)}</p>']
    if f["code"]:
        sketch = bool(m.get("sketch"))
        summary = t(ui["sketch" if sketch else "code"], lang)
        note = f' <span class="note">· {html.escape(t(ui["sketch_note"], lang))}</span>' if sketch else ""
        out.append(f'<details class="snippet"><summary>{html.escape(summary)}{note}</summary>'
                   f'<pre><code class="language-python">{html.escape(f["code"].rstrip())}</code></pre></details>')
    out.append("</div>")
    return "".join(out)


def render_lang(lang, site, sections, methods):
    pid = lambda x: f"{lang}-{x}"
    body, nav = [], []
    body.append(f"<h1>{html.escape(t(site['title'], lang))}</h1>")
    body.append(f"<p>{inline_md(t(site['intro'], lang))}</p>")
    body.append(f"<p><strong>{html.escape(t(site['grades_heading'], lang))}</strong></p><ul class='legend'>")
    for g in GRADES:
        body.append(f'<li><span class="badge {g}">{html.escape(t(site["grade_labels"][g], lang))}</span>: '
                    f"{inline_md(t(site['grades'][g], lang))}</li>")
    body.append("</ul>")

    # drop empty sections/subsections so numbering stays continuous
    used = {(m["section"], m.get("subsection")) for m in methods}
    visible = []
    for s in sections:
        subs = [sub for sub in s.get("subsections", []) if (s["id"], sub["id"]) in used]
        if (s["id"], None) in used or subs:
            visible.append({**s, "subsections": subs} if s.get("subsections") else s)
    sections = visible

    numbers = {}
    for i, s in enumerate(sections, 1):
        title = f"{i}. {t(s['title'], lang)}"
        body.append(f'<h2 id="{pid(s["id"])}">{html.escape(title)}</h2>')
        nav.append(f'<a class="l2" href="#{pid(s["id"])}">{html.escape(title)}</a>')
        groups = [(None, None)] if not s.get("subsections") else [(sub, f"{i}.{j}") for j, sub in enumerate(s["subsections"], 1)]
        for sub, num in groups:
            sub_id = sub["id"] if sub else None
            if sub:
                anchor = pid(f'{s["id"]}--{sub_id}')
                title = f"{num} {t(sub['title'], lang)}"
                body.append(f'<h3 id="{anchor}">{html.escape(title)}</h3>')
                nav.append(f'<a class="l3" href="#{anchor}">{html.escape(title)}</a>')
            items = sorted((m for m in methods if m["section"] == s["id"] and m.get("subsection") == sub_id),
                           key=lambda m: (m["order"], m["id"]))
            for m in items:
                numbers[m["id"]] = num or str(i)
                body.append(render_method(m, lang, site, lambda x: pid("m-" + x)))

    brilliant = [m for m in methods if m["grade"] == "brilliant"]
    if brilliant:
        body.append(f'<h2 id="{pid("brilliant")}">{html.escape(t(site["brilliant_heading"], lang))}</h2><ol>')
        nav.append(f'<a class="l2" href="#{pid("brilliant")}">{html.escape(t(site["brilliant_heading"], lang))}</a>')
        for m in sorted(brilliant, key=lambda m: numbers.get(m["id"], "")):
            body.append(f'<li><a href="#{pid("m-" + m["id"])}">{inline_md(localized(m, lang)["name"])}</a> '
                        f'(§{numbers.get(m["id"], "?")})</li>')
        body.append("</ol>")
    return "\n".join(body), "\n".join(nav)


def build(write=True):
    site, sections, methods, errors, warnings = load()
    for w in warnings:
        print("warning:", w)
    if errors:
        for e in errors:
            print("error:", e)
        sys.exit(1)

    langs = list(site["languages"])
    for lang in langs[1:]:
        done = sum(1 for m in methods if (m.get("translations") or {}).get(lang))
        print(f"{lang}: {done}/{len(methods)} methods translated")
    if not write:
        print(f"ok: {len(methods)} methods")
        return

    panes, navs = [], []
    for lang in langs:
        body, nav = render_lang(lang, site, sections, methods)
        panes.append(f'<div class="pane" data-lang="{lang}" lang="{lang}">{body}</div>')
        navs.append(f'<nav class="pane" data-lang="{lang}">{nav}</nav>')
    ui = {lang: {k: t(v, lang) for k, v in site["ui"].items()} for lang in langs}
    for lang in langs:
        ui[lang]["grades"] = {g: t(site["grade_labels"][g], lang) for g in GRADES}
        ui[lang]["title"] = t(site["title"], lang)
    options = "".join(f'<option value="{l}">{html.escape(name)}</option>' for l, name in site["languages"].items())
    page = (TEMPLATE.replace("{{PANES}}", "\n".join(panes)).replace("{{NAVS}}", "\n".join(navs))
            .replace("{{LANG_OPTIONS}}", options).replace("{{UI}}", json.dumps(ui, ensure_ascii=False))
            .replace("{{DEFAULT_LANG}}", langs[0]).replace("{{TITLE}}", html.escape(t(site["title"], "en"))))
    out = Path(sys.argv[sys.argv.index("--out") + 1]) if "--out" in sys.argv else OUT
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    print(f"wrote {out}: {len(methods)} methods, {len(langs)} languages")


TEMPLATE = (ROOT / "template.html").read_text(encoding="utf-8") if (ROOT / "template.html").exists() else ""

if __name__ == "__main__":
    build(write="--check" not in sys.argv)
