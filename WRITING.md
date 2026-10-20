# How to word a method

Every entry must make sense to a reader who has never seen the competition, the data or the code it came from.
The entry teaches a **general technique**; the code snippet is the only concrete part.

## 1. Name

- The general technique in standard ML terms: "Group K-fold", "Out-of-fold target encoding",
  "Link additional data to the training rows".
- Use the established term when one exists (record linkage, system identification, label shift). A reader should
  be able to search for it.
- Never the instance it was found in: not "StratifiedGroupKFold by protocol text", not "Join the extra table that is
  a noisy copy of train". Ask: *what would this be called in a textbook or a course?*
- Short: a noun phrase or an imperative, no full sentence, no trailing period.

## 2. Description

Two parts, usually two or three sentences (about 25–70 words):

1. **The principle**: when it applies and what to do, in general terms. Start conditional techniques with the
   condition: "If additional data is given …", "When rows come in groups …".
2. **Why it matters**: the failure mode it prevents or the payoff. "Otherwise the model is scored on near-copies of
   its own training rows." "A known formula costs one line, while a model would need far more data to rediscover it."

Rules:

- **No task specifics.** No dataset, competition, column or variable names, contest numbers, or domain nouns that
  only make sense in one task (patient, well, nozzle, protocol). If an illustration helps, use a short parenthetical
  of generic kinds that fit many tasks: "(sessions, users)", "(month, hour)", "(tables, templates, signatures)".
- **No story.** Don't say what happened in the source ("here …", "z-scoring made the term tiny, so …"). Turn the
  lesson into a general warning: "normalising one term can make the other dominate; check their magnitudes".
- **Algorithms, not libraries.** Name the method (gradient boosting, TPE, RANSAC, YOLO as a model family);
  library names (CatBoost, Optuna) belong in the code only.
- **No "Example:" line.** Examples were removed: the code snippet is the example.
- One technique per entry. If a description needs "and also …" for an unrelated idea, split it or drop the extra part.
- Inline markdown only (`code`, *italic*). No links.

## 3. Code

- Keep the snippet from the solution; it shows the technique working on real data. Do not rewrite it to match
  the wording.
- Short and self-contained, with readable names. Trim lines that don't illustrate the technique.
- If there is no real code, write a minimal illustration and set `sketch: true`.
- When entries are merged, their snippets are concatenated, separated by a blank line.

## 4. Grade

Grade the **general idea** after it has been reworded, never who used it and never whether it worked.

| grade | test |
|---|---|
| `book` | It appears in standard courses, textbooks or common practice guides. Basic feature engineering (domain formulas, calendars, group statistics), standard losses, validation schemes and ensembling are `book`. |
| `good` | Simple once seen, but most practitioners wouldn't reach for it: a small insight about the data, the metric or the task framing. |
| `brilliant` | A genuinely original use of the available data that a strong practitioner would not think of by default. Rare: most sections have none. |

A task-specific framing often makes a standard idea look novel. Once the specifics are gone, re-check: if the
remaining sentence describes something a course teaches, it is `book` (e.g. physics-derived features → domain-knowledge
features → `book`; exposure normalisation → `book`).

## 5. Duplicates

Before adding an entry, search the catalog for the same idea under another name (`python build.py --check` does not
catch this). Two entries are duplicates when their reworded names describe the same technique, e.g. "split on the unit
of correlation" and "Group K-fold", or "leave-one-out context features" and "target encoding". Merge them: keep the
more general name, fold the extra nuance into one clause of the description, concatenate the code, delete the other file.

## 6. Placement

- `section` is the task type the technique belongs to in general, not the task it was found in. A technique that works
  on any task type goes to `universal` (validation, ensembling, thresholds, hyperparameters, leaderboard).
- Order within a subsection: from the most basic to the most specialised.

## 7. Translation

- Translate the reworded English, not the original note. Same content and the same grade; never add specifics.
- Russian: names in the imperative or a noun phrase, like the English. Keep the standard English term when that is
  what Russian-speaking practitioners use (out-of-fold, target encoding, record linkage, bagging), optionally with a
  Russian gloss.
- Untranslated fields fall back to English automatically, so a partial translation is better than a wrong one.

## Checklist

- [ ] Would an outsider understand the name and description without the code?
- [ ] Is there any word that only makes sense in the source task? Remove it.
- [ ] Does the description say *why*, not only *what*?
- [ ] Is the grade still right for the general idea?
- [ ] Is there already an entry for the same idea?
- [ ] Is the translation updated?
