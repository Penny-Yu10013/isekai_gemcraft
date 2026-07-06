# Contributing to Isekai Gemcraft

Thanks for your interest! The primary contribution path is **new faceting diagrams** — the diagram system is fully data-driven, so a new cut design touches data only, never the engine.

> Deep-dive methodology doc: [`新增切型指南.md`](新增切型指南.md) (Traditional Chinese). Everything essential is summarized in English below — you don't need the Chinese doc to contribute.

## What a diagram PR changes

Exactly two places in `gemcraft.html`, nothing else:

1. **One entry in the `DIAGRAMS` array** (search for `const DIAGRAMS=`)
2. **One card in the `#diagramRow` picker** (search for `diagramRow`)

PRs that modify the cutting engine, UI logic, or other diagrams will be asked to split those changes out.

## Diagram data format

```js
{id:'asscher49', name:'八角階梯 · Asscher 49', nameEn:'Asscher Step Cut · 49', fold:8, gear:96,
 desc:'…中文描述…', descEn:'49-facet step cut: …',
 tiers:[
  {id:'G',  side:'girdle',   angle:90, d:0.90,  indices:[96,12,24,36,48,60,72,84]},
  {id:'P1', side:'pavilion', angle:55, d:0.754, indices:[96,12,24,36,48,60,72,84]},
  // …
  {id:'T',  side:'crown',    angle:0,  d:0.37,  indices:[96], indexFree:true}]},
```

| Field | Meaning |
|---|---|
| `id` | unique ASCII id (used by the `#dev` auditor: `__diag.run(id)`) |
| `name` / `nameEn` | display names — **both languages required** (zh format: `中文名 · English N`) |
| `desc` / `descEn` | one-line description, both languages |
| `tiers[].side` | `'pavilion'` (no flip) / `'crown'` (stone flips) / `'girdle'` (vertical blade, angle 90, no flip) |
| `tiers[].angle` | 0 = horizontal table, 90 = vertical girdle. **Must be a multiple of 0.5** (slider step) |
| `tiers[].d` | absolute plane distance in units of R (preform in-radius). Depth-stop slider range: 0.20–1.50 |
| `tiers[].indices` | teeth on the 96-tooth gear (96 ≡ 0°, one tooth = 3.75°) |
| `tiers[].indexFree` | table only (angle 0): spin doesn't change the normal → `indices:[96], indexFree:true` |

Tier order in the array = build order (girdle blades first if any, then pavilion steep→shallow, crown steep→shallow, table last).

The picker card (both languages come from the i18n table — add your EN card text to `I18N_STATIC` following the existing `.diagCard` entries):

```html
<button class="diagCard" data-diag="yourid">
  <span class="dcEmoji">🔷</span>
  <span class="dcText">中文名 · Name N<small>tagline · difficulty</small></span>
</button>
```

## The math you need

The preform is a 24-gon prism: in-radius **R** (this is the unit of `d`), girdle plane at y=0, pavilion budget **−1.05R**, crown budget **+0.55R** (hard ceiling — the table's `d` must be < 0.55).

A cut plane passing through radius `r` at vertical offset `h` from the girdle:

```
d = r·sin(angle) + h·cos(angle)
```

Chain tiers from the girdle inward: choose each tier's break radius, compute the depth at that radius on the previous tier's plane, feed it into the next tier. Worked example (Asscher pavilion) in `新增切型指南.md` §2.3.

**Five hard checks:**

1. **Culet closes**: final pavilion tier's `d / cos(angle) < 1.05`, or the preform's bottom cap survives and the audit fails.
2. **Table budget**: table `d < 0.55`.
3. **Steep-to-shallow ordering** per side (steeper tiers cut only near the girdle; invert it and a tier cuts nothing or eats the culet).
4. **Every tier must remove material** — a plane entirely outside the current solid produces zero facets and the audit catches it.
5. **Girdle blades**: adjacent-blade corner = `d / cos(half the angular gap)` must stay **< 1.0R** (octagon: d ≤ 0.90; trigon: d ≤ 0.49).

**Symmetry rules (96-tooth gear):**

- Usable folds divide 96: 2, 3, 4, 6, 8, 12, 16, 24, 32, 48. **5-fold and 7-fold are impossible** on this gear.
- Every tier's index set must be mirror-symmetric under `t → 96−t` (the crown flip mirrors azimuth). `[96,12,24,…,84]` ✓, `[3,9,…,93]` ✓, `[96,10,20]` ✗.
- **Elongated outlines (oval / pear / marquise / baguette) don't fit the data model** — they need per-index depths (cheater cuts), which the one-depth-per-tier format cannot express. Don't attempt them as data-only PRs.

## Acceptance checklist (run before opening the PR)

Open `gemcraft.html#dev` in a browser (reload after adding `#dev`), then in the console:

```js
__diag.run('yourid')   // auto-preforms and cuts the whole diagram
auditDiagram()         // ← must return matched === total, worst.dev ≈ 0
```

- [ ] `auditDiagram()`: **`matched === total`**, `worst.dev` ≈ 0 — this is the hard gate
- [ ] Visual check: correct outline, culet closed, girdle band (or blades) present, no broken faces
- [ ] Player path works: pick diagram → preform → tap tier rows → array cut → every row checks off → submit
- [ ] Regression: `__diag.run` every existing diagram id — all still 100%
- [ ] Both `name`/`nameEn`, `desc`/`descEn`, and the picker card's EN entry in `I18N_STATIC` are present

## PR description format

- Diagram name, fold symmetry, facet count
- The tier table (angle / d / indices) in the description
- A screenshot of the finished stone (main view + top-view navigator)
- **Source of the design**: original, public-domain chart, or licensed — if transcribed from a published faceting diagram (e.g. GemologyProject), name it and confirm the license permits it. Some designers (e.g. Surgical Precision Gems) restrict reuse.
- Paste the `auditDiagram()` output

## Bug reports

Use the issue templates. For geometry bugs, please distinguish "the mesh actually has holes / missing faces" from "my cut came out ugly" — only the former is an engine bug.
