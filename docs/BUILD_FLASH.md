# Build & Flash  -  GrokLink v2.1.3

## Prerequisites

- Git, Python 3.10+
- Flipper toolchain via `fbt` (bundled with Momentum / official firmware)
- Windows: PowerShell 5+ or 7
- Device: Flipper Zero (STM32WB55)

## Recommended base

Use a current **Momentum** or official Flipper Zero firmware tree with `fbt` working.

## Apply overlay

```powershell
cd path\to\GrokLink-Firmware
.\tools\apply_overlay.ps1 -FirmwareRoot "path\to\flipper-firmware"
```

The script:

1. Copies `lib/groklink` and `applications/services/grok_agent`
2. Adds `"groklink"` to `lib/SConscript` BuildModules
3. Adds `"groklink"` to `targets/f7/target.json` linker_dependencies
4. Adds `"grok_agent"` to `basic_services` provides

## Build

```powershell
cd path\to\flipper-firmware
.\fbt.cmd COMPACT=1 DEBUG=0
```

Expect services list to include **`grok_agent`**. Artifacts under `dist\f7-C\`.

## Flash

**qFlipper:** Install from file -> select the `.dfu` under `dist\f7-C\` or the GitHub
Release asset `GrokLink-v2.1.3.dfu` (latest). DFU binaries are **not** stored in git;
attach them to Releases only.

**CLI:**

```powershell
cd path\to\flipper-firmware
.\fbt.cmd flash_usb_full
```

## SD card layout

Copy repo `sd_card/groklink` to Flipper SD:

```
/ext/groklink/config/agent.json
/ext/groklink/blacklist/*
/ext/groklink/missions/
/ext/groklink/skills/
/ext/groklink/logs/
```

## Verify

**On device (USB CLI):**

```
groklink status
groklink rpc {"id":1,"method":"status"}
```

**PC bridge:**

```powershell
cd path\to\GrokLink-Firmware\bridge
py -3 -m pip install -e .
# PowerShell:
$env:GROKLINK_PORT = "auto"
$env:GROKLINK_TRANSPORT = "cli"
py -3 -m groklink.cli connect
py -3 -m groklink.cli status
py -3 -m groklink.cli hw subghz-rx --freq 433920000 --ms 3000
```

Audit log: `/ext/groklink/logs/audit.jsonl`

## Official firmware (alternate)

Same overlay script works on stock `flipperzero-firmware` if paths match; re-validate linker_dependencies and fam provides.

## Rollback

Flash stock/Momentum release via qFlipper. SD `groklink/` data remains until deleted.

## See also

- [INTEGRATION_STATUS.md](INTEGRATION_STATUS.md)
- [SAFETY.md](SAFETY.md)
