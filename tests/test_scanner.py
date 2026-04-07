"""Tests for the Terraform plan scanner and security checks."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from cloudsentry_cli.checks import (
    check_s3_public_acl,
    check_sg_open_ingress,
)
from cloudsentry_cli.scanner import _is_active_change, scan_plan


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_plan(resource_changes: list) -> dict:
    """Return a minimal Terraform plan JSON structure."""
    return {
        "format_version": "1.2",
        "terraform_version": "1.7.0",
        "resource_changes": resource_changes,
    }


def _write_plan(tmp_path: Path, resource_changes: list) -> str:
    """Write a plan JSON to *tmp_path* and return the file path string."""
    plan_file = tmp_path / "tfplan.json"
    plan_file.write_text(json.dumps(_make_plan(resource_changes)))
    return str(plan_file)


# ---------------------------------------------------------------------------
# check_sg_open_ingress
# ---------------------------------------------------------------------------

class TestCheckSgOpenIngress:
    def test_ssh_open_to_world_is_high(self):
        after = {
            "ingress": [
                {
                    "from_port": 22,
                    "to_port": 22,
                    "cidr_blocks": ["0.0.0.0/0"],
                    "ipv6_cidr_blocks": [],
                }
            ]
        }
        findings = check_sg_open_ingress("aws_security_group", "example", after)
        assert len(findings) == 1
        assert findings[0]["severity"] == "HIGH"
        assert "22" in findings[0]["issue"]

    def test_rdp_open_to_world_is_high(self):
        after = {
            "ingress": [
                {
                    "from_port": 3389,
                    "to_port": 3389,
                    "cidr_blocks": ["0.0.0.0/0"],
                    "ipv6_cidr_blocks": [],
                }
            ]
        }
        findings = check_sg_open_ingress("aws_security_group", "rdp_sg", after)
        assert len(findings) == 1
        assert findings[0]["severity"] == "HIGH"
        assert "3389" in findings[0]["issue"]

    def test_ssh_restricted_cidr_no_finding(self):
        after = {
            "ingress": [
                {
                    "from_port": 22,
                    "to_port": 22,
                    "cidr_blocks": ["10.0.0.0/8"],
                    "ipv6_cidr_blocks": [],
                }
            ]
        }
        findings = check_sg_open_ingress("aws_security_group", "private_sg", after)
        assert findings == []

    def test_non_sg_resource_ignored(self):
        after = {"ingress": [{"from_port": 22, "to_port": 22, "cidr_blocks": ["0.0.0.0/0"]}]}
        findings = check_sg_open_ingress("aws_instance", "web", after)
        assert findings == []

    def test_ipv6_open_detected(self):
        after = {
            "ingress": [
                {
                    "from_port": 22,
                    "to_port": 22,
                    "cidr_blocks": [],
                    "ipv6_cidr_blocks": ["::/0"],
                }
            ]
        }
        findings = check_sg_open_ingress("aws_security_group", "ipv6_sg", after)
        assert len(findings) == 1

    def test_port_range_covering_ssh_detected(self):
        after = {
            "ingress": [
                {
                    "from_port": 0,
                    "to_port": 65535,
                    "cidr_blocks": ["0.0.0.0/0"],
                    "ipv6_cidr_blocks": [],
                }
            ]
        }
        findings = check_sg_open_ingress("aws_security_group", "wide_open", after)
        # Both port 22 and 3389 are in range → 2 findings
        assert len(findings) == 2

    def test_standalone_sg_rule_ingress(self):
        after = {
            "type": "ingress",
            "from_port": 22,
            "to_port": 22,
            "cidr_blocks": ["0.0.0.0/0"],
            "ipv6_cidr_blocks": [],
        }
        findings = check_sg_open_ingress("aws_security_group_rule", "allow_ssh", after)
        assert len(findings) == 1

    def test_standalone_sg_rule_egress_ignored(self):
        after = {
            "type": "egress",
            "from_port": 22,
            "to_port": 22,
            "cidr_blocks": ["0.0.0.0/0"],
            "ipv6_cidr_blocks": [],
        }
        findings = check_sg_open_ingress("aws_security_group_rule", "egress_rule", after)
        assert findings == []


# ---------------------------------------------------------------------------
# check_s3_public_acl
# ---------------------------------------------------------------------------

class TestCheckS3PublicAcl:
    def test_public_read_is_high(self):
        findings = check_s3_public_acl("aws_s3_bucket", "my_bucket", {"acl": "public-read"})
        assert len(findings) == 1
        assert findings[0]["severity"] == "HIGH"

    def test_private_acl_no_finding(self):
        findings = check_s3_public_acl("aws_s3_bucket", "safe_bucket", {"acl": "private"})
        assert findings == []

    def test_non_s3_resource_ignored(self):
        findings = check_s3_public_acl("aws_instance", "web", {"acl": "public-read"})
        assert findings == []


# ---------------------------------------------------------------------------
# _is_active_change
# ---------------------------------------------------------------------------

class TestIsActiveChange:
    def test_create_is_active(self):
        assert _is_active_change(["create"]) is True

    def test_update_is_active(self):
        assert _is_active_change(["update"]) is True

    def test_delete_is_not_active(self):
        assert _is_active_change(["delete"]) is False

    def test_no_op_is_not_active(self):
        assert _is_active_change(["no-op"]) is False

    def test_create_before_destroy_is_active(self):
        assert _is_active_change(["create", "delete"]) is True


# ---------------------------------------------------------------------------
# scan_plan (integration-style)
# ---------------------------------------------------------------------------

class TestScanPlan:
    def test_open_sg_detected(self, tmp_path):
        rc = [
            {
                "type": "aws_security_group",
                "name": "web_sg",
                "change": {
                    "actions": ["create"],
                    "after": {
                        "ingress": [
                            {
                                "from_port": 22,
                                "to_port": 22,
                                "cidr_blocks": ["0.0.0.0/0"],
                                "ipv6_cidr_blocks": [],
                            }
                        ]
                    },
                },
            }
        ]
        findings = scan_plan(_write_plan(tmp_path, rc))
        assert len(findings) == 1
        assert findings[0]["severity"] == "HIGH"

    def test_delete_action_skipped(self, tmp_path):
        rc = [
            {
                "type": "aws_security_group",
                "name": "old_sg",
                "change": {
                    "actions": ["delete"],
                    "after": None,
                },
            }
        ]
        findings = scan_plan(_write_plan(tmp_path, rc))
        assert findings == []

    def test_clean_plan_no_findings(self, tmp_path):
        rc = [
            {
                "type": "aws_s3_bucket",
                "name": "secure_bucket",
                "change": {
                    "actions": ["create"],
                    "after": {"acl": "private"},
                },
            }
        ]
        findings = scan_plan(_write_plan(tmp_path, rc))
        assert findings == []

    def test_missing_file_raises(self):
        with pytest.raises(FileNotFoundError):
            scan_plan("/nonexistent/path/tfplan.json")

    def test_multiple_resources_multiple_findings(self, tmp_path):
        rc = [
            {
                "type": "aws_security_group",
                "name": "sg1",
                "change": {
                    "actions": ["create"],
                    "after": {
                        "ingress": [
                            {
                                "from_port": 22,
                                "to_port": 22,
                                "cidr_blocks": ["0.0.0.0/0"],
                                "ipv6_cidr_blocks": [],
                            }
                        ]
                    },
                },
            },
            {
                "type": "aws_s3_bucket",
                "name": "pub_bucket",
                "change": {
                    "actions": ["create"],
                    "after": {"acl": "public-read-write"},
                },
            },
        ]
        findings = scan_plan(_write_plan(tmp_path, rc))
        assert len(findings) == 2


# ---------------------------------------------------------------------------
# CLI integration via argparse
# ---------------------------------------------------------------------------

class TestCLI:
    def test_scan_returns_0_on_clean_plan(self, tmp_path):
        """Exit code 0 when no findings meet the threshold."""
        from cloudsentry_cli.cli import build_parser, cmd_scan

        plan_file = _write_plan(
            tmp_path,
            [
                {
                    "type": "aws_s3_bucket",
                    "name": "safe",
                    "change": {"actions": ["create"], "after": {"acl": "private"}},
                }
            ],
        )
        out_file = str(tmp_path / "report.json")
        parser = build_parser()
        args = parser.parse_args(["scan", "--input", plan_file, "--output", out_file])
        rc = cmd_scan(args)
        assert rc == 0
        assert Path(out_file).exists()

    def test_scan_returns_1_on_high_finding(self, tmp_path):
        """Exit code 1 when a HIGH finding exists and threshold is HIGH."""
        from cloudsentry_cli.cli import build_parser, cmd_scan

        plan_file = _write_plan(
            tmp_path,
            [
                {
                    "type": "aws_security_group",
                    "name": "bad_sg",
                    "change": {
                        "actions": ["create"],
                        "after": {
                            "ingress": [
                                {
                                    "from_port": 22,
                                    "to_port": 22,
                                    "cidr_blocks": ["0.0.0.0/0"],
                                    "ipv6_cidr_blocks": [],
                                }
                            ]
                        },
                    },
                }
            ],
        )
        out_file = str(tmp_path / "report.json")
        parser = build_parser()
        args = parser.parse_args(
            ["scan", "--input", plan_file, "--fail-on", "HIGH", "--output", out_file]
        )
        rc = cmd_scan(args)
        assert rc == 1

    def test_scan_returns_0_when_threshold_is_critical_and_only_high(self, tmp_path):
        """A HIGH finding does NOT fail when threshold is CRITICAL."""
        from cloudsentry_cli.cli import build_parser, cmd_scan

        plan_file = _write_plan(
            tmp_path,
            [
                {
                    "type": "aws_security_group",
                    "name": "sg_high",
                    "change": {
                        "actions": ["create"],
                        "after": {
                            "ingress": [
                                {
                                    "from_port": 22,
                                    "to_port": 22,
                                    "cidr_blocks": ["0.0.0.0/0"],
                                    "ipv6_cidr_blocks": [],
                                }
                            ]
                        },
                    },
                }
            ],
        )
        out_file = str(tmp_path / "report.json")
        parser = build_parser()
        args = parser.parse_args(
            ["scan", "--input", plan_file, "--fail-on", "CRITICAL", "--output", out_file]
        )
        rc = cmd_scan(args)
        assert rc == 0

    def test_report_json_contents(self, tmp_path):
        """Verify the JSON report structure is correct."""
        from cloudsentry_cli.cli import build_parser, cmd_scan

        plan_file = _write_plan(
            tmp_path,
            [
                {
                    "type": "aws_security_group",
                    "name": "bad_sg",
                    "change": {
                        "actions": ["create"],
                        "after": {
                            "ingress": [
                                {
                                    "from_port": 22,
                                    "to_port": 22,
                                    "cidr_blocks": ["0.0.0.0/0"],
                                    "ipv6_cidr_blocks": [],
                                }
                            ]
                        },
                    },
                }
            ],
        )
        out_file = str(tmp_path / "report.json")
        parser = build_parser()
        args = parser.parse_args(["scan", "--input", plan_file, "--output", out_file])
        cmd_scan(args)

        report = json.loads(Path(out_file).read_text())
        assert report["tool"] == "cloudsentry-cli"
        assert report["summary"]["total_findings"] >= 1
        assert report["summary"]["high"] >= 1
        assert isinstance(report["findings"], list)
