# Field Report  -  GrokLink v2.1.2 / v2.1.3 tools

**Product:** GrokLink Firmware  
**Field build under test:** groklink-**2.1.3** (device status)  
**Bridge:** 2.1.3  
**Scope:** Authorized educational lab  -  passive first; TX remains gated  
**Classification:** public / educational (no operator PII, no COM ports, no home coordinates)

> NOT A MEDICAL DEVICE. Not for diagnosis, treatment, or patient-connected care.

---

## 1. Purpose

Document live lab verification of tools added after v2.1.1:

1. **Phase 1** healthcare/MedSec passive packs (research only)
2. **Phase 2** PC engagement, export, and anomaly tooling
3. **v2.1.3** device radio circuit-breaker force-trip (`radio_trip`) and CLI

This report is evidence that the control plane and safety interlocks behave as designed under human-in-the-loop lab use.

---

## 2. Stack under test

| Layer | Component | Observed |
|-------|-----------|----------|
| Device | Flipper + GrokAgent | Agent running; strict safety |
| Firmware | groklink-2.1.3 | Status reports matching VERSION string |
| RPC API | 2 | methods include radio_trip / radio_reset / radio_status |
| SD | /ext/groklink skills + missions | skill_count 12; mission_count 3 |
| PC bridge | Python groklink CLI | connect, status, lab tools, radio group |
| DFU | GrokLink-v2.1.3.dfu | Built from Momentum overlay + fbt; Release asset |

---

## 3. New tools inventory

### 3.1 Device radio circuit breaker (v2.1.3)

| Tool | Role |
|------|------|
| `radio_status` | breaker_open, faults, last_fault, can_start, threshold, cooldown_ms |
| `radio_trip` | Force breaker **OPEN** (lab); reason string audited |
| `radio_reset` | Close breaker, clear faults, force radio idle |
| CLI | `groklink radio status|trip|reset` |

**Design:** Threshold 3 faults or force-open; 30 s auto-cooldown may reset open state; SubGHz path refuses start when breaker open.

### 3.2 Phase 2 PC lab tools (v2.1.2+)

| CLI | Role |
|-----|------|
| `lab engagement-init` | Save operator_id / engagement_id / site_label (no PHI) |
| `lab engagement-show` | Show engagement context |
| `lab stamp-audit` | Stamp audit JSONL with engagement fields |
| `lab casefile` | CASEFILE.json with engagement + not_medical_device |
| `lab export-csv` | History samples to CSV |
| `lab export-json` | Stamped JSON history bundle |
| `lab export-fhir` | Experimental research-shaped Bundle only (not for EHR/care) |
| `lab anomaly` | Pulse-edge anomaly vs baseline; **never auto-TX** |

### 3.3 Phase 1 healthcare packs (research only)

| Skill / mission | Risk | Role |
|-----------------|------|------|
| medsec_passive_ism_watch | passive_rx | Lab ISM watch |
| fac_rf_baseline_watch | passive_rx | Facility RF baseline |
| med_asset_uid_inventory | passive_rx | Owned NFC/UID study path |
| fac_rf_snapshot_passive | mission | Multi-band passive snapshot |
| medsec_lab_passive_ism | mission | MedSec passive ISM sample |
| healthcare blacklist templates | policy | Copy-with-intent TX deny examples |

---

## 4. Field procedure (device breaker)

1. Flash `GrokLink-v2.1.3.dfu` (qFlipper Install from file).
2. `groklink connect` then `groklink status`  -  expect groklink-2.1.3.
3. `groklink radio status`  -  breaker_open false, can_start true.
4. `groklink radio trip --reason lab_field`  -  breaker OPEN, faults at threshold.
5. `subghz_rx` short window  -  expect failure / no useful radio start while open.
6. `groklink radio reset`  -  breaker closed, faults 0.
7. Short passive RX again  -  expect ok with pulse metadata.

### 4.1 Observed results (lab session)

| Check | Result |
|-------|--------|
| firmware_version | groklink-2.1.3 |
| agent_version | 2.1.3 |
| radio_trip present in methods | yes |
| breaker after trip | open=true, faults=3, last_fault set |
| status.radio_breaker after trip | true |
| RX while open | ok=false (radio blocked path) |
| after radio_reset | open=false, faults=0, can_start=true |
| RX after reset | ok=true with non-zero pulse edges on 433.92 MHz class sample |

No unauthorized third-party access. No continuous TX campaign. Confirm-gated TX path unchanged (ack_file mode).

---

## 5. Field procedure (PC Phase 2 tools)

```text
# Engagement labels only  -  no PHI
groklink lab engagement-init --operator lab-op --engagement ENG-DEMO --site bench --roe-ack

# After pulling device audit
groklink lab stamp-audit --input audit.jsonl --out audit_stamped.jsonl

# Casefile + exports (research)
groklink lab casefile --dir cases/ENG-DEMO --title "lab baseline" --hypothesis "passive floor"
groklink lab export-csv --history history.jsonl --out export.csv
groklink lab anomaly --history history.jsonl --out anomaly.json
```

**Note:** `export-fhir` is an experimental research artifact only. Do not use for clinical care or EHR ingest without a separate regulated system design.

---

## 6. Safety notes

- Default safety_mode remained **strict** throughout.
- Breaker force-open is for **authorized lab fault injection**, not production hospital floors.
- TX still requires PC allow env + confirm token; full SubGHz encoder is not the default path.
- Healthcare packs are **not** medical devices; pulse edges are not clinical signals.

---

## 7. Artifacts

| Artifact | Location |
|----------|----------|
| DFU | GitHub Release **v2.1.3** asset `GrokLink-v2.1.3.dfu` (not committed to git) |
| Plan | docs/HEALTHCARE_MEDSEC_PLAN.md |
| Runbook | docs/HEALTHCARE_OPERATOR_RUNBOOK.md |
| This report | docs/FIELD_REPORT_V2.1.3.md |
| SD packs | sd_card/groklink/healthcare/ |

---

## 8. Conclusion

v2.1.3 closes the lab loop on **explicit radio circuit-breaker control** (trip/status/reset) with live verification.  
v2.1.2 PC tools add **engagement-stamped evidence**, **exports**, and **anomaly scoring** without enabling auto-TX.  
Together they strengthen GrokLink as an **authorized research control plane**, not a clinical instrument.

Next optional field work: longer multi-session anomaly baselines, dual-operator TX drills in Faraday cage only, fuller NFC inventory FAP (still deferred).
