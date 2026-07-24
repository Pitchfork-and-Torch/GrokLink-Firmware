"""GrokLink CLI  -  terminal entry for humans and agent tool-calling."""

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from groklink import __version__
from groklink.rpc.client import GrokLinkClient, list_serial_ports
from groklink.safety import PcSafetyPolicy, SafetyError
from groklink.skills.craft import craft_skill_from_log, deploy_skill_to_sd_tree

console = Console()
_CLIENT: GrokLinkClient | None = None


def get_client() -> GrokLinkClient:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = GrokLinkClient()
        port = os.environ.get("GROKLINK_PORT", "auto")
        transport = os.environ.get("GROKLINK_TRANSPORT")
        _CLIENT.connect(port, transport=transport)
    return _CLIENT


@click.group()
@click.version_option(__version__, prog_name="groklink")
def main() -> None:
    """GrokLink PC bridge  -  authorized educational / lab use only."""
    pass


@main.command("ports")
def ports_cmd() -> None:
    """List serial ports (highlight likely Flipper)."""
    from groklink.rpc.transport import find_flipper_port

    ps = list_serial_ports()
    likely = find_flipper_port("auto")
    if not ps:
        console.print("[yellow]No serial ports (or pyserial missing). Use GROKLINK_PORT=sim[/]")
        return
    for p in ps:
        mark = "  <- flipper?" if p == likely else ""
        console.print(f"{p}{mark}")


@main.command("connect")
@click.option("--port", default=None, help="Serial port, 'auto', or 'sim'")
@click.option(
    "--transport",
    type=click.Choice(["sim", "cli", "json"], case_sensitive=False),
    default=None,
    help="sim | cli (Flipper VCP) | json",
)
def connect_cmd(port: str | None, transport: str | None) -> None:
    """Open session (edu ack automatic from client)."""
    global _CLIENT
    c = GrokLinkClient()
    resp = c.connect(
        port or os.environ.get("GROKLINK_PORT", "auto"),
        transport=transport or os.environ.get("GROKLINK_TRANSPORT"),
    )
    _CLIENT = c
    console.print(f"[dim]mode={c.mode} port={c.port}[/]")
    console.print_json(data=resp)
    if not resp.get("ok"):
        sys.exit(1)


@main.command("status")
def status_cmd() -> None:
    resp = get_client().status()
    console.print_json(data=resp)


@main.command("confirm")
@click.option("--action", default="subghz_tx", show_default=True)
@click.option("--ttl", default=60, show_default=True)
@click.option("--rationale", default="lab")
def confirm_cmd(action: str, ttl: int, rationale: str) -> None:
    """Issue device-side confirm token for elevated actions."""
    policy = PcSafetyPolicy.from_env()
    try:
        policy.require_tx_allowed(action)
    except SafetyError as e:
        console.print(f"[red]{e}[/]")
        sys.exit(2)
    resp = get_client().confirm(action, ttl=ttl, rationale=rationale)
    console.print_json(data=resp)


@main.group("mission")
def mission_grp() -> None:
    """Mission control."""


@mission_grp.command("list")
def mission_list() -> None:
    resp = get_client().mission_list()
    console.print_json(data=resp)


@mission_grp.command("start")
@click.argument("mission_id")
@click.option("--confirm-id", default=None)
def mission_start(mission_id: str, confirm_id: str | None) -> None:
    resp = get_client().mission_start(mission_id, confirm_id)
    console.print_json(data=resp)


@main.group("skill")
def skill_grp() -> None:
    """Skills."""


@skill_grp.command("list")
def skill_list() -> None:
    console.print_json(data=get_client().skill_list())


@skill_grp.command("reload")
def skill_reload() -> None:
    console.print_json(data=get_client().skill_reload())


@skill_grp.command("craft")
@click.option("--log", "log_path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--out", "out_dir", required=True, type=click.Path(path_type=Path))
@click.option("--name", default=None, help="Skill id/name")
@click.option("--notes", default=None, help="Optional Grok/LLM protocol notes")
@click.option(
    "--deploy-sd",
    default=None,
    type=click.Path(path_type=Path),
    help="Optional path to sd_card/groklink mirror for offline deploy",
)
def skill_craft(
    log_path: Path,
    out_dir: Path,
    name: str | None,
    notes: str | None,
    deploy_sd: Path | None,
) -> None:
    """Analyze a log and generate a skill package (human review before use)."""
    result = craft_skill_from_log(log_path, out_dir, skill_name=name, llm_notes=notes)
    console.print(f"[green]{result.summary}[/]")
    for f in result.files:
        console.print(f"  wrote {f}")
    if deploy_sd:
        target = deploy_skill_to_sd_tree(result.out_dir, deploy_sd)
        console.print(f"[cyan]Deployed mirror -> {target}[/]")


@main.group("hw")
def hw_grp() -> None:
    """Hardware ops (gated)."""


@hw_grp.command("subghz-rx")
@click.option("--freq", "freq_hz", default=433920000, show_default=True)
@click.option("--ms", "duration_ms", default=1000, show_default=True)
def hw_rx(freq_hz: int, duration_ms: int) -> None:
    """Passive RX (default 1s; device clamps max)."""
    console.print_json(data=get_client().subghz_rx(freq_hz, duration_ms))


@hw_grp.command("spectrum")
@click.option("--ms", "duration_ms", default=400, show_default=True, help="Per-band duration")
@click.option("--settle", default=2.0, show_default=True, help="Seconds between bands")
@click.option(
    "--history",
    "history_path",
    default=None,
    type=click.Path(path_type=Path),
    help="Append survey to JSONL history for delta detection",
)
@click.option("--label", default="", help="Optional label stored in history")
@click.option("--device", is_flag=True, help="Call on-device spectrum_scan (usually disabled)")
def hw_spectrum(duration_ms: int, settle: float, history_path: Path | None, label: str, device: bool) -> None:
    """Safe multi-band survey (PC-orchestrated, circuit breaker).

    Default path does NOT use on-device spectrum_scan (reboot-loop risk).
    """
    from groklink.research.survey import LabBandSurvey
    from groklink.research.history import RfHistoryStore
    from groklink.research.delta import detect_deltas
    from serial.tools import list_ports
    from groklink.rpc.transport import FlipperCliTransport, find_flipper_port

    if device:
        console.print("[yellow]On-device spectrum_scan is disabled on stable firmware.[/]")
        console.print_json(data=get_client().spectrum_scan(duration_ms))
        return

    port = os.environ.get("GROKLINK_PORT", "auto")
    if port == "auto":
        port = find_flipper_port("auto")
    if not port or port == "sim":
        console.print("[red]No Flipper port (set GROKLINK_PORT)[/]")
        sys.exit(2)

    def rx(freq_hz: int, ms: int) -> dict:
        # Fresh open per band - avoids sticky CDC state
        t = FlipperCliTransport(port=port, baud=115200, timeout=max(14.0, ms / 1000.0 + 8.0))
        t.open()
        try:
            return t.request_json(
                {"id": int(time.time() * 1000) % 100000, "method": "subghz_rx", "freq_hz": freq_hz, "duration_ms": ms}
            )
        finally:
            t.close()

    import time

    survey = LabBandSurvey(rx, duration_ms=duration_ms, settle_s=settle)
    result = survey.run()
    console.print_json(data=result.as_dict())
    table = Table(title="PC lab survey (safe multi-band)")
    table.add_column("MHz")
    table.add_column("pulses", justify="right")
    table.add_column("status")
    for mhz, pulses, st in result.table_rows():
        table.add_row(mhz, pulses, st)
    console.print(table)
    if result.breaker_open:
        console.print(f"[red]Circuit breaker OPEN:[/] {result.breaker_reason}")
        console.print("[yellow]Stopped further radio. Do not retry aggressively.[/]")

    if history_path:
        store = RfHistoryStore(history_path)
        payload = result.as_dict()
        store.append_survey(payload, label=label)
        base = store.baseline_by_freq(exclude_last_n_surveys=1)
        deltas = detect_deltas(payload.get("samples") or [], base)
        console.print(f"[cyan]{deltas.summary}[/]")
        console.print_json(data=deltas.as_dict())
        # metrics + auto graph into vault
        from groklink.research.metrics import LocalMetrics
        from groklink.research.vault import ensure_vault
        from groklink.research.graph import build_personality_html
        from groklink.research.oracle import rank_hottest

        vault = ensure_vault()
        LocalMetrics(vault / "metrics" / "metrics.jsonl").from_survey(payload, label=label)
        build_personality_html(history_path, vault / "history" / "personality.html")
        console.print_json(data=rank_hottest(history_path))
        if result.breaker_open:
            # auto-reflect
            ref = vault / "raw" / f"reflect_{int(time.time())}.md"
            ref.write_text(
                f"# Auto reflect\n\nbreaker: {result.breaker_reason}\n",
                encoding="utf-8",
            )
            console.print(f"[yellow]Auto-reflect[/] {ref}")


@hw_grp.command("ir-rx")
@click.option("--ms", "duration_ms", default=1000, show_default=True)
def hw_ir_rx(duration_ms: int) -> None:
    """Passive IR listen."""
    console.print_json(data=get_client().ir_rx(duration_ms))


@hw_grp.command("gpio-read")
@click.option("--pin", required=True, type=int)
def hw_gpio_read(pin: int) -> None:
    console.print_json(data=get_client().gpio_read(pin))


@hw_grp.command("subghz-tx")
@click.option("--file", "file_path", required=True)
@click.option("--confirm-id", default=None, help="Device confirm token; omit to auto-issue one")
@click.option("--freq", "freq_hz", default=0)
@click.option("--yes", is_flag=True, help="Skip interactive YES if GROKLINK_ALLOW_TX=1")
def hw_tx(file_path: str, confirm_id: str | None, freq_hz: int, yes: bool) -> None:
    """Active TX path (v2: file-ack unless full encoder linked)  -  authorized only."""
    policy = PcSafetyPolicy.from_env()
    try:
        policy.require_tx_allowed("subghz_tx", yes=yes)
    except SafetyError as e:
        console.print(f"[red]{e}[/]")
        sys.exit(2)
    client = get_client()
    if not confirm_id:
        conf = client.confirm("subghz_tx", ttl=120, rationale="cli_auto_confirm")
        console.print_json(data=conf)
        if not conf.get("ok"):
            sys.exit(2)
        confirm_id = conf.get("confirm_id")
        if not confirm_id:
            console.print("[red]No confirm_id from device[/]")
            sys.exit(2)
    console.print_json(data=client.subghz_tx(file_path, confirm_id, freq_hz=freq_hz))


@main.command("methods")
def methods_cmd() -> None:
    """List device RPC methods (v2)."""
    console.print_json(data=get_client().methods())


@main.group("radio")
def radio_grp() -> None:
    """Device radio lock / circuit breaker (lab)."""


@radio_grp.command("status")
def radio_status_cmd() -> None:
    console.print_json(data=get_client().radio_status())


@radio_grp.command("trip")
@click.option("--reason", default="lab_trip", show_default=True)
def radio_trip_cmd(reason: str) -> None:
    """Force circuit breaker OPEN (blocks SubGHz until reset or cooldown)."""
    console.print_json(data=get_client().radio_trip(reason))
    st = get_client().status()
    console.print_json(data={"status_radio_breaker": st.get("radio_breaker"), "status": st})


@radio_grp.command("reset")
def radio_reset_cmd() -> None:
    """Close/reset circuit breaker and force radio idle."""
    console.print_json(data=get_client().radio_reset())


@main.group("lab")
def lab_grp() -> None:
    """Lab research tools (PC-side graphs, cases, deploy, heartbeat)."""


@lab_grp.command("graph")
@click.option("--history", "history_path", required=True, type=click.Path(path_type=Path))
@click.option(
    "--out",
    "out_html",
    default=None,
    type=click.Path(path_type=Path),
    help="HTML output (default: next to history)",
)
def lab_graph(history_path: Path, out_html: Path | None) -> None:
    """Build RF personality HTML from survey history."""
    from groklink.research.graph import build_personality_html

    out = out_html or Path(history_path).with_suffix(".html")
    path = build_personality_html(history_path, out)
    console.print(f"[green]Wrote[/] {path}")


@lab_grp.command("mission-compile")
@click.option("--id", "mission_id", required=True)
@click.option("--freq", "freq_hz", default=433920000, show_default=True)
@click.option("--ms", "duration_ms", default=400, show_default=True)
@click.option("--out", "out_dir", required=True, type=click.Path(path_type=Path))
def lab_mission_compile(mission_id: str, freq_hz: int, duration_ms: int, out_dir: Path) -> None:
    """Compile a passive single-band mission JSON (autonomous=false)."""
    from groklink.research.mission_compile import compile_passive_mission, write_mission

    m = compile_passive_mission(mission_id, freq_hz=freq_hz, duration_ms=duration_ms)
    path = write_mission(out_dir, m)
    console.print_json(data=m)
    console.print(f"[green]Wrote[/] {path}")


@lab_grp.command("audit-html")
@click.option("--input", "inp", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--out", "out_html", required=True, type=click.Path(path_type=Path))
def lab_audit_html(inp: Path, out_html: Path) -> None:
    """Render audit JSONL (or device log export) to HTML."""
    from groklink.research.audit_dash import parse_audit_lines, build_audit_html

    rows = parse_audit_lines(Path(inp).read_text(encoding="utf-8", errors="replace"))
    path = build_audit_html(rows, out_html)
    console.print(f"[green]Wrote[/] {path} ({len(rows)} rows)")


@lab_grp.command("casefile")
@click.option("--dir", "case_dir", required=True, type=click.Path(path_type=Path))
@click.option("--title", required=True)
@click.option("--hypothesis", required=True)
@click.option("--notes", default="")
@click.option("--capture", "capture_path", default=None, type=click.Path(path_type=Path))
@click.option("--operator", "operator_id", default="", help="Override operator_id")
@click.option("--engagement", "engagement_id", default="", help="Override engagement_id")
@click.option("--site", "site_label", default="", help="Override site_label")
def lab_casefile(
    case_dir: Path,
    title: str,
    hypothesis: str,
    notes: str,
    capture_path: Path | None,
    operator_id: str,
    engagement_id: str,
    site_label: str,
) -> None:
    """Create a lab CASEFILE.json with optional capture SHA-256 + engagement IDs."""
    from groklink.research.casefile import create_casefile

    path = create_casefile(
        case_dir,
        title=title,
        hypothesis=hypothesis,
        notes=notes,
        capture_path=capture_path,
        operator_id=operator_id,
        engagement_id=engagement_id,
        site_label=site_label,
    )
    console.print(f"[green]Wrote[/] {path}")


@lab_grp.command("replay")
@click.option("--log", "log_path", required=True, type=click.Path(exists=True, path_type=Path))
def lab_replay(log_path: Path) -> None:
    """Replay a public explore jsonl without hardware (digital twin stats)."""
    from groklink.research.sim_replay import replay_jsonl

    console.print_json(data=replay_jsonl(log_path))


@lab_grp.command("heartbeat")
@click.option("--log", "log_path", default=None, type=click.Path(path_type=Path))
@click.option("--radio", is_flag=True, help="Optional single gentle 300ms RX (default off)")
def lab_heartbeat(log_path: Path | None, radio: bool) -> None:
    """Status-only heartbeat (optional gentle radio)."""
    from groklink.research.heartbeat import run_heartbeat

    client = get_client()

    def status():
        return client.status()

    def rx(freq, ms):
        return client.subghz_rx(freq, ms)

    row = run_heartbeat(
        status,
        rx_fn=rx if radio else None,
        allow_radio=radio,
        log_path=log_path,
    )
    console.print_json(data=row)
    if not row.get("ok"):
        sys.exit(1)


@lab_grp.command("deploy-skills")
@click.option(
    "--src",
    "skills_src",
    required=True,
    type=click.Path(exists=True, path_type=Path),
    help="Folder of skill packages (e.g. skills/examples)",
)
@click.option(
    "--sd",
    "sd_root",
    required=True,
    type=click.Path(path_type=Path),
    help="SD mirror groklink root (e.g. sd_card/groklink)",
)
def lab_deploy_skills(skills_src: Path, sd_root: Path) -> None:
    """Copy skill packages into an SD card mirror tree."""
    from groklink.research.sd_deploy import deploy_skills_tree

    deployed = deploy_skills_tree(skills_src, sd_root)
    console.print(f"[green]Deployed {len(deployed)} skills[/]: {', '.join(deployed)}")


@lab_grp.command("reflect")
@click.option("--log", "log_path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--out", "out_md", required=True, type=click.Path(path_type=Path))
def lab_reflect(log_path: Path, out_md: Path) -> None:
    """Write a short postmortem markdown from a failed suite/jsonl log."""
    text = Path(log_path).read_text(encoding="utf-8", errors="replace")
    fails = sum(1 for line in text.splitlines() if '"ok": false' in line or '"ok":false' in line)
    com_errs = sum(1 for line in text.splitlines() if "ClearComm" in line or "Access is denied" in line)
    md = f"""# Suite reflect

Source: `{Path(log_path).name}`

## Signals
- false/ok failures (string scan): {fails}
- COM/link error lines: {com_errs}

## Recommended patches
1. Prefer PC `hw spectrum` with settle + circuit breaker; never on-device multi-band.
2. After 2 link errors, stop and `radio_reset` / wait for USB re-enum.
3. Do not skill_reload mid radio matrix.
4. Cap RX at 400-1000 ms per band.

## Next skill updates
- Document failure in ops_port_and_promo_lessons
- Add casefile for this run
"""
    Path(out_md).parent.mkdir(parents=True, exist_ok=True)
    Path(out_md).write_text(md, encoding="utf-8")
    console.print(f"[green]Wrote[/] {out_md}")


@lab_grp.command("oracle")
@click.option("--history", "history_path", required=True, type=click.Path(path_type=Path))
def lab_oracle(history_path: Path) -> None:
    """Rank hottest bands from history (contrast oracle)."""
    from groklink.research.oracle import rank_hottest

    console.print_json(data=rank_hottest(history_path))


@lab_grp.command("audit-pull")
@click.option("--out", "out_path", required=True, type=click.Path(path_type=Path))
@click.option("--html", "html_path", default=None, type=click.Path(path_type=Path))
def lab_audit_pull(out_path: Path, html_path: Path | None) -> None:
    """Pull device audit.jsonl over USB CLI and optionally render HTML."""
    from groklink.rpc.transport import find_flipper_port
    from groklink.research.audit_pull import pull_audit_via_serial
    from groklink.research.audit_dash import parse_audit_lines, build_audit_html

    port = os.environ.get("GROKLINK_PORT", "auto")
    if port == "auto":
        port = find_flipper_port("auto")
    if not port:
        console.print("[red]No Flipper port[/]")
        sys.exit(2)
    path = pull_audit_via_serial(port, out_path)
    console.print(f"[green]Pulled[/] {path}")
    if html_path:
        rows = parse_audit_lines(path.read_text(encoding="utf-8", errors="replace"))
        build_audit_html(rows, html_path)
        console.print(f"[green]HTML[/] {html_path}")


@lab_grp.command("vault-init")
def lab_vault_init() -> None:
    """Create private ~/.groklink/vault layout."""
    from groklink.research.vault import ensure_vault

    root = ensure_vault()
    console.print(f"[green]Vault ready[/] {root}")


@lab_grp.command("curriculum")
@click.option("--mark", "mark_id", default=None, type=int, help="Mark lesson id done")
def lab_curriculum(mark_id: int | None) -> None:
    """RF literacy curriculum progress."""
    from groklink.research.curriculum import curriculum_state, mark_lesson

    prog = Path.home() / ".groklink" / "curriculum_progress.txt"
    if mark_id is not None:
        mark_lesson(prog, mark_id)
    console.print_json(data=curriculum_state(prog))


@lab_grp.command("device-deploy-skills")
@click.option(
    "--src",
    "skills_src",
    default=None,
    type=click.Path(exists=True, path_type=Path),
    help="Default: repo sd_card/groklink/skills",
)
def lab_device_deploy(skills_src: Path | None) -> None:
    """Push skill packages to Flipper SD via serial (small text files)."""
    from groklink.rpc.transport import find_flipper_port
    from groklink.research.device_deploy import deploy_all_skills

    port = os.environ.get("GROKLINK_PORT", "auto")
    if port == "auto":
        port = find_flipper_port("auto")
    if not port:
        console.print("[red]No Flipper[/]")
        sys.exit(2)
    src = skills_src or (Path(__file__).resolve().parents[2] / "sd_card" / "groklink" / "skills")
    if not src.exists():
        src = Path(__file__).resolve().parents[2] / "skills" / "examples"
    result = deploy_all_skills(port, src)
    console.print_json(data=result)
    console.print("[cyan]Tip: groklink skill reload (may drop COM briefly)[/]")


@lab_grp.command("metrics-html")
@click.option("--metrics", "metrics_path", required=True, type=click.Path(path_type=Path))
@click.option("--out", "out_html", required=True, type=click.Path(path_type=Path))
def lab_metrics_html(metrics_path: Path, out_html: Path) -> None:
    from groklink.research.metrics_html import build_metrics_html

    path = build_metrics_html(metrics_path, out_html)
    console.print(f"[green]Wrote[/] {path}")


@lab_grp.command("engagement-init")
@click.option("--operator", "operator_id", required=True, help="Lab operator label (no PHI)")
@click.option("--engagement", "engagement_id", required=True, help="Engagement / case id")
@click.option("--site", "site_label", default="", help="Site label (no street address/PHI)")
@click.option("--roe-ack", is_flag=True, help="Mark written RoE acknowledged")
@click.option("--path", "eng_path", default=None, type=click.Path(path_type=Path))
def lab_engagement_init(
    operator_id: str,
    engagement_id: str,
    site_label: str,
    roe_ack: bool,
    eng_path: Path | None,
) -> None:
    """Save PC engagement context (operator/engagement IDs) for casefile + audit stamp."""
    from groklink.research.engagement import save_engagement

    path = save_engagement(
        operator_id=operator_id,
        engagement_id=engagement_id,
        site_label=site_label,
        roe_ack=roe_ack,
        path=eng_path,
    )
    console.print(f"[green]Engagement saved[/] {path}")
    console.print("[dim]Not a medical device. No PHI in operator/site labels.[/]")


@lab_grp.command("engagement-show")
@click.option("--path", "eng_path", default=None, type=click.Path(path_type=Path))
def lab_engagement_show(eng_path: Path | None) -> None:
    """Show current engagement context."""
    from groklink.research.engagement import load_engagement

    console.print_json(data=load_engagement(eng_path))


@lab_grp.command("stamp-audit")
@click.option("--input", "inp", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--out", "out_path", required=True, type=click.Path(path_type=Path))
def lab_stamp_audit(inp: Path, out_path: Path) -> None:
    """Stamp audit JSONL rows with engagement_id / operator_id (PC-side)."""
    from groklink.research.engagement import stamp_audit_jsonl

    console.print_json(data=stamp_audit_jsonl(inp, out_path))


@lab_grp.command("export-csv")
@click.option("--history", "history_path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--out", "out_csv", required=True, type=click.Path(path_type=Path))
def lab_export_csv(history_path: Path, out_csv: Path) -> None:
    """Export RF history samples to CSV (research only; not clinical)."""
    from groklink.research.export_lab import export_history_csv

    path = export_history_csv(history_path, out_csv)
    console.print(f"[green]Wrote[/] {path}")


@lab_grp.command("export-json")
@click.option("--history", "history_path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--out", "out_json", required=True, type=click.Path(path_type=Path))
def lab_export_json(history_path: Path, out_json: Path) -> None:
    """Export RF history to stamped JSON bundle (research only)."""
    from groklink.research.export_lab import export_history_json

    path = export_history_json(history_path, out_json)
    console.print(f"[green]Wrote[/] {path}")


@lab_grp.command("export-fhir")
@click.option("--history", "history_path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--out", "out_json", required=True, type=click.Path(path_type=Path))
@click.option("--max-obs", default=50, show_default=True)
def lab_export_fhir(history_path: Path, out_json: Path, max_obs: int) -> None:
    """Experimental FHIR-shaped Bundle (research only - NOT for EHR/care)."""
    from groklink.research.export_lab import export_experimental_fhir_bundle

    path = export_experimental_fhir_bundle(history_path, out_json, max_obs=max_obs)
    console.print(f"[green]Wrote[/] {path}")
    console.print("[yellow]Experimental research artifact only. Not a medical device. Do not use for care.[/]")


@lab_grp.command("anomaly")
@click.option("--history", "history_path", required=True, type=click.Path(exists=True, path_type=Path))
@click.option("--out", "out_json", default=None, type=click.Path(path_type=Path))
@click.option("--hot-ratio", default=2.5, show_default=True)
@click.option("--quiet-ratio", default=0.35, show_default=True)
def lab_anomaly(history_path: Path, out_json: Path | None, hot_ratio: float, quiet_ratio: float) -> None:
    """PC RF anomaly score vs history baseline. Never auto-TX. Not threat intel."""
    from groklink.research.anomaly import score_anomaly, write_anomaly_report

    if out_json:
        path = write_anomaly_report(
            history_path, out_json, hot_ratio=hot_ratio, quiet_ratio=quiet_ratio
        )
        console.print(f"[green]Wrote[/] {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
    else:
        data = score_anomaly(history_path, hot_ratio=hot_ratio, quiet_ratio=quiet_ratio)
    console.print_json(data=data)



@lab_grp.command("parse-stream")
@click.option("--input", "inp", required=True, type=click.Path(exists=True, path_type=Path))
def lab_parse_stream(inp: Path) -> None:
    """Extract GROKSTREAM events from a captured serial log."""
    from groklink.research.stream import iter_stream_events

    events = list(iter_stream_events(Path(inp).read_text(encoding="utf-8", errors="replace")))
    console.print_json(data={"count": len(events), "events": events[:50]})


@main.command("grok-prompt")
def grok_prompt() -> None:
    """Print a ready-made system prompt for terminal Grok tool-use."""
    console.print(
        """
You are Grok controlling a Flipper Zero via the `groklink` CLI (GrokLink bridge v2).
Rules:
1. Only operate on authorized / owned targets. Educational research only.
2. Prefer passive RX, status, and `hw spectrum`. Never TX unless the user explicitly authorizes.
3. Before TX: set GROKLINK_ALLOW_TX=1, run `groklink confirm --action subghz_tx`, then `groklink hw subghz-tx`.
4. Use `groklink status`, `methods`, `mission list`, `skill list`, `hw subghz-rx`, `hw spectrum`.
5. After captures, use `groklink skill craft --log <file> --out <dir>` and ask the human to review before deploy.
6. Quote safety denials verbatim; do not attempt to bypass confirmations.
7. TX path may be ack-file mode (gates exercised) unless full radio encoder is linked.
""".strip()
    )


if __name__ == "__main__":
    main()
