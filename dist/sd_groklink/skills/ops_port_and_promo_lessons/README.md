# Skill `ops_port_and_promo_lessons`

Crafted by GrokLink skill craft.

## Analysis
```json
{
  "event_count": 6,
  "pulse_total": 6001,
  "dominant_freq_hz": 433920000,
  "action_hist": {
    "subghz_rx": 3,
    "subghz_tx": 1,
    "promo": 1,
    "status": 1
  },
  "suggested_risk": "passive_rx"
}
```

## Deploy
Copy this folder to Flipper SD:
`/ext/groklink/skills/ops_port_and_promo_lessons/`

Then: `groklink skill reload` or reboot agent.

## Safety
Default is **passive RX only**. Do not enable TX without authorization and confirm tokens.
