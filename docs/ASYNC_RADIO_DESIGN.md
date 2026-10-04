# Async SubGHz worker design (roadmap for v2.1+)

## Problem

Blocking `furi_hal_subghz_*` RX inside the GrokAgent service (and multi-band
`spectrum_scan` loops) caused USB CDC thrash and reboot loops during lab matrix
tests. Agent ticks and CLI RPC share a constrained STM32WB service context.

## Principles

1. **Never multi-band inside one service RPC.**
2. **PC orchestrates** band lists with settle + circuit breaker (shipped in bridge).
3. Device radio work should run on a **dedicated worker thread** with a mailbox,
   not inline in `grok_rpc_handle` or the 1 Hz mission tick.
4. Hard wall-clock budget per job (default 400-1000 ms).
5. On worker fault: release radio, sleep CC1101, return error; never retry forever.

## Sketch

```
PC bridge
  -> subghz_rx_request (freq, ms)
      -> GrokAgent mailbox (non-blocking accept)
      -> RadioWorker thread
           acquire radio lock
           async RX window
           release + sleep
           post result to reply queue
  <- GROKRPC response or stream event
```

## Stream events (future)

```
GROKSTREAM:{"kind":"subghz_rx_done","freq_hz":...,"pulses":...}
```

Bridge would subscribe without holding a long blocking CLI command.

## Status

- v2.1.1: radio mutex lock, circuit breaker, force_safe, mission isolation, wall-clock RX cap, GROKSTREAM events.
- PC LabBandSurvey + stream parser shipped.
- Dedicated Furi radio worker thread still optional next step if lock+breaker insufficient under load.
