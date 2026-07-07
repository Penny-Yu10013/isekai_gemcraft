# Credits

Built by a jewelry designer with no programming background, through several rounds
of AI-assisted development ("vibe coding") with Claude Code. Honest timeline below —
including the attempt that didn't work out.

## Timeline

**2026-06-23, 02:50–04:50** — First attempt, **Opus 4.8**. Two hours in, the cutting
engine kept producing broken/degenerate geometry. Shelved rather than keep burning
tokens on it — this looked like it would need a much bigger investment than expected,
so it went back in the drawer in favor of other creative work.

**2026-06-26** — Found **GemCutter**, a Blender plugin by Máté Djuroska with the same
core math (angle × index × depth = facet), built for precise modeling rather than
interactive play. Never integrated — just left as a reference note in `CLAUDE.md`.

**2026-07-05, 03:00 →** — Restarted from scratch with **Fable 5**, fresh off release.
Built the large majority of the project — cutting engine, diagram system, procedural
machine model, most UI systems — across roughly three ~1M-token Claude Code threads
in a self-imposed few-day sprint.

**2026-07-05, 11:00 →** — **Sonnet 5** joined in parallel: UI polish and bugfixes
(mobile flexbox squeeze, theme toggle, tooltip i18n), the light-glass theme, favicon,
sound design touch-ups, and this file.

## Rough split

- **Fable 5** — the bulk of it (~80%): cutting engine, diagram system, machine model,
  most features
- **Sonnet 5** — UI refinement, bugfixes, polish passes, marketing copy review
- **Opus 4.8** — first attempt; not shipped, but the reason the second attempt started
  from a clearer idea of what to avoid
- **Human** — every creative and design decision, final say on all copy (AI drafted,
  human approved or replaced), gemology accuracy checks, QA on an actual phone

## Also

- Cut-shape icons: [JewelCraft](https://github.com/mrachinskiy/jewelcraft) (Mikhail
  Rachinskiy, GPL-3.0)
- Faceting diagram references: [GemologyProject](https://www.gemologyproject.com/wiki/index.php?title=Faceting_Designs)
