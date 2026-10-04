# GrokLink Healthcare and MedSec Plan

**Status:** Phase 1 + Phase 2 PC tools in tree (v2.1.2).  
**Product:** GrokLink Firmware - Flipper Zero agent overlay (not a medical device).  
**Intended use:** Authorized research, education, and MedSec lab work only.

> NOT A MEDICAL DEVICE. Not for diagnosis, treatment, monitoring of care,
> closed-loop control, or patient-connected use. DIY or Flipper sensors must
> never drive clinical decisions.

---

## 0. Grounding (what GrokLink is)

| Layer | Role |
|-------|------|
| GrokAgent | On-device missions, rules, audit, offline schedule |
| GrokRPC | Gated hardware over USB CLI (BLE status planned only) |
| Safety | Default-deny TX/GPIO, confirm tokens, blacklists, duty cycle, radio lock/breaker, fail-closed |
| Skills | SD packages: manifest + rules + optional FAP |
| PC bridge | Survey, history, audit, vault, casefile, skill craft |
| ML | PC/cloud only; no on-device LLM; models never auto-TX |

**Hardware:** STM32WB55 / Flipper Zero. Thin edge, SD for bulk data.  
**TX:** Default `ack_file` (confirm + path); full SubGHz encoder not productized.  
**NFC:** Conservative; stock NFC / FAP for real inventory work.  
**Spectrum:** On-device multi-band scan disabled; prefer PC multi-band survey.

See ARCHITECTURE.md, SAFETY.md, GROKRPC.md, MISSIONS.md, EXTENSIBILITY_ML.md.

---

## 1. Capability map (healthcare lens)

| Domain | Fit | Maturity | Direction |
|--------|-----|----------|-----------|
| Passive SubGHz survey | High for lab RF character | High (pulse edges) | MedSec / facility baselines |
| NFC UID inventory | Medium for owned tags | Low-medium | Read-only asset skills |
| GPIO / DIY sensors | Lab teaching only | Medium | Never clinical care |
| Actuation (TX/IR/GPIO out) | High dual-use risk | TX incomplete by design | Lab Faraday + dual control only |
| Audit + HITL gates | Strong differentiator | High | Engagement evidence |
| Skill craft loop | Playbook generation | Medium-high | Human approve always |
| Clinical monitoring / EHR | Poor on Flipper | N/A | Abandon on this hardware |

---

## 2. Use-case priority

### Pursue (low risk relative)

| ID | Use case | Notes |
|----|----------|--------|
| A | Authorized MedSec lab | Passive first; TX only in cage with RoE |
| C | Facility RF baselines | Engineering spaces; passive only |
| E | BME / cyber education | Safety model is the curriculum |
| B | Owned asset NFC reads | Inventory experiments; no write |
| G | Non-therapeutic research logistics | IRB if subjects involved |

### Defer / abandon

| ID | Use case | Action |
|----|----------|--------|
| D | Bedside diagnostics on Flipper | Abandon for care |
| F | Production legacy-to-EHR bridge on Flipper | Defer pattern to medical-grade edge |
| - | Live-ward TX / spoof of clinical links | Abandon |
| - | Closed-loop therapy / alarms | Abandon |

### Dual-use red lines

- No jamming or spoofing life-critical wireless outside authorized controlled labs.
- No TX on hospital floors without clinical engineering + RF safety approval.
- No write/emulate on in-use medication or implant-related tags.
- No care decisions from Flipper or DIY pulse data.

---

## 3. Barriers (summary)

| Barrier | Implication |
|---------|-------------|
| FDA / MDR | Intended use drives device regulation; do not market for care |
| IEC 60601 | Flipper is not medical electrical equipment |
| HIPAA / GDPR | SD/PC logs not PHI-safe by default; vault + process required |
| FCC / hospital EMC | TX interference risk; passive preferred |
| Liability / IRB | Written RoE and institutional review for on-prem work |
| Form factor | No sterilization path; USB EMI; consumer reliability |

**Split:** Research/education/MedSec lab = feasible with process. Clinical care = not acceptable on this platform.

---

## 4. Roadmap

### Phase 1 (done) - research / education / MedSec tooling

- [x] This plan document
- [x] Healthcare blacklist **templates** (copy into active blacklist with intent)
- [x] Passive missions (facility snapshot, MedSec ISM watch)
- [x] Skill packs: medsec_passive_ism_watch, fac_rf_baseline_watch, med_asset_uid_inventory
- [x] Operator runbook + NOT A MEDICAL DEVICE disclaimers
- [x] Deploy packs to device SD (lab verify)
- [ ] Institution: written RoE before any TX-class work (process)

### Phase 2 (partial - software done) - specialized packs

- [x] Operator ID / engagement ID (PC engagement file + audit stamp + casefile)
- [x] PC RF anomaly score vs history (never auto-TX)
- [x] CSV / JSON history export
- [x] Experimental FHIR-shaped research bundle (explicitly non-clinical)
- [x] CLI: `lab engagement-init|stamp-audit|export-csv|export-json|export-fhir|anomaly`
- [ ] Isolated lab DAQ hat (education hardware - deferred)
- [ ] Fuller NFC inventory FAP (deferred)

### Phase 3 - medical-grade migration

- Keep software patterns (safety classes, confirm, skills, craft loop)
- Move edge off Flipper to 60601-minded hardware if productizing
- Mutual-auth control plane; HL7/FHIR; ISO 14971 risk file

---

## 5. Verdict

GrokLink's **architecture** (gated RPC, risk-class missions, audit, human-approved skill craft) is valuable for MedSec and education. The **Flipper embodiment** is a research appliance, not a clinical device. Highest ROI: authorized lab MedSec, training, passive facility RF, read-only asset experiments.

---

## 6. Related paths

| Path | Purpose |
|------|---------|
| docs/HEALTHCARE_OPERATOR_RUNBOOK.md | Phase 1 how-to |
| sd_card/groklink/healthcare/ | Phase 1 packs and templates |
| docs/SAFETY.md | Core safety model |
| docs/PRIVATE_VAULT.md | Private capture layout |
| docs/AGENT_SKILLS.md | PC skills; non-medical pulse rule |
