# Skill tracking (public)

| Skill ID | Version | Risk | Status | Notes |
|----------|---------|------|--------|-------|
| lab_pulse_counter | 1.0.0 | passive_rx | seed | Basic pulse counter |
| sigint_433_activity_watch | 0.1.0 | passive_rx | crafted | 433.92 activity watch |
| lab_quiet_band_contrast | 0.1.0 | passive_rx | crafted | Hot vs quiet bands |
| lab_band_survey_leisure | 0.1.0 | passive_rx | crafted | Multi-band leisure notes |
| ops_port_and_promo_lessons | 0.1.0 | passive_rx | crafted | USB exclusivity + promo ops |
| lab_rf_delta_watch | 0.1.0 | passive_rx | crafted | PC history delta |
| lab_contrast_oracle | 0.1.0 | passive_rx | crafted | Rank hottest bands from history |
| flipper_rf_literacy | 0.1.0 | passive_rx | crafted | Progressive RF curriculum |
| lab_gpio_event_logger | 0.1.0 | passive_rx | crafted | GPIO logger seed |
| lab_ir_remote_inventory | 0.1.0 | passive_rx | crafted | Owned IR remotes only |
| lab_nfc_study_path | 0.1.0 | passive_rx | crafted | Stock NFC + status/SD |
| ops_sd_deploy | 0.1.0 | passive_rx | crafted | SD skill deploy ops |
| medsec_passive_ism_watch | 0.1.0 | passive_rx | healthcare p1 | MedSec lab passive ISM; not a medical device |
| fac_rf_baseline_watch | 0.1.0 | passive_rx | healthcare p1 | Facility RF baseline; passive only |
| med_asset_uid_inventory | 0.1.0 | passive_rx | healthcare p1 | Owned NFC/UID study path; read-oriented |

Deploy: copy `sd_card/groklink/skills/<id>/` to device `/ext/groklink/skills/<id>/`, then reload/reboot.

Healthcare Phase 1 packs also live under `sd_card/groklink/healthcare/` (templates + runbook).
See `docs/HEALTHCARE_MEDSEC_PLAN.md` and `docs/HEALTHCARE_OPERATOR_RUNBOOK.md`.

Prefer PC `groklink hw spectrum` for multi-band (circuit breaker). On-device multi-band spectrum_scan is disabled.
