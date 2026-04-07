"""
cloudsentry-cli – command line entry point.

Commands
--------
scan    Scan a Terraform plan JSON file for security issues.

Examples
--------
    cloudsentry-cli scan --input tfplan.json
    cloudsentry-cli scan --input tfplan.json --fail-on MEDIUM --output report.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from cloudsentry_cli import __version__
from cloudsentry_cli.scanner import scan_plan

# Severity ordering (higher index = higher severity)
SEVERITY_ORDER = ["LOW", "MEDIUM", "HIGH", "CRITICAL"]


def _severity_index(severity: str) -> int:
    """Return the numeric rank of *severity* (higher = more severe)."""
    try:
        return SEVERITY_ORDER.index(severity.upper())
    except ValueError:
        return -1


def cmd_scan(args: argparse.Namespace) -> int:
    """Execute the ``scan`` sub-command.  Returns an exit code (0 or 1)."""
    try:
        findings = scan_plan(args.input)
    except FileNotFoundError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    threshold_index = _severity_index(args.fail_on)

    # -----------------------------------------------------------------------
    # Classify findings against the threshold
    # -----------------------------------------------------------------------
    failing_findings = [
        f for f in findings
        if _severity_index(f.get("severity", "")) >= threshold_index
    ]

    # -----------------------------------------------------------------------
    # Console summary
    # -----------------------------------------------------------------------
    total = len(findings)
    by_severity: dict[str, int] = {s: 0 for s in SEVERITY_ORDER}
    for f in findings:
        sev = f.get("severity", "").upper()
        if sev in by_severity:
            by_severity[sev] += 1

    print("=" * 60)
    print(f"CloudSentry CLI  v{__version__}")
    print(f"Input : {args.input}")
    print(f"Threshold: {args.fail_on}")
    print("-" * 60)
    print(f"Total findings : {total}")
    for sev in SEVERITY_ORDER:
        print(f"  {sev:<10}: {by_severity[sev]}")
    print("-" * 60)

    if findings:
        for f in findings:
            marker = "✖" if _severity_index(f.get("severity", "")) >= threshold_index else "·"
            print(
                f"  {marker} [{f.get('severity', '?'):8}] "
                f"{f.get('resource', '?')} – {f.get('issue', '')}"
            )
        print("-" * 60)

    if failing_findings:
        print(
            f"FAIL  {len(failing_findings)} finding(s) at or above threshold "
            f"'{args.fail_on}'."
        )
    else:
        print("PASS  No findings at or above threshold.")
    print("=" * 60)

    # -----------------------------------------------------------------------
    # JSON report
    # -----------------------------------------------------------------------
    report = {
        "tool": "cloudsentry-cli",
        "version": __version__,
        "scan_time": datetime.now(timezone.utc).isoformat(),
        "input": str(args.input),
        "fail_on": args.fail_on,
        "summary": {
            "total_findings": total,
            **{s.lower(): by_severity[s] for s in SEVERITY_ORDER},
        },
        "findings": findings,
    }

    output_path = Path(args.output)
    output_path.write_text(json.dumps(report, indent=2))
    print(f"Report written to: {output_path}")

    return 1 if failing_findings else 0


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cloudsentry-cli",
        description="CloudSentry CLI – Terraform plan security scanner",
    )
    parser.add_argument(
        "--version", action="version", version=f"%(prog)s {__version__}"
    )

    sub = parser.add_subparsers(dest="command", required=True)

    # -- scan ----------------------------------------------------------------
    scan_parser = sub.add_parser(
        "scan",
        help="Scan a Terraform plan JSON file.",
    )
    scan_parser.add_argument(
        "--input",
        required=True,
        metavar="FILE",
        help="Path to the Terraform plan JSON file (terraform show -json plan.out).",
    )
    scan_parser.add_argument(
        "--fail-on",
        dest="fail_on",
        default="HIGH",
        choices=SEVERITY_ORDER,
        metavar="SEVERITY",
        help=(
            "Minimum severity that causes a non-zero exit code. "
            "Choices: LOW, MEDIUM, HIGH, CRITICAL. Default: HIGH."
        ),
    )
    scan_parser.add_argument(
        "--output",
        default="cloudsentry_report.json",
        metavar="FILE",
        help="Path for the JSON report output. Default: cloudsentry_report.json.",
    )

    return parser


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "scan":
        sys.exit(cmd_scan(args))
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
