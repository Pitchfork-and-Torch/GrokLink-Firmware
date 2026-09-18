# GrokLink v2.0 / v2.0.1

## v2.0.2 / bridge 2.1

- **RX cooldown** on device (`rx cooldown` / `rate_limited`) between passive SubGHz RPCs.
- **PC LabBandSurvey**: multi-band via discrete short `subghz_rx`, settle delays, circuit breaker after 2 link failures.
- CLI: `groklink hw spectrum --ms 400 --settle 2 --history <jsonl>`
- Skill seed: `lab_rf_delta_watch`
- Design: `docs/ASYNC_RADIO_DESIGN.md`
- Lab poster: `assets/groklink-lab-poster.png`

## v2.0.1 (stability)

- **`spectrum_scan` hard-disabled** on device (multi-band SubGHz in the agent service caused USB thrash / reboot loops under lab stress).
- **Single RPC `subghz_rx` capped at 1 s** wall time in the service path.
- **No per-RX SD capture meta writes** by default (optional `GROKLINK_RX_SD_META`).
- Prefer PC-side discrete short `subghz_rx` calls with settle time between bands.

## Highlights (v2.0)

- **RPC API 2** with `methods` / `ping` discovery
- **Spectrum scan** one-shot multi-band passive survey
- **Freq window** 281-928 MHz (out-of-range denied at RPC)
- **RX duration clamp** default 1s, max 5s
- **IR RX + GPIO read/write** on JSON control plane
- **Mission reload** + fixed SD JSON string parsers (skill/mission lists)
- **Honest TX messaging** (`tx_mode: ack_file` until full encoder linked)
- **Larger agent stack** (8 KB) for multi-band work
- **Bridge 2.0**: spectrum CLI, methods, sim parity, lenient JSON transport

## Breaking / behavior changes

| Area | v1 | v2 |
|------|----|----|
| `firmware_version` | groklink-1.0.0 | groklink-2.0.0 |
| Out-of-band RX (0, 2.4G) | allow, 0 pulses | deny `freq out of range` |
| TX success message | `tx queued` | `tx ack (file ok; radio encoder gated)` + `tx_mode` |
| Default CLI RX ms | 5000 | 1000 |

## Flash

1. Build overlay into Momentum: `tools/apply_overlay.ps1`
2. `fbt COMPACT=1 DEBUG=0`
3. Install DFU via qFlipper
4. Copy `sd_card/groklink` to `/ext/groklink`

## Verify

```
groklink rpc {"id":1,"method":"status"}
# expect firmware_version groklink-2.0.0, api 2

groklink rpc {"id":2,"method":"spectrum_scan","duration_ms":500}
groklink rpc {"id":3,"method":"methods"}
```
