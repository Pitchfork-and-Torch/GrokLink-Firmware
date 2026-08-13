# Safety Model

## Principles

1. **Educational / authorized use only**
2. **Default deny** for transmit and GPIO output
3. **Human in the loop** for elevated risk
4. **Audit everything** that touches hardware
5. **Fail closed** on policy or integrity errors

## Action classes

| Class | Examples | Default policy |
|-------|----------|----------------|
| `INFO` | Status, version, battery | Allow |
| `PASSIVE_RX` | SubGHz listen, NFC read (user tag), IR learn | Allow if not blacklisted band |
| `ACTIVE_TX` | SubGHz TX, IR blast, RFID emulate | Deny + confirm + allowlist duty cycle |
| `GPIO_OUT` | Drive pins | Deny + confirm |
| `CONTACT` | iButton write | Deny + confirm |
| `SYSTEM` | Clear blacklist, disable safety | Deny + **on-device physical confirm only** |

## Confirm tokens

PC elevates with a short-lived token:

```
groklink confirm --action subghz_tx --ttl 60
# returns confirm_id
groklink hw subghz tx --file burst.sub --confirm <confirm_id>
```

On-device: long-press OK on confirmation dialog for local missions.

## Blacklists

Files under `/ext/groklink/blacklist/`:

- `freq_mhz.json`  -  forbidden TX center frequencies / bands
- `protocols.json`  -  forbidden protocol names (e.g. access-control families in lab policy)
- `gpio_pins.json`  -  pins that must never be driven

RPC cannot empty these without `SYSTEM` + physical confirm.

## Duty cycle & rate limits

Agent enforces:

- Max continuous TX time (default 2 s)
- Cool-down between TX (default 5 s)
- Max missions/hour (config)

## Logging

Every check logs:

```json
{"ts":1710000000,"actor":"rpc|agent|cli","action":"subghz_tx","result":"deny|allow|confirm_needed","reason":"...","hash":"..."}
```

Integrity: optional SHA-256 chain in `logs/audit_chain.sha256`.

## Operator checklist

- [ ] I own or am authorized on all targets
- [ ] I understand local spectrum / privacy law
- [ ] TX allow is intentional (`GROKLINK_ALLOW_TX`)
- [ ] Blacklists match my lab policy
- [ ] Audit log is retained for the engagement
- [ ] If healthcare-adjacent: I follow HEALTHCARE_OPERATOR_RUNBOOK.md (passive default; not a medical device)

## Healthcare-adjacent research

See `docs/HEALTHCARE_MEDSEC_PLAN.md`. Prefer `passive_rx` missions only.
Do not use GrokLink for clinical care, diagnosis, or patient-connected actuation.
Optional TX deny templates: `sd_card/groklink/healthcare/blacklist/`.
