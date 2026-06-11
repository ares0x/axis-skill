# sanage Axis Agent Directory & Subskills Overview

This file serves as a reference catalog for AI agents (e.g. Claude Code or claude.ai) executing the **sanage Axis** major selection skill.

## 📁 Repository Map

- `skills/axis/SKILL.md` — The main entrypoint for triggering the高考志愿顾问 service.
- `skills/` — The directory hosting specialized subskills:
  - `profile/SKILL.md` — Information collection protocols & interactive personality diagnostic scripts.
  - `analyze/SKILL.md` — Utilization matching rules & three-officer backend adversarial review.
  - `report/SKILL.md` — Formatting requirements for outputting the final 1+X roadmap.
  - `save/SKILL.md` — Session snapshot saving subskill.
  - `restore/SKILL.md` — Session snapshot restoring subskill.
  - `list/SKILL.md` — Snapshot and candidate list subskill.
- `scripts/` — Tool scripts for computing math models:
  - `evaluator.py` — Survival scores and compatibility ranks.
  - `injector.py` — Database lookups.
  - `trait_evaluator.py` — Holland Codes converter.
  - `output_generator.py` — Report compiler helper.
- `data/` — Static data files containing rules, cancellations, and score limits.

## ⚙️ How to Call Subskills

To execute the workflow pipeline:
1. Load student details using `/profile` subskill. If inputs are missing, run the 8-question quiz.
2. Feed compiled facts to `/analyze` subskill. The agent reads `data/` and performs adversarial reasoning.
3. Pass analysis results to `/report` subskill to format and print the final document.
