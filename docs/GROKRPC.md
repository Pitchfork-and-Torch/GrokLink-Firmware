# GrokRPC Protocol

GrokRPC extends Flipper's existing protobuf RPC with a GrokLink message group. Framing remains compatible with Flipper's length-delimited protobuf over USB CDC / BLE serial.

## Transport

| Transport | Notes |
|-----------|-------|
| USB | Primary; same port as qFlipper |
| BLE | Optional; lower throughput; for status/missions |

## Session

```
GrokSessionStart { client_name, client_version, capabilities[], request_elevated }
  -> GrokSessionStartResponse { session_id, agent_version, safety_mode, features[] }

GrokSessionEnd { session_id }
```

## Core methods

| Method | Direction | Class |
|--------|-----------|-------|
| `GrokStatus` | req/resp | INFO |
| `GrokConfirm` | req/resp | elevates token |
| `GrokMissionList/Load/Start/Stop` | req/resp | INFO / SYSTEM |
| `GrokHwSubGhzRx/Tx` | req/resp + stream | PASSIVE_RX / ACTIVE_TX |
| `GrokHwNfc` | req/resp | PASSIVE_RX / ACTIVE_TX |
| `GrokHwIr` | req/resp | PASSIVE_RX / ACTIVE_TX |
| `GrokHwGpio` | req/resp | GPIO_OUT |
| `GrokSkillList/Install/Reload` | req/resp | SYSTEM for install |
| `GrokStream` | server push | events, samples, audit |
| `GrokLogPull` | req/resp | INFO |

## Stream events

```
GrokStreamEvent {
  ts_ms, kind,   // "subghz_raw" | "audit" | "mission" | "metric"
  payload_bytes  // or json_utf8 for control events
}
```

## Compatibility

Bridge first probes official Flipper RPC `system.ping` / `system.device_info`. If Grok RPC app is missing, bridge enters **compat mode** (storage + limited CLI).

## Schema

Canonical schema: [`schemas/groklink.proto`](../schemas/groklink.proto)
