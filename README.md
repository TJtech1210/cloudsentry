# 🛡️ CloudSentry

[![CI](https://github.com/TJtech1210/cloudsentry/actions/workflows/cloudsentry-ci.yml/badge.svg?branch=main)](https://github.com/TJtech1210/cloudsentry/actions)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
![Security Gate](https://img.shields.io/badge/security-CI%20Enforced-red)

**CloudSentry is a Python CLI that scans Terraform plan JSON for security misconfigurations and fails CI automatically — blocking risky infrastructure changes before `terraform apply` ever runs.**

---

## 🚀 Demo in 60 Seconds

No AWS account or Terraform installation required. The repo includes a ready-made sample plan.

```bash
# 1. Install
pip install cloudsentry-cli

# 2. Clone the repo to get the sample plan
git clone https://github.com/TJtech1210/cloudsentry.git
cd cloudsentry

# 3. Scan the sample plan (contains intentional HIGH findings)
cloudsentry-cli scan --input examples/tfplan.json
```

Expected output (exit 1 — pipeline blocked):

```
============================================================
CloudSentry CLI  v0.1.0
Input : examples/tfplan.json
Threshold: HIGH
------------------------------------------------------------
Total findings : 2
  LOW       : 0
  MEDIUM    : 0
  HIGH      : 2
  CRITICAL  : 0
------------------------------------------------------------
  ✖ [HIGH] aws_security_group.web – Port 22 open to the world (0.0.0.0/0 or ::/0) in ingress rule
  ✖ [HIGH] aws_s3_bucket.assets – S3 bucket ACL is set to "public-read" which allows broad access
------------------------------------------------------------
FAIL  2 finding(s) at or above threshold 'HIGH'.
============================================================
```

Fix the issues and re-scan (or raise the threshold to see a passing run):

```bash
cloudsentry-cli scan --input examples/tfplan.json --fail-on CRITICAL
# → PASS  No findings at or above threshold.   (exit 0)
```

---

## 🎯 Features

- **Terraform plan gating** — scans `resource_changes[].change.after` before anything is deployed
- **Configurable severity threshold** — fail on `LOW`, `MEDIUM`, `HIGH`, or `CRITICAL`
- **Extensible check registry** — add a function, register it, done; no other code changes required
- **JSON report output** — machine-readable `cloudsentry_report.json` for downstream pipeline steps
- **Zero external dependencies** — pure Python stdlib; install anywhere in seconds
- **Composite GitHub Action** — drop-in one step that gates Terraform pipelines
- **Tested** — unit and integration tests with pytest; CI enforced on every push

---

## 🧠 How It Works

Terraform produces a plan before it changes anything. CloudSentry scans that plan so misconfigurations are caught at review time, not after deployment.

```
terraform plan -out plan.out                 # 1. create binary plan
terraform show -json plan.out > tfplan.json  # 2. export to JSON
cloudsentry-cli scan --input tfplan.json     # 3. EXIT 1 if risky → STOP
terraform apply                              # 4. only reached when clean
```

### Plan JSON anatomy

| Key | Meaning |
|-----|---------|
| `change.before`  | Current resource config (null for new resources) |
| `change.after`   | Config that will exist **after apply** — what CloudSentry evaluates |
| `change.actions` | `create`, `update`, `delete`, `no-op` |

CloudSentry only evaluates resources being **created or updated**, skipping deletions and no-ops.

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | No findings at or above `--fail-on` threshold → pipeline continues |
| `1` | At least one finding meets or exceeds the threshold → pipeline halts |

---

## 🏗️ Architecture

```
Developer push / PR
       │
       ▼
GitHub Actions (CI)
  ├─ checkout repo
  ├─ terraform plan → tfplan.json
  └─ cloudsentry-cli scan ──────────────────┐
                                            │
                           ┌────────────────▼──────────────────┐
                           │        CloudSentry Engine          │
                           │  scanner.py  →  checks registry    │
                           │  check_sg_open_ingress()           │
                           │  check_s3_public_acl()             │
                           │  ... (add more checks here)        │
                           └────────────────┬──────────────────┘
                                            │
                              ┌─────────────┴──────────────┐
                              │     Policy Gate             │
                              │  findings ≥ threshold?      │
                              │  YES → exit 1 → CI FAIL     │
                              │  NO  → exit 0 → CI PASS     │
                              └─────────────────────────────┘
                                       │
                              cloudsentry_report.json
```

---

## 🔍 Security Checks

| Check | Resources evaluated | Severity |
|-------|---------------------|----------|
| `check_sg_open_ingress` | `aws_security_group`, `aws_security_group_rule` | HIGH |
| `check_s3_public_acl`   | `aws_s3_bucket`, `aws_s3_bucket_acl`           | HIGH |

Each finding contains:

```json
{
  "resource":       "aws_security_group.web",
  "issue":          "Port 22 open to the world (0.0.0.0/0 or ::/0) in ingress rule",
  "severity":       "HIGH",
  "severity_index": 2,
  "recommendation": "Restrict the CIDR to known IP ranges or use AWS Systems Manager Session Manager.",
  "remediations": [
    "Restrict CIDR to specific IP ranges",
    "Use AWS Systems Manager Session Manager",
    "Use a bastion host for administrative access"
  ],
  "check_id": "check_sg_open_ingress",
  "documentation_url": "https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html",
  "url": "https://github.com/TJtech1210/cloudsentry"
}
```

---

## 📊 Output Format

`cloudsentry_report.json` (written after every scan):

```json
{
  "generated_at": "2025-05-01T12:00:00+00:00",
  "input_file":   "examples/tfplan.json",
  "fail_on":      "HIGH",
  "outcome":      "FAIL",
  "summary": { "total": 2, "LOW": 0, "MEDIUM": 0, "HIGH": 2, "CRITICAL": 0 },
  "findings": [
    {
      "resource":       "aws_security_group.web",
      "issue":          "Port 22 open to the world (0.0.0.0/0 or ::/0) in ingress rule",
      "severity":       "HIGH",
      "severity_index": 2,
      "recommendation": "Restrict the CIDR to known IP ranges or use AWS Systems Manager Session Manager.",
      "remediations": [
        "Restrict CIDR to specific IP ranges",
        "Use AWS Systems Manager Session Manager",
        "Use a bastion host for administrative access"
      ],
      "check_id": "check_sg_open_ingress",
      "documentation_url": "https://docs.aws.amazon.com/vpc/latest/userguide/VPC_SecurityGroups.html",
      "url": "https://github.com/TJtech1210/cloudsentry"
    }
  ]
}
```

---

## ➕ Adding New Checks

1. Open `src/cloudsentry_cli/checks.py`
2. Write a function with this signature:

```python
def check_my_rule(
    resource_type: str,
    resource_name: str,
    after: dict,
) -> list[dict]:
    findings = []
    if resource_type != "aws_my_resource":
        return findings
    if after.get("some_risky_field"):
        findings.append({
            "resource":       f"{resource_type}.{resource_name}",
            "issue":          "Description of the problem",
            "severity":       "HIGH",
            "recommendation": "How to fix it",
        })
    return findings
```

3. Register it in the `CHECKS` list at the bottom of the file — **no other code changes needed**.

---

## 🧪 Testing

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run all tests
pytest

# Run with coverage
pytest --cov=cloudsentry_cli --cov-report=term-missing
```

Tests live in `tests/test_scanner.py` and cover individual check functions plus end-to-end `scan_plan()` integration scenarios.

---

## ⚙️ CI Integration

### Composite GitHub Action (recommended)

Drop a single step into any workflow to gate Terraform:

```yaml
- name: CloudSentry scan
  uses: TJtech1210/cloudsentry/.github/actions/cloudsentry-scan@main
  with:
    input: terraform/tfplan.json
    fail_on: HIGH
    output: cloudsentry_report.json
    version: "0.1.0"   # pin a PyPI version; omit for latest; "git" for local source
```

See [`.github/workflows/terraform-pipeline.yml`](.github/workflows/terraform-pipeline.yml) for a full end-to-end pipeline example.

### Raw workflow step

```yaml
- name: Install CloudSentry CLI
  run: pip install cloudsentry-cli==0.1.0

- name: Scan Terraform plan
  run: cloudsentry-cli scan --input terraform/tfplan.json --fail-on HIGH --output cloudsentry_report.json

- name: Upload security report
  if: always()
  uses: actions/upload-artifact@v4
  with:
    name: cloudsentry-report
    path: cloudsentry_report.json
```

### CLI flags

| Flag | Default | Description |
|------|---------|-------------|
| `--input`    | *(required)* | Path to the Terraform plan JSON file |
| `--fail-on`  | `HIGH`        | Minimum severity for exit 1: `LOW \| MEDIUM \| HIGH \| CRITICAL` |
| `--output`   | `cloudsentry_report.json` | Path for the JSON report |

---

## 🏅 Skills Demonstrated

| Skill | Where it shows up |
|-------|-------------------|
| **Terraform / IaC** | Understands plan JSON structure (`resource_changes`, `change.after`, `actions`) and gates the apply step |
| **GitHub Actions** | Composite action, workflow gating, artifact upload, CI badge |
| **Python (CLI)** | `argparse`, exit codes, stdlib-only package, `pyproject.toml` packaging |
| **Security engineering** | Misconfiguration detection, severity classification, shift-left enforcement |
| **Extensible design** | Check registry pattern — new rules added without touching scanner core |
| **Testing** | `pytest` unit + integration tests; coverage reporting |
| **CI gating** | Pipeline halts on policy violation via Unix exit codes; no manual review needed |
| **Supply chain hygiene** | Zero runtime dependencies; pinnable PyPI version for reproducible builds |

---

## 📁 Repository Layout

```
cloudsentry/
├── src/cloudsentry_cli/
│   ├── __init__.py       # version
│   ├── cli.py            # argparse entry point
│   ├── scanner.py        # plan JSON loader + check dispatcher
│   └── checks.py         # security check functions + CHECKS registry
├── tests/
│   └── test_scanner.py   # unit + integration tests
├── examples/
│   └── tfplan.json       # sample plan with intentional HIGH findings (no AWS needed)
├── .github/
│   ├── actions/cloudsentry-scan/action.yml   # composite action
│   └── workflows/
│       ├── cloudsentry-ci.yml                # library CI (lint + test)
│       └── terraform-pipeline.yml           # end-to-end pipeline demo
└── pyproject.toml
```

---

## ⚠️ Legacy: Live AWS Scanner

> **Note:** The files `cloudsentry.py` and `checks.py` at the repository root are an earlier prototype that scanned **live AWS resources** using Boto3. That version is **frozen** and kept for reference only. The primary project is `cloudsentry-cli` (in `src/`), which scans Terraform plan JSON without any AWS credentials.

---

## 📄 License

[MIT](LICENSE)
