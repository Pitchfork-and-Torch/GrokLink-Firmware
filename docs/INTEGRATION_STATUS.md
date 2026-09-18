# Integration status (v2.0)

## Completed

| Item | Status | Evidence |
|------|--------|----------|
| `lib/groklink` Furi builds | Done | `libgroklink.a` links into firmware |
| Safety / audit / missions / skills | Done | Core symbols in ELF |
| SubGHz RX via `furi_hal_subghz` async capture | Done | `gl_hw_subghz_rx` pulse counter + SD meta |
| GPIO read/write via `furi_hal_resources` | Done | Pin number API |
| IR RX via `infrared_worker` | Done | Timed listen |
| Blacklist load from SD | Done | `gl_blacklist.c` |
| Mission/skill SD loaders | Done | Dir walk under `/ext/groklink` |
| GrokAgent service | Done | In firmware services list |
| CLI + JSON RPC over VCP | Done | `groklink` command + `GROKRPC:` lines |
| Overlay apply script | Done | `tools/apply_overlay.ps1` patches lib + linker |
| Momentum firmware build | Done | Release / local `dist` DFU |
| Python bridge sim + CLI transport | Done | pytest; `--transport cli` |
| Skill craft | Done | generates skill packages |

## Conservative (intentional)

| Item | Why |
|------|-----|
| Full `.sub` / `.ir` TX encoder path | Disabled unless `GROKLINK_SUBGHZ_TX_FULL`; avoid half-broken radio TX |
| Full NFC poller | Returns audit-only; use stock NFC or skill FAP for production reads |
| Protobuf binary RPC merge | JSON CLI path is the v1.0 production control plane |

## Flash path

```powershell
# Rebuild (example paths  -  adjust to your checkout)
.\tools\apply_overlay.ps1 -FirmwareRoot "path\to\flipper-firmware"
cd path\to\flipper-firmware
.\fbt.cmd COMPACT=1 DEBUG=0
# Artifacts: dist\f7-C\*.dfu
```

Flash via qFlipper or `.\fbt.cmd flash_usb_full`.

SD: copy `GrokLink-Firmware\sd_card\groklink` -> `/ext/groklink`.

## PC verify after flash

```powershell
cd path\to\GrokLink-Firmware\bridge
py -3 -m pip install -e .
$env:GROKLINK_PORT = "auto"
$env:GROKLINK_TRANSPORT = "cli"
py -3 -m groklink.cli connect
py -3 -m groklink.cli status
py -3 -m groklink.cli hw subghz-rx --freq 433920000 --ms 3000
```

On-device CLI (USB serial terminal):

```
groklink status
groklink rpc {"id":1,"method":"status"}
groklink mission list
groklink skill list
```

## Symbols present in built ELF

- `grok_agent_app`
- `groklink_cli_register` / `groklink_cli_execute`
- `grok_rpc_handle`
- `groklink_core_init` / `tick` / `deinit`
