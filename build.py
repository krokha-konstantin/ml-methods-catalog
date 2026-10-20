"""Build methods_catalog.html from methods/*.yml, sections.yml, site.yml and glossary.yml.

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
Glossary terms (glossary.yml) are marked on their first mention in each method and listed at the end.
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
SLOTS = ("when", "do", "why")
METHOD_KEYS = {"section", "subsection", "order", "grade", "name", *SLOTS, "see_also", "sketch", "code", "translations"}
TRANSLATABLE = {"name", *SLOTS, "code"}


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
    glossary = load_yaml(ROOT / "glossary.yml") or []
    langs = list(site["languages"])
    errors, warnings = [], []

    known = {}
    for s in sections:
        known[s["id"]] = {sub["id"] for sub in s.get("subsections", [])}

    files = {p.stem: p for p in sorted((ROOT / "methods").glob("*.yml")) if not p.name.startswith("_")}
    private_files = {p.stem: p for p in sorted((ROOT / "private" / "methods").glob("*.yml"))
                     if not p.name.startswith("_")}
    if PRIVATE:
        files.update(private_files)
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
        if not m.get("do"):
            warnings.append(f"{where}: no `do` text, only the name will be shown")
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

    ids = {m["id"] for m in methods}
    for m in methods:
        for ref in m.get("see_also") or []:
            if ref not in ids and ref not in private_files:
                errors.append(f"{m['id']}.yml: see_also refers to unknown method {ref!r}")
        m["see_also"] = [ref for ref in m.get("see_also") or [] if ref in ids]   # private links drop out of public builds

    for g in glossary:
        for key in ("term", "match", "def"):
            if not g.get(key):
                errors.append(f"glossary.yml: entry {g.get('term')!r} is missing `{key}`")
        for pats in (g.get("match") or {}).values():
            for pat in pats:
                try:
                    re.compile(pat)
                except re.error as e:
                    errors.append(f"glossary.yml: bad pattern {pat!r}: {e}")

    seen = {}
    for m in methods:
        key = (m.get("section"), m.get("subsection"), m["order"])
        if key in seen:
            warnings.append(f"{m['id']}.yml and {seen[key]}.yml share order {m['order']} in {key[0]}/{key[1]}")
        seen[key] = m["id"]
    return site, sections, methods, glossary, errors, warnings


def localized(m, lang):
    """Method fields in `lang`, falling back to English per method, then per field."""
    tr = (m.get("translations") or {}).get(lang) if lang != "en" else None
    fields = {k: m.get(k) for k in TRANSLATABLE}
    if tr:
        fields.update({k: v for k, v in tr.items() if v})
    fields["fallback"] = lang != "en" and not tr
    return fields


# ---------------------------------------------------------------- glossary terms
def term_matchers(glossary, lang):
    """[(index, regex)] for `lang`; a pattern without lowercase letters is case-sensitive."""
    out = []
    for i, g in enumerate(glossary):
        pats = g["match"].get(lang) or g["match"]["en"]
        parts = [f"(?{'i' if re.search('[a-zа-яё]', p) else ''}:{p})" for p in pats]
        out.append((i, re.compile(r"(?<![\w-])(?:" + "|".join(parts) + r")(?!\w)")))
    return out


def mark_terms(fragment, matchers, glossary, lang, used):
    """Wrap the first mention of each glossary term (`used` is per method) in an HTML fragment, outside tags and code."""
    out, in_code = [], 0
    for piece in re.split(r"(<[^>]+>)", fragment):
        if piece.startswith("<"):
            if re.match(r"<code\b", piece):
                in_code += 1
            elif piece.startswith("</code"):
                in_code -= 1
            out.append(piece)
            continue
        while piece and not in_code:
            hits = [(m.start(), -len(m.group(0)), i, m) for i, rx in matchers if i not in used
                    for m in [rx.search(piece)] if m]
            if not hits:
                break
            _, _, i, m = min(hits)
            used.add(i)
            definition = html.escape(t(glossary[i]["def"], lang), quote=True)
            out.append(piece[:m.start()])
            out.append(f'<span class="term" tabindex="0" data-def="{definition}">{m.group(0)}</span>')
            piece = piece[m.end():]
        out.append(piece)
    return "".join(out)


# ---------------------------------------------------------------- rendering
def render_method(m, lang, site, pid, names, matchers, glossary):
    f = localized(m, lang)
    ui = site["ui"]
    label = t(site["grade_labels"][m["grade"]], lang)
    anchor = pid("m-" + m["id"])
    head = [f'<span class="badge {m["grade"]}">{html.escape(label)}</span>',
            f'<span class="mname">{names[m["id"]]}</span>']
    if f["fallback"]:
        head.append(f'<span class="fallback" title="{html.escape(t(ui["untranslated"], lang))}">EN</span>')
    head.append(f'<a class="perma" href="#{anchor}" title="{html.escape(t(ui["permalink"], lang))}">#</a>')

    body, used = [], set()
    for slot in SLOTS:
        if f[slot]:
            text = mark_terms(inline_md(f[slot]), matchers, glossary, lang, used)
            body.append(f'<div class="slot {slot}"><span class="label">{html.escape(t(ui[slot], lang))}</span>'
                        f'<span class="text">{text}</span></div>')
    if m["see_also"]:
        links = " · ".join(f'<a href="#{pid("m-" + ref)}">{names[ref]}</a>' for ref in m["see_also"])
        body.append(f'<div class="slot see"><span class="label">{html.escape(t(ui["see_also"], lang))}</span>'
                    f'<span class="text">{links}</span></div>')
    if f["code"]:
        sketch = bool(m.get("sketch"))
        summary = t(ui["sketch" if sketch else "code"], lang)
        note = f' <span class="note">· {html.escape(t(ui["sketch_note"], lang))}</span>' if sketch else ""
        body.append(f'<details class="snippet"><summary>{html.escape(summary)}{note}</summary>'
                    f'<pre><code class="language-python">{html.escape(f["code"].rstrip())}</code></pre></details>')
    return (f'<div class="method" data-grade="{m["grade"]}" id="{anchor}">'
            f'<div class="mhead" role="button" tabindex="0" aria-expanded="true">{"".join(head)}</div>'
            f'<div class="mbody">{"".join(body)}</div></div>')


def render_lang(lang, site, sections, methods, glossary):
    pid = lambda x: f"{lang}-{x}"
    names = {m["id"]: inline_md(localized(m, lang)["name"]).rstrip(".") for m in methods}
    matchers = term_matchers(glossary, lang)
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
                body.append(render_method(m, lang, site, pid, names, matchers, glossary))

    brilliant = [m for m in methods if m["grade"] == "brilliant"]
    if brilliant:
        body.append(f'<h2 id="{pid("brilliant")}">{html.escape(t(site["brilliant_heading"], lang))}</h2><ol>')
        nav.append(f'<a class="l2" href="#{pid("brilliant")}">{html.escape(t(site["brilliant_heading"], lang))}</a>')
        for m in sorted(brilliant, key=lambda m: numbers.get(m["id"], "")):
            body.append(f'<li><a href="#{pid("m-" + m["id"])}">{names[m["id"]]}</a> '
                        f'(§{numbers.get(m["id"], "?")})</li>')
        body.append("</ol>")

    if glossary:
        title = t(site["ui"]["glossary"], lang)
        body.append(f'<h2 id="{pid("glossary")}">{html.escape(title)}</h2>')
        body.append(f'<p class="muted">{html.escape(t(site["ui"]["glossary_intro"], lang))}</p><dl class="glossary">')
        nav.append(f'<a class="l2" href="#{pid("glossary")}">{html.escape(title)}</a>')
        for g in sorted(glossary, key=lambda g: t(g["term"], lang).lower()):
            body.append(f"<dt>{html.escape(t(g['term'], lang))}</dt><dd>{html.escape(t(g['def'], lang))}</dd>")
        body.append("</dl>")
    return "\n".join(body), "\n".join(nav)


def build(write=True):
    site, sections, methods, glossary, errors, warnings = load()
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
        print(f"ok: {len(methods)} methods, {len(glossary)} glossary terms")
        return

    panes, navs = [], []
    for lang in langs:
        body, nav = render_lang(lang, site, sections, methods, glossary)
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
    print(f"wrote {out}: {len(methods)} methods, {len(glossary)} glossary terms, {len(langs)} languages")


TEMPLATE = (ROOT / "template.html").read_text(encoding="utf-8") if (ROOT / "template.html").exists() else ""

if __name__ == "__main__":
    build(write="--check" not in sys.argv)
