# GrokLink Python Bridge

PC-side controller for GrokLink Firmware.

## Install

```bash
cd bridge
python -m venv .venv
# Windows
.venv\Scripts\activate
pip install -e .
```

## Environment

| Variable | Meaning |
|----------|---------|
| `GROKLINK_PORT` | Serial port (e.g. `COM5`, `/dev/ttyACM0`) |
| `GROKLINK_ALLOW_TX` | Must be `1` to enable TX-class commands |
| `GROKLINK_BAUD` | Default `115200` (Flipper CDC ignores baud but library needs it) |

## CLI

```bash
groklink ports
groklink connect
groklink status
groklink confirm --action subghz_tx
groklink hw subghz-rx --freq 433920000 --ms 5000
groklink mission list
groklink skill list
groklink skill craft --log ../captures/sample.jsonl --out ./generated_skill
```

## Safety

TX requires:

1. `GROKLINK_ALLOW_TX=1`
2. Interactive confirmation (or `--yes` after env allow)
3. Device-side confirm token

Educational use on **authorized targets only**.
