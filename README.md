# ✦ Isekai Gemcraft — 異世界魔法石工坊

**A 3D gemstone faceting simulator in a single HTML file.**
Real faceting-machine mechanics — tilt angle × index gear × depth stop — driven by real-time convex polytope clipping in the browser. No build step, no install, no backend.

**▶ [Play Now](https://penny-yu10013.github.io/isekai_gemcraft/)** — desktop & mobile (portrait), English / 繁體中文 (toggle in-game, bottom-left)

<!-- screenshot placeholder: title screen (machine idle animation) -->
<!-- screenshot placeholder: cutting view with diagram panel -->
<!-- screenshot placeholder: appraisal card with hero stone -->

## What is this?

You are the cutter, not the audience. Pick a crystal system, mount the rough on the dop, then work like a real faceting machine:

- **Tilt** the stone with the protractor (0–90°) — the stone tilts live
- **Rotate** to a symmetry position on the 96-tooth index gear
- **Press** — blind: the view masks while you grind, longer press cuts deeper, release to reveal. No undo.
- **Depth stop** (mast height analog): grinding halts at the exact target plane; re-cutting the same setting removes nothing — that's how the symmetry math works on real machines too
- Swap laps (coarse → fine → polish), then submit for an **overdramatic otherworld appraisal** (sharp tongue included)

### Faceting diagrams

Five built-in cut designs executed like real faceting charts (angle + index + depth per tier), with a guided instruction sheet, target-index compass rings, and one-tap symmetric array cutting:

| Diagram | Facets | Symmetry | Difficulty |
|---|---|---|---|
| Simple Sun (tutorial) | 17 | 8-fold | ⭐ start here |
| Standard Round Brilliant | 57 | 8-fold | challenge |
| Asscher Step Cut | 49 | 8-fold, girdle blades | intermediate |
| Portuguese | 97 | 16-fold, staggered rows | hard |
| Trillion | 16 | 3-fold | quick |

Free-cutting mode (no diagram, zero guardrails) is there for purists.

### Also inside

- Top-view **navigator** with live n-fold symmetry analysis
- **Gem collection**: every stone (including scrapped ones) gets a thumbnail snapshot, scooped into a daily tray; ⭐ favorites, JSON export/import
- Procedurally generated faceting machine (Blender-scripted GLB, base64-embedded), fully animated title scene
- 100% procedural WebAudio (BGM, grinding, appraisal chimes) — zero audio files
- Dark cathedral / light liquid-glass themes; full touch support on mobile

## How it works (the interesting part)

The stone is a **convex polytope** (vertex + face lists). Every cut is one half-space plane clip (`clipSolid`) — computed exactly, no voxels, no CSG library, no mesh booleans. Facets stay perfectly planar at any count (the Portuguese cut runs 121 faces), and cutting the same plane twice is a geometric no-op, which is precisely the property that makes depth-stop faceting and symmetric arrays work.

The cut plane is always "world down"; the stone's tilt (angle) and spin (index) are quaternions, and the plane is transformed into stone-local coordinates — the same mental model as a physical faceting machine, where the lap is horizontal and the stone does all the moving.

Keywords for the curious: real-time convex clipping · procedural gemstone faceting simulation · computational geometry in the browser.

**Stack**: one HTML file, Three.js r128 (CDN), vanilla JS. That's the whole thing.

## Contributing

New faceting diagrams are the main contribution path — the diagram system is data-driven, so a new cut design is a data entry plus one card in the picker, no engine changes. See **[CONTRIBUTING.md](CONTRIBUTING.md)** for the format, the depth-value math, and the acceptance checklist (the built-in `#dev` auditor must report a 100% facet match).

## Development docs (中文)

The engineering handover doc is [`CLAUDE.md`](CLAUDE.md) (architecture decisions, code map), and the full diagram-authoring methodology is [`新增切型指南.md`](新增切型指南.md) — both in Traditional Chinese; CONTRIBUTING.md carries the English essentials.

## Credits

- Cut-shape icons from [JewelCraft](https://github.com/mrachinskiy/jewelcraft) (Mikhail Rachinskiy, GPL-3.0)
- Faceting diagram references: [GemologyProject Faceting Designs](https://www.gemologyproject.com/wiki/index.php?title=Faceting_Designs); the five built-in diagrams are original simplified designs
- Built in collaboration with [Claude Code](https://claude.com/claude-code)

## License

Code license: not yet chosen (all rights reserved for now — open an issue if this blocks you). Embedded cut-shape icons remain GPL-3.0 per JewelCraft.
