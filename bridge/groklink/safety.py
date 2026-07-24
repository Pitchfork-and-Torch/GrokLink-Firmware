"""PC-side safety gates (mirror device policy)."""

from __future__ import annotations

import os
import sys
from dataclasses import dataclass


class SafetyError(RuntimeError):
    pass


@dataclass
class PcSafetyPolicy:
    allow_tx: bool = False
    interactive: bool = True

    @classmethod
    def from_env(cls) -> "PcSafetyPolicy":
        return cls(
            allow_tx=os.environ.get("GROKLINK_ALLOW_TX", "0") == "1",
            interactive=sys.stdin.isatty(),
        )

    def require_tx_allowed(self, action: str, *, yes: bool = False) -> None:
        if not self.allow_tx:
            raise SafetyError(
                f"TX-class action '{action}' blocked. "
                "Set GROKLINK_ALLOW_TX=1 only for authorized lab use."
            )
        if yes:
            return
        if not self.interactive:
            raise SafetyError("Non-interactive session requires --yes after GROKLINK_ALLOW_TX=1")
        print(
            "\n*** LEGAL WARNING ***\n"
            "You are about to request an ACTIVE TRANSMIT / drive action.\n"
            "Only proceed if you own the target or have written authorization.\n"
        )
        ans = input(f"Type YES to confirm '{action}': ").strip()
        if ans != "YES":
            raise SafetyError("Operator did not confirm TX")
