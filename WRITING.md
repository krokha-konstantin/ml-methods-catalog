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

## 2. When / Do / Why

The description is three short fields, one or two sentences each (about 40–80 words in total):

| field | content | example |
|---|---|---|
| `when` | The situation that calls for the technique, as a statement. Leave it out only when the technique always applies (a standard recipe). | "Additional data is given that describes the same objects as the training set." |
| `do` | What to do, in general terms. Required. | "Match each training row to its counterpart by nearest neighbour on the shared columns and add the extra columns." |
| `why` | The failure mode it prevents or the payoff. | "Otherwise the model is scored on near-copies of its own training rows." |

- Each field must read on its own: no "it" pointing back to another field's noun.
- `when` describes the data or the setting, not the method ("Labels are noisy", not "Use when labels are noisy").
- Don't repeat the name in `do`; add what the name leaves out.

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
- Inline markdown only (`code`, *italic*). No links: related methods go in `see_also`, definitions in the glossary.

## 3. Code

- Keep the logic of the snippet from the solution; it shows the technique working on real data.
- Start with a one-line comment saying what the snippet shows: `# out-of-fold encoding, and a smoothed leave-one-out variant`.
- Use generic names: `target`, `category`, `entity_id`, `sales`, `series_id`, not the source's column names
  (`rent_price`, `protocol_text`). Library names are fine in code.
- Short and self-contained. Trim lines that don't illustrate the technique.
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

### The `general` flag

Set `general: true` when the trick carries over to a typical task: fine-tuning a transformer (warm-up and decay,
gradient clipping, dynamic padding) is general; removing training classes that never occur in the test set is
specific. It is independent of the grade. Leave it out for specific tricks; the page shows a GENERAL tag next to
the name.

## 5. Duplicates

Before adding an entry, search the catalog for the same idea under another name (`python build.py --check` does not
catch this). Two entries are duplicates when their reworded names describe the same technique, e.g. "split on the unit
of correlation" and "Group K-fold", or "leave-one-out context features" and "target encoding". Merge them: keep the
more general name, fold the extra nuance into one clause of the description, concatenate the code, delete the other file.

## 6. Placement and links

- `section` is the task type the technique belongs to in general, not the task it was found in. A technique that works
  on any task type goes to `universal` (validation, ensembling, thresholds, hyperparameters, leaderboard).
- Solutions to one-off puzzles (simulators, games, math problems) go to `puzzles`, so they don't interrupt the
  reusable material.
- Order within a subsection: from the most basic to the most specialised.
- `see_also`: two to four closely related methods, especially ones in other sections (metric as loss ↔ metric-weighted
  loss; predict the change ↔ residual over a baseline). Add the link in both files.

## 7. Glossary

- A term that an outsider may not know (OOF, RANSAC, InfoNCE) goes into `glossary.yml`, not into the method text.
  It is then underlined automatically on its first mention in every method.
- Definitions are one or two plain sentences, readable without other glossary entries.
- Don't add everyday ML words (model, feature, training) or the method names themselves.

## 8. Translation

- Translate the reworded English, not the original note. Same content and the same grade; never add specifics.
- Translate `when`, `do` and `why` field by field; add Russian `match` patterns for new glossary terms (word stems with `\w*`).
- Russian: names in the imperative or a noun phrase, like the English. Keep the standard English term when that is
  what Russian-speaking practitioners use (out-of-fold, target encoding, record linkage, bagging), optionally with a
  Russian gloss.
- Untranslated fields fall back to English automatically, so a partial translation is better than a wrong one.

## Checklist

- [ ] Would an outsider understand the name and the when / do / why without the code?
- [ ] Is there any word that only makes sense in the source task? Remove it.
- [ ] Is `why` filled in, and is it a reason rather than a restatement of `do`?
- [ ] Does the code start with a one-line comment and use generic names?
- [ ] Are related methods linked in `see_also`, and new jargon added to the glossary?
- [ ] Is the grade still right for the general idea?
- [ ] Is there already an entry for the same idea?
- [ ] Is the translation updated?
