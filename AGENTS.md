# sanage Axis Agent Directory & Subskills Overview

This file serves as a reference catalog for AI agents (e.g. Claude Code or claude.ai) executing the **sanage Axis** major selection skill.

## 📁 Repository Map

- `SKILL.md` — The main entrypoint with routing rules, CLI conventions, and knowledge file index.
- `references/` — On-demand protocol documents (loaded per stage):
  - `profile_protocol.md` — Three-gate information collection protocol & 8-question Holland quiz.
  - `analyze_protocol.md` — Five-phase reasoning & three-officer adversarial review.
  - `report_protocol.md` — 1+X survival report formatting requirements.
  - `snapshot_protocol.md` — Session snapshot save/restore/list operations.
  - `user_state_tpl.md` — Student state template (v3.0 nested schema).
- `scripts/` — Tool scripts for computing math models:
  - `runner.py` — CLI entrypoint with multi-command chain support.
  - `evaluator.py` — Survival scores and compatibility ranks.
  - `injector.py` — Database lookups.
  - `trait_evaluator.py` — Holland Codes converter (with 8-question scoring `evaluate_8q`).
  - `mbti_evaluator.py` — MBTI personality assessment and major matching (optional).
  - `fallback_data.py` — Local fallback data for provincial lines and rank estimation (API unavailable).
  - `output_generator.py` — Report compiler helper.
- `data/` — Static data files containing rules, cancellations, and score limits.
- `tests/` — Test files for core functionality:
  - `test_skills.py` — Unit tests (15 cases covering evaluator, injector, trait, sogou API, runner, snapshots).
  - `test_runner.py` — Integration tests for the main runner and interactive console.

## ⚙️ Workflow Pipeline

To execute the workflow pipeline:

1. Read `references/profile_protocol.md` and follow the three-gate collection flow. If Holland code is missing, run the 8-question quiz.
2. Read `references/analyze_protocol.md`. Feed compiled facts and perform adversarial reasoning against `data/` knowledge base.
3. Read `references/report_protocol.md` to format and print the final 1+X survival document.
