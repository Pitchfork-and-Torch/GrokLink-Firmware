# Full exploration report (aggregated)

Public, educational RF characterization and system validation.
No operator identity, no device serials, no private paths.

## 1. System state (live sessions)

Aggregated from successful sessions:

| Metric | Typical value |
|--------|----------------|
| Firmware | groklink-1.0.0 |
| Agent | running |
| Safety | strict |
| SD | present |
| Skills | lab_pulse_counter (+ craft packages on SD seed) |
| Missions | 0-1 depending on SD content |

USB CDC is exclusive: if qFlipper or another serial client holds the port, bridge returns Access denied. Operator must close competing apps.

## 2. Spectrum findings (passive RX only)

### Leisure multi-band survey (1 s windows)

| Band (MHz) | Pulses (edges) | Character |
|------------|----------------|-----------|
| 300 | 780 | Unexpectedly dense |
| 315 | 41 | Low-moderate |
| **433.92** | 199, then 269 / 188 / 169 / 317 / 233 | Dominant consistent activity |
| 868.35 | 2 | Near quiet |
| 915 | 2 | Near quiet |

Capture log (public, scrubbed): `examples/leisure_explore_public.jsonl`.

### Prior sessions

433.92 often showed multi-thousand edges/s in denser samples; 315/868/915 stayed near quiet. Absolute rates vary by time-of-day and local emitters.

### Theories

1. Local 433-class ISM devices, remotes, sensors.
2. Site path / antenna response can make **300 MHz** appear denser than 433 in short windows (leisure finding).
3. EMI / desense coupling into SubGHz front-end.
4. Continuous floor plus occasional bursts.

Pulse counts are **not** protocol IDs and are **not** medical or identity signals.

## 3. TX path (authorized lab)

| Step | Result |
|------|--------|
| TX without confirm | `confirm_needed` (deny) |
| `confirm` issued | token returned (e.g. pattern `c########`) |
| Missing `.sub` file after allow | `tx failed` fail closed |
| No silent wideband TX | enforced |

Real RF TX still requires owned capture files on SD plus firmware TX allow gates. Never invent confirm tokens.

## 4. Stability and software fixes (this cycle)

| Issue | Fix |
|-------|-----|
| `skill_list` / `mission_list` `Invalid control character` | SD pretty-print JSON + double-quote advance in string extract embedded bare newlines; fixed in `gl_skill_load.c` / `gl_mission.c` |
| Bridge defense | `loads_json_lenient` + control-char scrub in `bridge/groklink/rpc/transport.py` |
| Autonomous SubGHz reboot loops | No auto radio missions; larger stack; seed `autonomous=false` |
| Long RX vs RPC timeout | Prefer 1 s RX windows |
| COM exclusivity | Kill competing python/qFlipper before bridge |

**Reflash note:** Correct mission ids and skill versions need the fixed firmware loaders. Bridge scrub unblocks list RPC on older flashes (fields may still show scrubbed garbage until reflash).

## 5. Skills grown

| Skill | Type |
|-------|------|
| lab_pulse_counter | seed passive |
| sigint_433_activity_watch | crafted 433 watch |
| lab_quiet_band_contrast | hot vs quiet bands |
| lab_band_survey_leisure | multi-band 1s leisure survey (300 + 433 hot) |
| ops_port_and_promo_lessons | USB exclusivity + release promo ops |

PC agent skills (operator Grok install): skill-router, skill-reflector, research-synthesis, workflow-orchestrator, code-quality, flipper-pulse-edu (educational BPM only).

## 6. Ethics

Authorized research and education only. Human in the loop. No medical claims from Flipper or DIY sensors.

## 7. Next experiments

1. Reflash DFU with fixed skill/mission JSON parsers; copy full `sd_card/groklink/skills/*` to device.
2. Owned-remote A/B on 433.92 vs baseline floor (confirm-gated TX only with owned `.sub`).
3. Time-series 300 vs 433 contrast (is 300 dense stable or bursty?).
