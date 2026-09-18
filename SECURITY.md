# Security Policy  -  GrokLink Firmware

## Supported research use

GrokLink is intended for:

- Your own devices and lab equipment
- Explicitly authorized penetration tests / red-team engagements
- Classroom / CTF / educational RF and embedded labs

## Reporting issues

If you find a vulnerability that could enable **bypass of safety interlocks**, **silent TX**, or **remote unauthenticated control**, report privately to the repository maintainer. Do not open a public issue with exploit detail.

## Hard security goals (v1.0)

1. No elevated hardware action without a valid confirm token or local UI confirmation.
2. Blacklist cannot be cleared over RPC without physical confirmation on-device.
3. Audit log is append-only on SD; agent refuses to start if log integrity check fails (config option).
4. PC bridge refuses TX-class methods unless `GROKLINK_ALLOW_TX=1` and operator confirms.

## Non-goals

- Cryptographic remote attestation of firmware image (future)
- Full secure boot chain (depends on Flipper platform)
- On-device secret storage beyond Flipper's existing mechanisms
