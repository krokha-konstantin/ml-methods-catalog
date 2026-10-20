# ML competition methods catalog

A static, multilingual page listing ML competition methods, built from one YAML file per method.

**Live page:** https://&lt;github-username&gt;.github.io/ml-methods-catalog/ — rebuilt automatically on every push to `main`
(see `.github/workflows/pages.yml`). Editing a YAML file on GitHub and committing is enough; if the build finds an
error, the Action fails and the live page stays as it was.

```
catalog/
├── methods/            one file per method (<id>.yml); _template.yml shows every field
├── sections.yml        section/subsection ids, order and titles (all languages)
├── site.yml            languages, page texts, grade labels, example-task table, UI strings
├── template.html       page layout, styles and script (no content)
├── build.py            validates everything and writes methods_catalog.html
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
2. Fill in `section`, `subsection`, `order`, `grade`, `name`, `description`, `example`, `code`.
3. Run `python build.py`. Errors name the file and the problem (unknown section, bad grade, …).

## Content that can't be public yet
`private/methods/` is git-ignored and never published, e.g. code from a competition that is still running.
`python build.py --private` builds a local page that includes it; a private file with the same name as a
public one replaces it in that build (useful to keep the full version of a method whose public copy is trimmed).
A task row in `site.yml` with `private: true` is likewise shown only in `--private` builds.
Sections left without public methods are dropped from the public page automatically.
To publish later, move the files from `private/methods/` to `methods/` and remove `private: true`.

## Add a section or subsection
Add an entry to `sections.yml` with an `id` and a `title` per language. Numbering follows the list order.
Quote titles in the `{en: "...", ru: "..."}` form: an unquoted comma ends the value.

## Translate
- **A method**: add `translations: {<lang>: {name, description, example}}` to its file. Untranslated methods
  are shown in English with an "EN" marker, and untranslated fields fall back to English one by one.
- **A new language**: add it under `languages` in `site.yml`, then add that key to the strings in
  `site.yml` and `sections.yml` (missing strings fall back to English too).

The page has a language switcher; `?lang=ru` in the URL selects a language directly.

## Writing guidelines
- **Name:** the general technique in standard ML terms, never a competition-specific instance.
- **Description:** the principle, then why it matters (the failure mode it prevents or the payoff).
- **Example:** the only place for task specifics, written as "task, concrete instance".
- **Grade:** rate the idea itself, not who used it or whether it worked:
  - `book`: everyone studies it.
  - `good`: simple once seen, but not standard practice.
  - `brilliant`: a genuinely original use of the available data.
