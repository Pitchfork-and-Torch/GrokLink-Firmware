# GrokLink Firmware v2.1.3

GrokLink Firmware - Flipper Zero agent overlay with gated RPC, missions, skills, and PC bridge for authorized research.

## Install

1. Flash GrokLink-v2.1.3.dfu with qFlipper (Install from file).
2. Copy sd_card/groklink to the Flipper SD at /ext/groklink/.
3. Install the PC bridge from bridge/ and run: groklink connect; groklink status.

## Highlights

- radio_trip / radio_status / radio_reset circuit breaker control (lab)
- PC lab engagement stamp, export CSV/JSON, experimental research FHIR-shaped export
- RF anomaly score (never auto-TX)
- Healthcare Phase 1 passive packs (not a medical device)

Educational / authorized lab use only. Not a medical device.

MIT License.
