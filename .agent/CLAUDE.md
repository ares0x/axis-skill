# sanage Axis - Agent Execution Rules

## Philosophy
1. Survival First: Employment and adaptability trump academic illusions.
2. No Hallucinations: All recommendations must match `data/` and `facts.json`.
3. Progressive Discovery: Never give a school list before `facts.json` is 100% complete.

## Workflow Pipeline
1. `/init` -> Trigger `profile_officer` to establish `workspace/sessions/{uid}/facts.json`.
2. `/veto` -> Trigger `veto_officer` to cross-check `2026_cancelled_majors.csv` and output risk alerts.
3. `/audit` -> Trigger `audit_officer` to balance family resources and industrial trends.
4. `/export` -> Generate the final "1+X" future survival action list.

## State Guard [DBSkill Concept]
- If user changes mind (e.g., changes city preference), rewrite `facts.json` and clear `blind_spots.md`.
- Every AI response must append: `[Current State: Profile Step X/4]`.
