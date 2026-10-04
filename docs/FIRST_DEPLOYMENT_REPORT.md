# First Deployment Report  -  World of Signals

**GrokLink Firmware v1.0 - Educational RF characterization - Passive-first**

> Classification for this document: **public / educational**  
> No operator identity, no home coordinates, no device serials, no capture payloads that identify third parties.

---

## 1. Mission intent

Validate that a Flipper Zero running **GrokLink** can act as a **scriptable, safety-gated sensor** under PC-side Grok control: observe the local ISM environment, quantify activity, and turn observations into **passive skills**  -  without unauthorized access to third-party systems.

This is **signals characterization**, not offensive SIGINT against others.

---

## 2. Stack under test

| Layer | Component | Result |
|-------|-----------|--------|
| Device OS | Flipper firmware + GrokAgent service | Agent running |
| Safety | Strict mode, confirm tokens for TX class | RX allowed; TX gated |
| Storage | SD `/ext/groklink` | Present; skills load |
| PC bridge | `groklink` CLI over USB VCP (`cli` transport) | Status / skills / RX operational |
| Skill craft | Offline analysis -> skill package | `sigint_433_activity_watch` generated |

---

## 3. Method

1. Confirm agent health (`status`).
2. Enumerate skills / missions.
3. **Passive** multi-band 1 s listens: 300 / 315 / 433.92 / 868.35 / 915 MHz.
4. Deep passive samples on the loudest band (433.92 MHz): 3x2 s + 5x1 s.
5. Aggregate pulse-edge counts (async SubGHz capture).
6. Craft a **passive_rx** skill from the survey log.
7. Document TX path architecture (confirm + file TX); full encoder remains conservative in v1.0.

No third-party access systems were targeted. No jamming. No continuous high-power TX campaign.

---

## 4. Observations

### 4.1 Agent health (representative)

- `agent_running`: true  
- `safety_mode`: strict  
- `sd_present`: true  
- `skill_count`: >= 1 (`lab_pulse_counter`)  
- `mission_count`: 0 until mission JSON is present on SD  

### 4.2 Band sweep (1 s each)

| Freq (MHz) | Pulse edges | Qualitative |
|------------|-------------|-------------|
| 300.00 | ~150 | Low-moderate |
| 315.00 | ~1 | Quiet |
| **433.92** | **~2900** | **Dominant** |
| 868.35 | ~2 | Quiet |
| 915.00 | ~2 | Quiet |

### 4.3 433.92 MHz deep samples

| Mode | Results (pulse edges) |
|------|------------------------|
| 3 x 2 s | ~5578, ~5772, ~6375 (rising, dense) |
| 5 x 1 s | ~2938-3146 (stable ~3k / s) |
| Other sessions | ~3.2k-3.5k / 2 s; longer windows scale up |

**Character:** Continuous, high edge density on 433.92 with low variance in short bursts  -  consistent with a **busy band or elevated noise floor**, not a single isolated button press.

### 4.4 Skills learned / tracked

| Skill ID | Risk | Origin |
|----------|------|--------|
| `lab_pulse_counter` | passive_rx | Seed skill |
| `sigint_433_activity_watch` | passive_rx | Crafted from first deployment survey |

Crafted skill intent: periodic passive 433.92 observation, log pulse activity, **no TX**.

---

## 5. Analysis & theories

### Theory A  -  Dense local 433 ISM traffic
Cheap sensors, remotes, weather stations, and power-line-adjacent gadgets often share 433.92-class bands. Continuous edge counts can reflect **multiple weak OOK sources** overlapping in time.

### Theory B  -  EMI / desense masquerading as "traffic"
Switching PSUs, LEDs, USB hosts, and monitors can inject energy that an OOK async path still **counts as edges**. The near-silence of 315 / 868 / 915 **supports either** a true 433-centric environment **or** path-specific coupling into the 433 front-end.

### Theory C  -  Mixed floor + occasional remotes
A high baseline (~3k edges/s) with modest variance leaves room for **bursts on top of noise**. Distinguishing requires timing histograms / raw captures (future skill / FAP), not counts alone.

**Working conclusion:**  
Treat **433.92 as the primary band of interest** for this deployment site. Prefer **variance tracking and controlled experiments** (move device, power-cycle nearby gear, test **owned** remotes) before claiming a specific protocol family.

---

## 6. TX path (authorized research posture)

v1.0 policy:

- TX-class actions require **PC allow** + **device confirm token** + audit.  
- File TX encoder is **intentionally conservative** until fully validated (missing `.sub` -> deny; path present may ack without full RF blast depending on build flags).  
- Operators must only TX toward **owned / authorized** systems.

### 6.1 Live gate validation (lab)

With `GROKLINK_ALLOW_TX=1` on the PC bridge:

| Step | Result |
|------|--------|
| `subghz_tx` without token | **`confirm_needed`** (deny) |
| `confirm` for `subghz_tx` | Issues short-lived `confirm_id` |
| Pre-fix firmware `confirm_id` parse | Broken (same JSON string bug as edu_ack) -> TX still denied until reflash |
| Post-fix firmware | Parses `confirm_id` + edu_ack correctly |
| Missing `.sub` file | Deny / fail closed (no silent RF) |

First deployment prioritized **listening and learning**. Full multi-protocol TX campaigns remain out of scope without owned capture files and a reflash containing the JSON parse fix.

---

## 7. Lessons for the product

| Lesson | Action |
|--------|--------|
| Bridge timeouts too short for multi-second RX | Default timeout raised (~12 s) |
| `edu_ack` JSON parse bug | Fixed string extractor in GrokRPC |
| Empty missions confuse operators | Document SD layout; ship example mission |
| Pulse counts  protocol ID | Emphasize educational limits in docs |
| Serial exclusivity | Only one of qFlipper CLI / bridge at a time |

---

## 8. Ethics reminder

GrokLink is for **authorized educational and research use**.  
Do not use captures or skills to attack systems you do not own or administer.  
When in doubt: **listen only**.

---

## 9. Next experiments (recommended)

1. Controlled **owned-remote** click during a 2 s RX; measure delta above baseline.  
2. Spatial move / rotation of the Flipper; re-run band sweep.  
3. Install `sigint_433_activity_watch` on SD; reload skills.  
4. Add an autonomous **passive** mission for hourly 10 s 433 samples.  
5. Phase-B: on-device pulse histograms -> PC classifier.

---

*Report generated for the GrokLink open-source project. Environment-specific absolute paths and personal identifiers intentionally omitted.*
