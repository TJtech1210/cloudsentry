"""
Security checks that evaluate a single Terraform resource's ``change.after``
configuration and return a list of finding dicts.

Each finding has the shape::

    {
        "resource": "<type>.<name>",
        "issue":    "<human-readable description>",
        "severity": "LOW" | "MEDIUM" | "HIGH" | "CRITICAL",
        "severity_index": 0 | 1 | 2 | 3,
        "recommendation": "<fix guidance>",
        "remediations": ["<alternative fix 1>", "<alternative fix 2>"],
        "check_id": "<check function id>",
        "documentation_url": "<external docs>",
        "url": "<CloudSentry repo URL>",
    }

To add a new check:
1. Write a function that accepts (resource_type, resource_name, after) and
   returns a list of findings (empty = no issues).
2. Register it in CHECKS below – no other code needs to change.
"""

from __future__ import annotations

from typing import Any

REPOSITORY_URL = "https://github.com/TJtech1210/cloudsentry"
SEVERITY_INDEX = {"LOW": 0, "MEDIUM": 1, "HIGH": 2, "CRITICAL": 3}


# ---------------------------------------------------------------------------
# Individual check functions
# ---------------------------------------------------------------------------

def check_sg_open_ingress(
    resource_type: str,
    resource_name: str,
    after: dict[str, Any],
) -> list[dict[str, Any]]:
    """Flag security group ingress rules open to 0.0.0.0/0 on SSH/RDP ports."""
    findings: list[dict[str, Any]] = []

    if resource_type not in ("aws_security_group", "aws_security_group_rule"):
        return findings

    risky_ports = {22, 3389}
    label = f"{resource_type}.{resource_name}"

    # aws_security_group: ingress is a list of rule blocks
    for rule in after.get("ingress", []):
        from_port = rule.get("from_port", -1)
        to_port = rule.get("to_port", -1)
        cidr_blocks = rule.get("cidr_blocks", [])
        ipv6_cidr_blocks = rule.get("ipv6_cidr_blocks", [])

        for port in risky_ports:
            if _port_in_range(port, from_port, to_port):
                if "0.0.0.0/0" in cidr_blocks or "::/0" in ipv6_cidr_blocks:
                    findings.append({
                        "resource": label,
                        "issue": (
                            f"Port {port} open to the world "
                            f"(0.0.0.0/0 or ::/0) in ingress rule"
                        ),
                        "severity": "HIGH",
                        "severity_index": SEVERITY_INDEX["HIGH"],
                        "recommendation": (
                            "Restrict the CIDR to known IP ranges or use "
                            "AWS Systems Manager Session Manager instead of "
                            "exposing SSH/RDP."
                        ),
                        "remediations": [
                            "Restrict CIDR to specific IP ranges",
                            "Use AWS Systems Manager Session Manager",
                            "Use a bastion host for administrative access",
                        ],
                        "check_id": "check_sg_open_ingress",
                        "documentation_url": (
                            "https://docs.aws.amazon.com/vpc/latest/userguide/"
                            "VPC_SecurityGroups.html"
                        ),
                        "url": REPOSITORY_URL,
                    })

    # aws_security_group_rule (standalone resource)
    if resource_type == "aws_security_group_rule":
        rule_type = after.get("type", "")
        if rule_type == "ingress":
            from_port = after.get("from_port", -1)
            to_port = after.get("to_port", -1)
            cidr_blocks = after.get("cidr_blocks", [])
            ipv6_cidr_blocks = after.get("ipv6_cidr_blocks", [])

            for port in risky_ports:
                if _port_in_range(port, from_port, to_port):
                    if "0.0.0.0/0" in cidr_blocks or "::/0" in ipv6_cidr_blocks:
                        findings.append({
                            "resource": label,
                            "issue": (
                                f"Port {port} open to the world "
                                f"(0.0.0.0/0 or ::/0)"
                            ),
                            "severity": "HIGH",
                            "severity_index": SEVERITY_INDEX["HIGH"],
                            "recommendation": (
                                "Restrict the CIDR to known IP ranges or use "
                                "AWS Systems Manager Session Manager instead of "
                                "exposing SSH/RDP."
                            ),
                            "remediations": [
                                "Restrict CIDR to specific IP ranges",
                                "Use AWS Systems Manager Session Manager",
                                "Use a bastion host for administrative access",
                            ],
                            "check_id": "check_sg_open_ingress",
                            "documentation_url": (
                                "https://docs.aws.amazon.com/vpc/latest/userguide/"
                                "VPC_SecurityGroups.html"
                            ),
                            "url": REPOSITORY_URL,
                        })

    return findings


def check_s3_public_acl(
    resource_type: str,
    resource_name: str,
    after: dict[str, Any],
) -> list[dict[str, Any]]:
    """Flag S3 buckets or ACL resources with a public ACL.

    Covers both the legacy ``aws_s3_bucket`` inline ``acl`` argument and the
    standalone ``aws_s3_bucket_acl`` resource introduced in AWS provider v4+.
    """
    findings: list[dict[str, Any]] = []

    if resource_type not in ("aws_s3_bucket", "aws_s3_bucket_acl"):
        return findings

    acl = after.get("acl", "")
    if acl in ("public-read", "public-read-write", "authenticated-read"):
        findings.append({
            "resource": f"{resource_type}.{resource_name}",
            "issue": f'S3 bucket ACL is set to "{acl}" which allows broad access',
            "severity": "HIGH",
            "severity_index": SEVERITY_INDEX["HIGH"],
            "recommendation": (
                'Set acl to "private" and use bucket policies to grant '
                "least-privilege access."
            ),
            "remediations": [
                'Set ACL to "private"',
                "Enable S3 Block Public Access settings",
                "Use bucket policies for least-privilege access",
            ],
            "check_id": "check_s3_public_acl",
            "documentation_url": (
                "https://docs.aws.amazon.com/AmazonS3/latest/userguide/"
                "access-control-block-public-access.html"
            ),
            "url": REPOSITORY_URL,
        })

    return findings


# ---------------------------------------------------------------------------
# Registry – add new check functions here
# ---------------------------------------------------------------------------

CHECKS = [
    check_sg_open_ingress,
    check_s3_public_acl,
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _port_in_range(port: int, from_port: int, to_port: int) -> bool:
    """Return True if *port* falls within [from_port, to_port]."""
    try:
        return int(from_port) <= port <= int(to_port)
    except (TypeError, ValueError):
        return False
