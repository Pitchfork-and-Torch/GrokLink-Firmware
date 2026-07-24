# Healthcare / MedSec operator runbook (Phase 1)

**NOT A MEDICAL DEVICE.** Authorized lab and education only.

## 1. Prerequisites

1. GrokLink firmware on device (status shows groklink-2.1.1 or newer).
2. SD layout `/ext/groklink/` present.
3. Written authorization for every target (own gear or signed RoE).
4. One serial owner: close qFlipper before the PC bridge.

## 2. Install Phase 1 packs

From a host checkout of this repo:

1. Copy skill folders under `sd_card/groklink/healthcare/skills/*`
   to Flipper `/ext/groklink/skills/<id>/`.
2. Copy missions under `sd_card/groklink/healthcare/missions/*`
   to Flipper `/ext/groklink/missions/`.
3. Optional: merge healthcare blacklist **templates** into active files
   under `/ext/groklink/blacklist/` only after reviewing each entry.
   Templates are **not** auto-loaded; the agent reads fixed names
   `freq_mhz.json`, `gpio_pins.json` only.
4. Reload skills / reboot as needed.

```
sd_card/groklink/healthcare/
  README.md
  blacklist/          # templates - copy with intent
  missions/           # passive only
  skills/             # passive_rx risk_class
```

## 3. Verify (passive only)

```powershell
cd bridge
$env:GROKLINK_PORT = "auto"
$env:GROKLINK_TRANSPORT = "cli"
py -3 -m pip install -e .
py -3 -m groklink.cli connect
py -3 -m groklink.cli status
py -3 -m groklink.cli skill list
py -3 -m groklink.cli mission list
# short passive listen - no TX
py -3 -m groklink.cli hw subghz-rx --freq 433920000 --ms 1000
```

Expect: safety_mode strict, radio_breaker false, no TX env required.

## 4. Default policies for healthcare-adjacent work

| Rule | Value |
|------|--------|
| Autonomous TX missions | Forbidden |
| max_risk_class | passive_rx unless dual-person RoE |
| GROKLINK_ALLOW_TX | Unset / 0 outside Faraday cage |
| Patient data on SD | Forbidden; use private vault process |
| Care decisions from edge metrics | Forbidden |

## 5. Engagement evidence

- Pull audit JSONL via bridge lab tools / mass storage.
- Store unredacted material under private vault (see PRIVATE_VAULT.md).
- Public repos: redacted examples only; no COM ports, names, PHI.

### Phase 2 PC tools (bridge 2.1.2+)

```powershell
# Lab labels only - no PHI
py -3 -m groklink.cli lab engagement-init --operator lab-op1 --engagement ENG-2026-001 --site bench-a --roe-ack
py -3 -m groklink.cli lab engagement-show

# After audit-pull:
py -3 -m groklink.cli lab stamp-audit --input audit.jsonl --out audit_stamped.jsonl

# Casefile picks up engagement from ~/.groklink/engagement.json
py -3 -m groklink.cli lab casefile --dir cases/ENG-2026-001 --title "passive survey" --hypothesis "baseline"

# History exports + anomaly (never auto-TX)
py -3 -m groklink.cli lab export-csv --history history.jsonl --out export.csv
py -3 -m groklink.cli lab export-json --history history.jsonl --out export.json
py -3 -m groklink.cli lab export-fhir --history history.jsonl --out research_bundle.json
py -3 -m groklink.cli lab anomaly --history history.jsonl --out anomaly.json
```

`export-fhir` is an **experimental research-shaped** bundle only. Not for EHR or care.

## 6. TX (only if RoE allows)

1. Faraday cage or manufacturer-approved chamber.
2. Dual operator (or institutional dual control).
3. `GROKLINK_ALLOW_TX=1` on PC.
4. Confirm token per action.
5. Owned or in-scope target file only.
6. Note: default firmware TX path is ack_file, not full encoder.

## 7. Stop conditions

- Unexpected clinical device behavior nearby: stop radio, radio_reset, document.
- Audit integrity concern: stop engagement, preserve SD image.
- Policy pressure to "just TX once" without RoE: refuse.

## 8. See also

- HEALTHCARE_MEDSEC_PLAN.md - full assessment and roadmap
- SAFETY.md - safety model
- MISSIONS.md - mission schema
