# Changelog

## 2.1.3

Lab radio circuit breaker force-trip: radio_trip RPC, gl_radio_breaker_force_open,
CLI groklink radio trip|status|reset. Field report docs/FIELD_REPORT_V2.1.3.md.
DFU published as Release asset GrokLink-v2.1.3.dfu (not in git).

## 2.1.2

Healthcare / MedSec Phase 2 (PC research tools, not a medical device): engagement
context (operator/engagement IDs), audit stamp, casefile fields, RF anomaly score
(never auto-TX), history export CSV/JSON, experimental FHIR-shaped research bundle,
CLI lab commands, tests.

## 2.1.1

Force-complete lab stack: radio force_safe, mission radio isolation, stream parser,
oracle/audit-pull/vault/curriculum/device skill deploy/metrics HTML, proto API2, polish.

Healthcare / MedSec Phase 1 (research only, not a medical device): plan + operator
runbook, passive skill packs (medsec_passive_ism_watch, fac_rf_baseline_watch,
med_asset_uid_inventory), passive missions, blacklist templates under
sd_card/groklink/healthcare/.

## 2.1.0

Full lab stack: radio lock + circuit breaker, GROKSTREAM events, PC lab tools
(graph, mission compile, audit HTML, casefiles, heartbeat, SD deploy, reflect,
sim replay, metrics), expanded skills, BLE/vault/router docs.

## 2.0.2 / bridge 2.1

- Device RX cooldown between passive radio RPCs (rate_limited).
- PC-side safe multi-band survey with circuit breaker (`groklink hw spectrum`).
- RF history store + delta detection; skill `lab_rf_delta_watch`.
- Async radio worker design doc; lab poster asset.

## 2.0.1

Stability release: disable multi-band `spectrum_scan` in the agent service path
(reboot-loop mitigation), cap RPC RX at 1 s, skip per-RX SD capture writes by
default. Use short single-band `subghz_rx` from the PC bridge instead.

## 2.0.0

GrokLink Firmware v2 - Flipper Zero agent overlay with gated RPC API 2, multi-band
spectrum scan, frequency/duration bounds, IR and GPIO RPC, honest TX ack mode,
fixed skill/mission JSON parsers, larger agent stack, and PC bridge 2.0 for
authorized educational hardware research.

## 1.0.0

GrokLink Firmware - Flipper Zero agent overlay with gated RPC, missions, skills,
and a PC bridge for authorized educational hardware research.

Includes deployment and full explore reports, passive RF skills, reboot-loop
hardening, ASCII-clean docs, promo assets on Releases, and agent-skills notes.
