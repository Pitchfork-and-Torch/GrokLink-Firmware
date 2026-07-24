# Healthcare / MedSec Phase 1 packs

NOT A MEDICAL DEVICE. Authorized research and education only.

Copy skills and missions into the live `/ext/groklink/` tree as described in
`docs/HEALTHCARE_OPERATOR_RUNBOOK.md`.

Blacklist files here are **templates**. The agent only loads:

- `/ext/groklink/blacklist/freq_mhz.json`
- `/ext/groklink/blacklist/gpio_pins.json`

Review every entry before merging a template into those active files.
Do not ban RX for facility survey work unless your RoE requires it;
these templates focus on **TX-forbidden** centers and protocol names.

## Contents

| Path | Purpose |
|------|---------|
| blacklist/*.template.json | Optional TX policy starters |
| missions/* | Passive-only mission JSON |
| skills/* | passive_rx skill packages |

## Skills

| ID | Risk | Purpose |
|----|------|---------|
| medsec_passive_ism_watch | passive_rx | Lab ISM activity watch for authorized MedSec |
| fac_rf_baseline_watch | passive_rx | Facility engineering RF baseline (passive) |
| med_asset_uid_inventory | passive_rx | Owned NFC/UID inventory study path |

## Missions

| ID | Purpose |
|----|---------|
| fac_rf_snapshot_passive | Short multi-band passive snapshot |
| medsec_lab_passive_ism | MedSec lab ISM passive sample |

All missions: autonomous false or passive max_risk_class only; short RX windows.
