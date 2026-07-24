# Missions

Missions are JSON documents on SD that GrokAgent executes offline or on demand.

## Schema (`*.mission.json`)

```json
{
  "id": "lab_scan_433",
  "name": "Lab passive 433 scan",
  "version": 1,
  "autonomous": true,
  "schedule": {
    "type": "interval",
    "every_sec": 3600,
    "window_start": "00:00",
    "window_end": "23:59"
  },
  "safety": {
    "max_risk_class": "passive_rx",
    "require_confirm": false
  },
  "steps": [
    {
      "op": "subghz_rx",
      "freq_hz": 433920000,
      "duration_ms": 30000,
      "save_as": "captures/scan_${ts}.raw"
    },
    {
      "op": "log",
      "message": "scan complete"
    }
  ]
}
```

## Supported ops (v1.0)

| op | Risk | Notes |
|----|------|-------|
| `delay` | INFO | `ms` |
| `log` | INFO | message to mission log |
| `subghz_rx` | PASSIVE_RX | freq, duration, optional modulation |
| `subghz_tx_file` | ACTIVE_TX | path to `.sub`, confirm if required |
| `ir_rx` | PASSIVE_RX | duration |
| `ir_tx_file` | ACTIVE_TX | `.ir` file |
| `nfc_read` | PASSIVE_RX | timeout |
| `gpio_read` | INFO | pin |
| `gpio_write` | GPIO_OUT | pin, level  -  always gated |
| `skill_run` | per skill | `skill_id` + params |
| `decision` | INFO | simple if/then on last metrics |

## Decision step example

```json
{
  "op": "decision",
  "if": { "metric": "subghz_pulse_count", "gte": 10 },
  "then": [{ "op": "log", "message": "activity detected" }],
  "else": [{ "op": "log", "message": "quiet" }]
}
```

Decision engine is intentionally tiny (comparisons only). Complex reasoning stays on PC.
