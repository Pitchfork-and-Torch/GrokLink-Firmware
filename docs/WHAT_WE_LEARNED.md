# GrokLink Lab Report — What We Learned (Plain English)

**For:** lab operator  
**About:** Flipper Zero + GrokLink firmware + PC bridge  
**Status:** product tree is **groklink-2.1.1** (firmware `GROKLINK_VERSION_STRING` + bridge). Flash the matching DFU if the device still reports an older build. Live lab check previously held **strict** safety when multi-band radio storms were avoided.

---

## The big picture

We built a system where:

- A **Flipper Zero** is the body: radio ears, IR, GPIO, SD card storage.
- A **PC program (GrokLink bridge)** is the brain: talks over USB, issues careful commands, logs results.
- **Skills** are small playbooks (on the SD card and on the PC) that capture what we learn so we can do it again.

Think of it like a lab robot with safety locks: it can listen a lot, and it only “speaks” (transmit) if you unlock the door with a confirm code — and even then, real radio transmit of recorded files is still deliberately limited until a full encoder is finished.

---

## What the hardware actually taught us about the air

In this room, passive “pulse edge counts” (not decoded messages) showed:

1. **This place is not quiet radio-wise.** There is real activity on several bands.
2. **433.92 MHz is busy**, but it is **not always the busiest**.
3. Sometimes **~300 MHz**, **~303.875 MHz**, **~390 MHz**, and **~434.42 MHz** look hotter than classic 433.92 in a short sample.
4. **868 / 915 MHz** usually look nearly empty here.
5. Pulse counts **change over minutes** — so one snapshot is a weather report, not a fingerprint of forever.

Important honesty: **more pulses ≠ “someone is attacking you.”** It can be remotes, sensors, noise, or how the antenna “hears” that day. We never claim medical meaning, identity, or guilt from pulses.

---

## What we learned about software and safety

### Safety that actually worked

- Sessions require an education phrase: you must acknowledge authorized use.
- Transmit without a confirm token is **blocked**.
- Fake confirm tokens are **blocked**.
- Confirm tokens are **one-use**.
- Missing TX file fails closed (no blast into the air).
- After a successful TX *path*, a **cooldown** stops back-to-back TX.
- GPIO write also wants a confirm.
- There is no RPC to wipe blacklists quietly.

### Safety messaging we cleaned up

- Earlier, TX success said “queued” even when only the **file was acknowledged** and the full radio encoder was not really blasting.  
  **Now it says so honestly** (`tx_mode: ack_file`).

### The painful lesson (boot loops)

When we asked the **on-device agent** to do **many radio listens in a row** (`spectrum_scan` multi-band, dense RX matrices), the Flipper could:

- drop USB,
- reboot,
- look like a boot loop if the PC kept retrying.

**Root cause class:** heavy SubGHz work **inside the agent service** on a small microcontroller, stacked with USB serial stress.

**What we did about it:**

- **Disabled** multi-band `spectrum_scan` on the device (returns a clear deny message).
- Cap single on-device RX windows.
- Stop writing a capture file to SD after every tiny RX (that I/O made things worse).
- Build a **PC-side multi-band survey** that listens **one band at a time**, waits between bands, and **stops after two link failures** (circuit breaker).
- Add **RX cooldown** on the device so even single-band RPC cannot be hammered instantly (in 2.0.2 source).

---

## What “v2” means in human terms

**v2.0** added:

- A clearer “API version” so tools know what the device can do.
- Frequency window rules (out of range is denied, not silently empty).
- IR/GPIO hooks on the control plane.
- Better skill/mission name parsing from SD JSON.
- Honest TX messaging.

**v2.0.1** (what you flashed for stability):

- Multi-band on-device spectrum **off** (to stop reboot loops).
- Safer defaults after the stress tests.

**Source now also includes 2.0.2 / bridge 2.1** improvements (need rebuild/reflash for device-side cooldown):

- RX rate limit between listens.
- PC survey + history + “is this band weird today?” delta skill.

---

## Skills and missions we grew

On the SD side (and repo):

- `lab_pulse_counter` — basic listen counter.
- `sigint_433_activity_watch` — 433.92 personality.
- `lab_quiet_band_contrast` — hot vs quiet bands.
- `lab_band_survey_leisure` — multi-band survey notes from leisure explore.
- `ops_port_and_promo_lessons` — USB exclusivity / ops notes.
- `lab_rf_delta_watch` — compare today vs history (PC-driven).

Mission seed: `lab_scan_433` (passive-oriented; autonomous radio off by design).

---

## How to use the system without hurting the Flipper

**Do:**

- One serial owner (close qFlipper when the bridge is talking).
- Short listens (about 0.4–1.0 second).
- Wait a couple seconds between bands.
- Prefer:  
  `groklink hw spectrum --ms 400 --settle 2 --history ...`  
  (PC survey, circuit breaker)
- Status / skill list / mission list anytime.

**Don’t:**

- Hammer multi-band radio from a tight loop.
- Auto-retry forever when USB errors appear.
- Treat pulse spikes as “proof” of anything without context.
- Transmit except with owned files, confirm tokens, and clear authorization.

---

## The poster on the repo

The image **“I FEEL / FOR THE FIRST TIME”** (cyberpunk figure with arms open) is now in the project assets as the lab art / emotional thesis of the work: the agent learning to sense the physical world for the first time — carefully, with gates.

File: `assets/groklink-lab-poster.png` in the GrokLink-Firmware repo.

---

## What we still want next (honest backlog)

1. **Async radio worker** on-device (design written) so long listens don’t freeze the agent.
2. **Optional event stream** over USB so the PC can watch progress without blocking.
3. **Full .sub encoder TX** behind a compile flag + allowlists (still gated).
4. Nightly **RF personality** graphs from history files.
5. BLE status side-channel so USB can be free for other tools.

---

## Bottom line

We learned that **listening carefully is already powerful**, that **this lab has a real RF fingerprint**, that **software safety gates work**, and that **the wrong kind of “do everything at once” radio automation can crash a small device**.  

The path forward is not less ambition — it’s **ambition with circuit breakers**: the PC plans, the Flipper feels the air in short safe sips, and skills remember what “normal” feels like so the system can notice when the world changes.

---

*Authorized educational / lab use only. Not medical advice. Not a surveillance product. Human stays in the loop.*
