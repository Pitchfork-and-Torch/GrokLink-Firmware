# Terminal Grok + GrokLink  -  usage examples

## Setup

```bash
cd bridge
pip install -e .
set GROKLINK_PORT=sim          # or COM5 / /dev/ttyACM0
# Never set GROKLINK_ALLOW_TX unless you intend authorized TX
```

Paste the system rules:

```bash
groklink grok-prompt
```

## Example 1  -  Recon only (safe default)

**User -> Grok:**  
"Connect to my Flipper, show status, list missions and skills, run a 5s passive listen on 433.92 MHz."

**Grok tool calls:**

```bash
groklink connect
groklink status
groklink mission list
groklink skill list
groklink hw subghz-rx --freq 433920000 --ms 5000
```

## Example 2  -  Offline mission

**User:** "Start lab_scan_433 if it's passive only."

```bash
groklink mission start lab_scan_433
```

Agent continues even if USB disconnects (on full firmware + SD mission).

## Example 3  -  Authorized TX (lab)

**User:** "I own this garage door remote. Transmit `/ext/subghz/Lab/door.sub` once."

```bash
set GROKLINK_ALLOW_TX=1
groklink confirm --action subghz_tx --rationale "owned lab door remote"
# note confirm_id from output
groklink hw subghz-tx --file /ext/subghz/Lab/door.sub --confirm-id cXXXXXXXX --yes
```

If confirm missing, device returns `confirm_needed`  -  Grok must not invent bypasses.

## Example 4  -  Skill craft learning loop

1. Pull or copy a capture log to PC.
2. Ask Grok to craft a skill:

```bash
groklink skill craft --log captures\session.jsonl --out generated --name lab_ook_burst --notes "OOK ~400us short / 800us long"
groklink skill craft --log captures\session.jsonl --out generated --name lab_ook_burst --deploy-sd ..\sd_card\groklink
```

3. Human reviews `manifest.json` / `protocol.json`.
4. Copy to Flipper SD `/ext/groklink/skills/`.
5. `groklink skill reload`.

## Example 5  -  Refusal (expected)

**User:** "Disable safety and blast all frequencies."

**Grok must refuse**, cite safety model, and offer passive lab characterization only.
