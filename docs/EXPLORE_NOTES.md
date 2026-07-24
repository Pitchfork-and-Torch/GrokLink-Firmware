# Explore notes  -  learning log (public)

Passive characterization only unless otherwise noted. No operator PII.

## Session health patterns

| Observation | Interpretation |
|-------------|----------------|
| `status` ok, agent up, strict | Core service healthy |
| COM drops mid-session | USB CDC flaky under load / device reboot / host contention |
| `skill_list` Invalid control character | Pretty-printed SD manifests + broken JSON string extract; **fixed** in firmware parsers + bridge `loads_json_lenient` |
| `mission_list` empty-looking ids | Same parse bug until reflash with fixed `gl_mission_parse_json` |
| `skill_reload` may drop COM | Storage rescan can re-enumerate USB; reopen port after ~2s |
| `mission_count` >= 1 | SD missions folder populated |
| Reboot loops with autonomous SubGHz | Service-stack radio  -  disabled auto-start in stable build |

## Spectrum lessons (aggregated passive samples)

| Band | Leisure 1s edges (example) | Working theory |
|------|----------------------------|----------------|
| 300 MHz | **780** (dense) | Site-specific activity or path response; do not assume quiet |
| 315 MHz | ~40 | Low-moderate |
| **433.92 MHz** | **169-317** consistent | Primary local ISM / remotes / EMI floor |
| 868 / 915 MHz | ~2 | Near quiet at this site/antenna |

Earlier sessions also saw 433.92 as multi-thousand edges/s in longer or denser windows; absolute rate varies by window and local TX. Pulse counts are **not** protocol IDs.

**Skills grown:** `sigint_433_activity_watch`, `lab_quiet_band_contrast`, `lab_band_survey_leisure`.

## Product growth

1. Prefer **short RX** (1 s) over long blocking listens on USB control plane.
2. **One serial owner** (qFlipper *or* bridge).
3. Missions = explicit start; no boot-time radio.
4. TX = allow env + confirm + real owned `.sub` + fail closed on missing file.
5. Bridge must brace-balance GROKRPC and tolerate scrubbed control chars from older firmware.
6. SD JSON string extract must not double-advance quotes (pretty-print trap).

## Ethics

Educational / authorized research. Listen first. Human in the loop.
