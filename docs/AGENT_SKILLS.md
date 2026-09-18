# Agent skills integration (PC side)

GrokLink firmware pairs with a PC-side Grok **skills** layer for routing, research,
pipelines, and educational helpers. Skills live in the operator's Grok skills
directory (not in firmware flash).

## What skills do for GrokLink

| Concern | Skill / tool |
|---------|----------------|
| Choose which skill to load | `skill-router` (rank / bootstrap discovery) |
| Improve a skill after failures | `skill-reflector` |
| Scaffold / validate skills | `create-skill` |
| Multi-step PC pipelines | `workflow-orchestrator` |
| Research notes -> report | `research-synthesis` |
| Educational pulse CSV BPM | `flipper-pulse-edu` (NOT medical) |
| On-device RF skills | SD `/ext/groklink/skills/*` via GrokLink skill craft |
| Public repo publish | `public-github-hygiene` (single commit, no PII) |

## Operator conventions

1. Prefer ranking before opening many skill bodies.
2. Log useful invokes when metrics tooling is available.
3. Keep firmware SD skills **passive by default**; no boot-time radio autonomy.
4. Never claim medical diagnosis from Flipper or DIY sensors. GrokLink is **not a medical device**.
   Healthcare/MedSec research packs: `docs/HEALTHCARE_MEDSEC_PLAN.md`, `sd_card/groklink/healthcare/`.
5. One serial owner: close qFlipper before bridge; free stuck python processes.
6. Prefer 1 s passive RX windows for control-plane stability.
7. After `skill_reload`, reopen COM if the port disappears.

## On-device skill packages (this repo)

See `skills/TRACKING.md` and `sd_card/groklink/skills/`.

Leisure explore skill: `lab_band_survey_leisure` (300 / 315 / 433.92 / 868 / 915 contrast).

## Bridge research improvements

- Brace-balanced `GROKRPC:` parse for multi-field responses
- Lenient JSON load strips bare control characters from older firmware list RPCs
- Skill craft defaults to 1 s RX; understands `method` fields in explore logs

## Safety

Authorized educational research only. TX remains confirm-gated on device and PC.
