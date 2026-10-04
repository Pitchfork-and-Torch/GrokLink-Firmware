"""
PC-side multi-band SubGHz survey with circuit breaker.

Never uses on-device spectrum_scan (disabled after reboot loops).
Issues one short subghz_rx per band, reopens transport between bands,
and aborts after consecutive COM/link failures.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Optional

# Lab bands from live research (safe window 281-928 MHz)
DEFAULT_LAB_BANDS_HZ = [
    300_000_000,
    303_875_000,
    315_000_000,
    390_000_000,
    433_000_000,
    433_920_000,
    434_420_000,
    868_350_000,
    915_000_000,
]


@dataclass
class CircuitBreaker:
    """Stop radio work after N consecutive link failures."""

    max_failures: int = 2
    failures: int = 0
    open: bool = False
    reason: str = ""

    def record_success(self) -> None:
        self.failures = 0
        self.open = False
        self.reason = ""

    def record_failure(self, reason: str) -> None:
        self.failures += 1
        self.reason = reason
        if self.failures >= self.max_failures:
            self.open = True


@dataclass
class BandSample:
    freq_hz: int
    duration_ms: int
    pulses: Optional[int]
    ok: bool
    safety: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None
    ts: float = field(default_factory=time.time)


@dataclass
class SurveyResult:
    samples: list[BandSample]
    breaker_open: bool = False
    breaker_reason: str = ""
    started_ts: float = 0.0
    ended_ts: float = 0.0

    def as_dict(self) -> dict[str, Any]:
        return {
            "started_ts": self.started_ts,
            "ended_ts": self.ended_ts,
            "breaker_open": self.breaker_open,
            "breaker_reason": self.breaker_reason,
            "samples": [
                {
                    "freq_hz": s.freq_hz,
                    "duration_ms": s.duration_ms,
                    "pulses": s.pulses,
                    "ok": s.ok,
                    "safety": s.safety,
                    "message": s.message,
                    "error": s.error,
                    "ts": s.ts,
                }
                for s in self.samples
            ],
        }

    def table_rows(self) -> list[tuple[str, str, str]]:
        rows = []
        for s in self.samples:
            mhz = f"{s.freq_hz / 1e6:.3f}"
            p = str(s.pulses) if s.pulses is not None else "-"
            st = "ok" if s.ok else (s.safety or s.error or "fail")
            rows.append((mhz, p, st))
        return rows


class LabBandSurvey:
    """
    Safe multi-band survey driven from the PC.

    rx_callable: function(freq_hz, duration_ms) -> dict response
    """

    def __init__(
        self,
        rx_callable: Callable[[int, int], dict[str, Any]],
        *,
        bands_hz: Optional[list[int]] = None,
        duration_ms: int = 400,
        settle_s: float = 2.0,
        breaker: Optional[CircuitBreaker] = None,
    ) -> None:
        self.rx = rx_callable
        self.bands = list(bands_hz or DEFAULT_LAB_BANDS_HZ)
        self.duration_ms = max(100, min(duration_ms, 1000))
        self.settle_s = max(0.5, settle_s)
        self.breaker = breaker or CircuitBreaker(max_failures=2)

    @staticmethod
    def _pulses(resp: dict[str, Any]) -> Optional[int]:
        meta = resp.get("json_meta")
        if isinstance(meta, str):
            try:
                return int(json.loads(meta).get("pulses"))
            except Exception:
                return None
        return None

    def run(self) -> SurveyResult:
        result = SurveyResult(samples=[], started_ts=time.time())
        for hz in self.bands:
            if self.breaker.open:
                result.breaker_open = True
                result.breaker_reason = self.breaker.reason
                break
            try:
                resp = self.rx(hz, self.duration_ms)
            except Exception as e:
                self.breaker.record_failure(str(e)[:160])
                result.samples.append(
                    BandSample(
                        freq_hz=hz,
                        duration_ms=self.duration_ms,
                        pulses=None,
                        ok=False,
                        error=str(e)[:160],
                    )
                )
                if self.breaker.open:
                    result.breaker_open = True
                    result.breaker_reason = self.breaker.reason
                time.sleep(self.settle_s)
                continue

            if not resp or resp.get("ok") is not True:
                # Rate limit is not a link failure
                safety = (resp or {}).get("safety")
                msg = (resp or {}).get("message") or (resp or {}).get("error")
                if safety == "rate_limited":
                    self.breaker.record_success()
                    result.samples.append(
                        BandSample(
                            freq_hz=hz,
                            duration_ms=self.duration_ms,
                            pulses=None,
                            ok=False,
                            safety=safety,
                            message=str(msg) if msg else "rx cooldown",
                        )
                    )
                    time.sleep(self.settle_s + 0.5)
                    continue
                # link-ish failure
                err = str(msg or "rx failed")
                if "COM" in err or "ClearComm" in err or "WriteFile" in err or "port" in err.lower():
                    self.breaker.record_failure(err)
                result.samples.append(
                    BandSample(
                        freq_hz=hz,
                        duration_ms=self.duration_ms,
                        pulses=None,
                        ok=False,
                        safety=safety,
                        message=err,
                    )
                )
                if self.breaker.open:
                    result.breaker_open = True
                    result.breaker_reason = self.breaker.reason
                time.sleep(self.settle_s)
                continue

            self.breaker.record_success()
            result.samples.append(
                BandSample(
                    freq_hz=hz,
                    duration_ms=resp.get("duration_ms") or self.duration_ms,
                    pulses=self._pulses(resp),
                    ok=True,
                    safety=resp.get("safety"),
                )
            )
            time.sleep(self.settle_s)

        result.ended_ts = time.time()
        return result
