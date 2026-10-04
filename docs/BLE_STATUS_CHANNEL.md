# BLE status channel (planned)

## Goal

Read agent status while USB is held by qFlipper or another tool.

## Approach

1. Expose a tiny BLE characteristic (status JSON) from Momentum BLE stack when linked.
2. Bridge gains `GROKLINK_TRANSPORT=ble` using OS BLE APIs.
3. **Read-only** first: firmware_version, api, breaker, skill_count.
4. No radio control over BLE until mutual auth + rate limits exist.

## Status

Stubbed as documentation in v2.1. USB CLI remains primary control plane.
