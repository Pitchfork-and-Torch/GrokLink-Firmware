# Skill `lab_band_survey_leisure`

Passive multi-band SubGHz survey skill crafted from a live leisure explore session.

## What it learns about the physical world

| Band | Leisure 1s edges | Character |
|------|------------------|-----------|
| 300 MHz | 780 | Unexpectedly dense (site-specific) |
| 315 MHz | 41 | Low-moderate |
| 433.92 MHz | 169-317 | Consistent activity |
| 868.35 MHz | 2 | Near quiet |
| 915 MHz | 2 | Near quiet |

Pulse edges are **not** decoded packets. Use for site personality / hot-vs-quiet contrast only.

## Deploy

Copy this folder to Flipper SD:

`/ext/groklink/skills/lab_band_survey_leisure/`

Then `groklink skill reload` (after firmware with fixed skill_list parsers preferred) or reboot.

## Safety

**Passive RX only.** No TX. Authorized educational research.
