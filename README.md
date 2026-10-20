# ML competition methods catalog

A static, multilingual page listing ML competition methods, built from one YAML file per method.

**Live page:** https://krokha-konstantin.github.io/ml-methods-catalog/ — rebuilt automatically on every push to `main`
(see `.github/workflows/pages.yml`). Editing a YAML file on GitHub and committing is enough; if the build finds an
error, the Action fails and the live page stays as it was.

```
catalog/
├── methods/            one file per method (<id>.yml); _template.yml shows every field
├── sections.yml        section/subsection ids, order and titles (all languages)
├── site.yml            languages, page texts, grade labels, UI strings
├── glossary.yml        term definitions shown on hover and in the Glossary section
├── template.html       page layout, styles and script (no content)
├── build.py            validates everything and writes methods_catalog.html
├── WRITING.md          how to word, grade and translate a method
└── methods_catalog.html  generated, self-contained; open it in any browser
```

Local preview: `pip install -r requirements.txt`, then build and open `methods_catalog.html` (it is git-ignored).

```
python build.py           # validate + build
python build.py --check   # validate only (exits 1 on errors), prints translation coverage
python build.py --private # local build that also includes private/ (see below)
```

## Add a method
1. Copy `methods/_template.yml` to `methods/<short-id>.yml`.
2. Fill in `section`, `subsection`, `order`, `grade`, `name`, `when`, `do`, `why`, `see_also`, `code`,
   following [WRITING.md](WRITING.md).
3. Run `python build.py`. Errors name the file and the problem (unknown section, bad grade, unknown `see_also` id, …).

## Content that can't be public yet
`private/methods/` is git-ignored and never published, e.g. code from a competition that is still running.
`python build.py --private` builds a local page that includes it; a private file with the same name as a
public one replaces it in that build (useful to keep the full version of a method whose public copy is trimmed).
Sections left without public methods are dropped from the public page automatically.
To publish later, reword the files per [WRITING.md](WRITING.md) and move them from `private/methods/` to `methods/`.

## Add a section or subsection
Add an entry to `sections.yml` with an `id` and a `title` per language. Numbering follows the list order.
Quote titles in the `{en: "...", ru: "..."}` form: an unquoted comma ends the value.

## Add a glossary term
Add an entry to `glossary.yml` with `term`, `match` (regular expressions per language) and `def`. The build
underlines the first mention of the term in each method (definition on hover or tap) and lists it in the Glossary
section at the end of the page.

## Translate
- **A method**: add `translations: {<lang>: {name, when, do, why}}` to its file. Untranslated methods
  are shown in English with an "EN" marker, and untranslated fields fall back to English one by one.
- **A new language**: add it under `languages` in `site.yml`, then add that key to the strings in
  `site.yml`, `sections.yml` and `glossary.yml` (missing strings fall back to English too).

The page has a language switcher; `?lang=ru` in the URL selects a language directly.

## Writing guidelines
See [WRITING.md](WRITING.md): how a method is named, described, graded, de-duplicated and translated.
