# med_asset_uid_inventory

**NOT A MEDICAL DEVICE.** Owned tags / authorized inventory study only.

GrokLink NFC poller is conservative. Prefer **stock Flipper NFC** for UID reads,
then log results via mission notes, PC casefile, or private vault.

## Hard rules

- Read-only unless separate written authorization for write.
- Never write or emulate tags on in-use clinical stock or implant-related media.
- No patient identifiers in public logs.

## Deploy

Copy to `/ext/groklink/skills/med_asset_uid_inventory/`.

## Workflow

1. Operator reads owned tag with stock NFC app.
2. Record UID + asset ID in private vault / casefile.
3. Optional: PC export to inventory CSV (not built into firmware).
