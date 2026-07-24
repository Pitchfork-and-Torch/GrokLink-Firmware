# GrokLink Architecture

## Design goals

1. **Overlay, don't rewrite**  -  reuse Flipper Furi services (SubGhz, Nfc, Infrared, Gpio, Rpc, Bt, Cli).
2. **SD for bulk data**  -  missions, skills, logs never exhaust internal flash.
3. **Thin agent**  -  deterministic C state machine; no heap thrash.
4. **Fat brain off-device**  -  Grok / PC does analysis and skill synthesis.
5. **Safety by construction**  -  every actuator path goes through `gl_safety_check()`.

## Process / task model

```
Furi services (existing)
  +-- rpc          <- extended with GrokRPC app messages
  +-- cli          <- groklink command group
  +-- storage      <- /ext/groklink/*
  +-- subghz, nfc, infrared, gpio, ...
  +-- grok_agent   <- NEW system service (always-on when enabled)
        +-- mission_scheduler (1 Hz tick)
        +-- skill_registry
        +-- decision_engine (rules)
        +-- audit_logger
```

### Why a service, not only a FAP?

FAPs are unloaded when closed. **Standalone missions** require a resident task that wakes on RTC/timer, runs steps, and sleeps. GrokAgent is a compact system service; the UI FAP is optional for local status.

## Memory budget (targets)

| Component | .text | .bss/.data |
|-----------|-------|------------|
| lib/groklink (safety+mission+skill) | 18-28 KB | 2-3 KB |
| grok_agent service | 12-20 KB | 4-6 KB |
| grok_rpc handlers | 8-15 KB | 1-2 KB |
| Mission runtime buffer |  -  | 1-2 KB |
| **Total add** | **~40-60 KB** | **~8-12 KB** |

Stream heavy captures to SD or PC immediately; do not buffer multi-MB on heap.

## GrokRPC layering

```
PC bridge
  -> framing (length-prefixed protobuf, Flipper-compatible)
    -> standard Flipper RPC (storage, gui, app, ...)
    -> GrokLink extension messages (GrokSession, GrokMission, GrokHw, GrokSkill, GrokStream)
      -> gl_safety_check
        -> Flipper API / workers
```

## Skill module format

```
/ext/groklink/skills/<skill_id>/
  manifest.json      # id, version, hw domains, risk_class, entry
  rules.json         # optional decision rules
  protocol.json      # optional decoder hints for PC
  skill.fap          # optional dynamic FAP
  README.md
```

`risk_class`: `passive_rx` | `active_tx` | `gpio` | `contact` | `system`

## Offline autonomy

When USB/BLE disconnected:

1. Agent loads `config/agent.json` and `missions/*.mission.json`.
2. Scheduler arms missions with `autonomous: true` and schedule windows.
3. Each step still passes safety (blacklist, max TX power, duty cycle).
4. Results append to `logs/mission_<id>_<ts>.jsonl`.
5. On reconnect, bridge syncs logs and can craft skills.

## Failure modes

| Failure | Behavior |
|---------|----------|
| SD missing | Agent runs in degraded mode (no missions, RPC status only) |
| Blacklist corrupt | Fail closed for TX; RX may continue if configured |
| Confirm timeout | Action aborted, audit entry `confirm_timeout` |
| OOM / worker stuck | Abort step, release hardware locks, log `resource_error` |
