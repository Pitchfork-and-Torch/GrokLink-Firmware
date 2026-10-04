# GrokLink Firmware v2.0.0

Flipper Zero agent overlay with gated RPC API 2, multi-band spectrum scan, missions, skills, and a PC bridge for authorized educational hardware research.

## Install

1. Flash `GrokLink-v2.0.0.dfu` with qFlipper (Install from file).
2. Copy `sd_card/groklink` to device `/ext/groklink` if needed.
3. PC: `cd bridge && py -3 -m pip install -e .` then set GROKLINK_TRANSPORT=cli.

## Verify

- status shows firmware_version groklink-2.0.0 and api 2
- methods lists spectrum_scan
- hw spectrum runs multi-band passive scan

MIT License.
