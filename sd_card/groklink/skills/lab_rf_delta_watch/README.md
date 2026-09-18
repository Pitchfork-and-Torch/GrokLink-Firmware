# lab_rf_delta_watch

Detect when a lab band becomes unusually hot or quiet versus history.

## Safe usage

```text
groklink hw spectrum --ms 400 --settle 2 --history %USERPROFILE%\.groklink\rf_history.jsonl --label nightly
```

Do **not** use on-device `spectrum_scan` (disabled after reboot loops).

## Deploy (optional on-device seed)

Copy this folder to `/ext/groklink/skills/lab_rf_delta_watch/`.
