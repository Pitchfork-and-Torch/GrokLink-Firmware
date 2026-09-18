# Skill `lab_quiet_band_contrast`

Crafted by GrokLink skill craft.

## Analysis
```json
{
  "event_count": 7,
  "pulse_total": 6003,
  "dominant_freq_hz": 433920000,
  "action_hist": {
    "status": 1,
    "note": 2,
    "subghz_rx": 4
  },
  "suggested_risk": "passive_rx"
}
```

## Deploy
Copy this folder to Flipper SD:
`/ext/groklink/skills/lab_quiet_band_contrast/`

Then: `groklink skill reload` or reboot agent.

## Safety
Default is **passive RX only**. Do not enable TX without authorization and confirm tokens.
