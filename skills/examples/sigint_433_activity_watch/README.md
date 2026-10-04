# Skill `sigint_433_activity_watch`

Crafted by GrokLink skill craft.

## Analysis
```json
{
  "event_count": 11,
  "pulse_total": 26700,
  "dominant_freq_hz": 433920000,
  "action_hist": {
    "deployment": 1,
    "subghz_rx": 10
  },
  "suggested_risk": "passive_rx"
}
```

## Deploy
Copy this folder to Flipper SD:
`/ext/groklink/skills/sigint_433_activity_watch/`

Then: `groklink skill reload` or reboot agent.

## Safety
Default is **passive RX only**. Do not enable TX without authorization and confirm tokens.
