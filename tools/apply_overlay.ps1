<#
.SYNOPSIS
  Copy GrokLink firmware overlay into a flipperzero-firmware / Momentum tree
  and register lib/groklink + service package hooks.

.PARAMETER FirmwareRoot
  Path to firmware repository root (contains applications/, lib/, fbt).

.EXAMPLE
  .\tools\apply_overlay.ps1 -FirmwareRoot C:\src\flipper-firmware
#>
param(
    [Parameter(Mandatory = $true)]
    [string]$FirmwareRoot
)

$ErrorActionPreference = "Stop"
$OverlayRoot = Split-Path -Parent $PSScriptRoot
$Src = Join-Path $OverlayRoot "firmware"

if (-not (Test-Path $FirmwareRoot)) {
    throw "FirmwareRoot not found: $FirmwareRoot"
}
if (-not (Test-Path (Join-Path $FirmwareRoot "lib"))) {
    throw "Does not look like a firmware root (missing lib/): $FirmwareRoot"
}

function Copy-Tree($rel) {
    $from = Join-Path $Src $rel
    $to = Join-Path $FirmwareRoot $rel
    if (-not (Test-Path $from)) {
        Write-Warning "Missing overlay path: $from"
        return
    }
    $parent = Split-Path -Parent $to
    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Force -Path $parent | Out-Null
    }
    if (Test-Path $to) {
        Remove-Item -Recurse -Force $to
    }
    Write-Host "Copy $rel"
    Copy-Item -Path $from -Destination $to -Recurse -Force
}

Copy-Tree "lib\groklink"
Copy-Tree "applications\services\grok_agent"

# Register lib/groklink in lib/SConscript if missing
$libScons = Join-Path $FirmwareRoot "lib\SConscript"
if (Test-Path $libScons) {
    $text = Get-Content $libScons -Raw
    if ($text -notmatch '"groklink"') {
        Write-Host "Patching lib/SConscript to include groklink"
        if ($text -match '"momentum",') {
            $text = $text -replace '("momentum",)', "`$1`r`n        `"groklink`","
        } elseif ($text -match '"toolbox",') {
            $text = $text -replace '("toolbox",)', "`$1`r`n        `"groklink`","
        } else {
            $text = $text -replace '(\n\s*\],\s*\n\))', "`n        `"groklink`",`$1"
        }
        Set-Content -Path $libScons -Value $text -Encoding UTF8
    } else {
        Write-Host "lib/SConscript already lists groklink"
    }
}

# Ensure basic_services provides grok_agent when present
$svcFam = Join-Path $FirmwareRoot "applications\services\application.fam"
if (Test-Path $svcFam) {
    $fam = Get-Content $svcFam -Raw
    if ($fam -notmatch 'grok_agent') {
        Write-Host "Patching services application.fam provides[]"
        $fam = $fam -replace '(provides=\[[^\]]*)(])', "`$1`r`n        `"grok_agent`",`$2"
        Set-Content -Path $svcFam -Value $fam -Encoding UTF8
    }
}

# Link libgroklink into firmware image
$targetJson = Join-Path $FirmwareRoot "targets\f7\target.json"
if (Test-Path $targetJson) {
    $tj = Get-Content $targetJson -Raw
    if ($tj -notmatch '"groklink"') {
        Write-Host "Patching targets/f7/target.json linker_dependencies"
        $tj = $tj -replace '("momentum",)', "`$1`r`n        `"groklink`","
        # official firmware may not have momentum entry
        if ($tj -notmatch '"groklink"') {
            $tj = $tj -replace '("toolbox",)', "`$1`r`n        `"groklink`","
        }
        Set-Content -Path $targetJson -Value $tj -Encoding UTF8
    }
}

$note = Join-Path $FirmwareRoot "GROKLINK_OVERLAY.md"
@"
# GrokLink overlay applied

## Included
- lib/groklink (GROKLINK_USE_FURI)
- applications/services/grok_agent (service + CLI registration)

## Build
``````
./fbt COMPACT=1 DEBUG=0
# Windows:
./fbt.cmd COMPACT=1 DEBUG=0
``````

## SD card
Copy GrokLink-Firmware/sd_card/groklink -> /ext/groklink on the device.

## Verify
- CLI: groklink status
- CLI RPC: groklink rpc {"id":1,"method":"status"}
- PC: groklink connect --port auto --transport cli

## Notes
- SubGHz RX uses furi_hal_subghz async capture (pulse count).
- SubGHz/IR full file TX encoders are intentionally conservative until validated.
- Safety gates remain mandatory for TX-class actions.
"@ | Set-Content -Path $note -Encoding UTF8

Write-Host ""
Write-Host "Overlay complete -> $FirmwareRoot"
Write-Host "See $note"
