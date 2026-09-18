# Skill `sample_crafted`

Crafted by GrokLink skill craft.

## Analysis
```json
{
  "event_count": 3,
  "pulse_total": 60,
  "dominant_freq_hz": 433920000,
  "action_hist": {
    "mission_done": 1,
    "subghz_rx": 2
  },
  "suggested_risk": "passive_rx"
}
```

## Deploy
Copy this folder to Flipper SD:
`/ext/groklink/skills/sample_crafted/`

Then: `groklink skill reload` or reboot agent.

## Safety
Default is **passive RX only**. Do not enable TX without authorization and confirm tokens.
