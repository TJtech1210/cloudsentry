# 🛡️ CloudSentry

[![CI](https://github.com/TJtech1210/cloudsentry/actions/workflows/cloudsentry-ci.yml/badge.svg?branch=main)](https://github.com/TJtech1210/cloudsentry/actions)
[![Python](https://img.shields.io/badge/python-3.10-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
![Security Gate](https://img.shields.io/badge/security-CI%20Enforced-red)


## Overview

**CloudSentry** is a CI-based cloud security gate that analyzes cloud security conditions and enforces pass/fail decisions automatically inside GitHub Actions.

It is designed to block insecure changes before they reach deployment, not just report them after the fact.

---

## 🎯 Project Goals

- Enforce cloud security rules automatically in CI/CD
- Detect high-risk IAM and network configurations
- Fail builds when critical security issues are found
- Keep AWS access read-only and safe
- Serve as a reusable security gate for larger pipelines

---

## 🧠 How CloudSentry Works

1. A push or manual trigger starts the workflow
2. GitHub Actions spins up a Linux runner
3. CloudSentry runs as a Python security engine
4. Security findings are generated
5. CI fails or passes automatically based on severity

Security decisions are enforced using exit codes, not manual review.

---

## 🧱 Architecture Overview

<img width="1536" height="1024" alt="Jan 20, 2026, 10_32_30 AM" src="https://github.com/user-attachments/assets/26c785ca-900c-4696-83fc-b59fd2e3c867" />


Developer Push / PR
        ↓
GitHub Repository
(cloudsentry.py, workflow)
        ↓
GitHub Actions (CI)
- Ubuntu runner
- Checkout repo
- Python execution
- AWS creds via GitHub Secrets (Read-Only)
        ↓
CloudSentry Scan Engine
- Enumerate IAM resources
- Evaluate security posture
- Flag HIGH risk findings
        ↓
AWS IAM (Read-Only via Boto3)
        ↓
Policy Enforcement Gate
        ├─ No HIGH findings → CI PASS (exit 0)
        └─ HIGH findings → CI FAIL (exit 1)


---

## 🔍 Security Checks (Current)

CloudSentry currently evaluates:

### IAM Risks
- Admin access without MFA

### Network Risks
- SSH (22) open to 0.0.0.0/0
- RDP (3389) open to 0.0.0.0/0

Each finding includes:
- Resource
- Issue description
- Severity
- Recommendation

---

## 🚦 CI Enforcement Logic

- Any HIGH severity finding → ❌ CI FAIL
- No HIGH severity findings → ✅ CI PASS

Logging explains why a decision was made.  
Exit codes enforce the outcome.

---

## 📊 Example: Failing CI Run

<img width="485" height="106" alt="fail" src="https://github.com/user-attachments/assets/c602f086-5094-4e5f-a609-faa16fb8207b" />


Example output showing high-risk IAM and network findings blocking the pipeline.

---

## ✅ Example: Passing CI Run

<img width="401" height="61" alt="pass" src="https://github.com/user-attachments/assets/0e6046c0-a547-4475-9e2f-2c96e59a8be9" />


Example output after fixing security issues, allowing the pipeline to continue.

---

## 📜 Logging & Observability

CloudSentry uses Python’s built-in logging to provide:

- Timestamps
- Severity levels (INFO / ERROR)
- Clear, human-readable findings

Logging is used for visibility only.  
CI enforcement is handled separately via exit codes.

---

## 🧪 Mocking vs Real AWS

CloudSentry supports mock mode for safe testing:

---

## 🔐 CloudSentry Status (Completed)

CloudSentry is now a stable, read-only AWS security scanner.

What it does:

-Scans real AWS resources (IAM + EC2)

-Uses least-privilege IAM (no write access)

-Runs locally and in GitHub Actions

-Fails CI on HIGH-risk findings

-Outputs cloudsentry_report.json for pipeline use

-Design notes

-Supports mock and aws modes via environment variables

-Zero cost (read-only API calls)

-Intended to act as a security gate for Secure-Infra-Pipeline

## Status: frozen and production-ready.

```python
USE_MOCK = True
```

---

## 📦 cloudsentry-cli – Terraform Plan Scanner

`cloudsentry-cli` is a pip-installable CLI package that scans a **Terraform plan JSON** file for security issues **before** `terraform apply` runs.

### Install

```bash
pip install cloudsentry-cli
```

### Usage

```bash
# Generate the plan JSON in your Terraform directory
terraform plan -out plan.out
terraform show -json plan.out > tfplan.json

# Scan it – exit 1 if any HIGH or above finding is detected
cloudsentry-cli scan --input tfplan.json

# Configure the threshold and output path
cloudsentry-cli scan --input tfplan.json --fail-on MEDIUM --output my_report.json
```

| Flag | Default | Description |
|------|---------|-------------|
| `--input` | *(required)* | Path to the Terraform plan JSON file |
| `--fail-on` | `HIGH` | Minimum severity for exit 1: `LOW \| MEDIUM \| HIGH \| CRITICAL` |
| `--output` | `cloudsentry_report.json` | Path for the JSON report |

---

## 🔎 How It Works – Plan JSON Scanning

### Why scan the plan JSON instead of live AWS state?

Terraform produces a **plan** before it changes anything. Scanning this plan
blocks risky configuration from ever reaching production. By the time you
scan live AWS state, the insecure resource is already deployed.

The typical pipeline looks like:

```
terraform plan -out plan.out             # creates a binary plan file
terraform show -json plan.out            # converts to tfplan.json
cloudsentry-cli scan --input tfplan.json # EXIT 1 if risky? STOP
terraform apply                          # only reached if CloudSentry exits 0
```

### What is `resource_changes[].change.after`?

The Terraform plan JSON contains a `resource_changes` array. Each element
describes one resource Terraform plans to **create, update, or delete**.

The `change` object inside each entry has three sub-keys:

| Key | Meaning |
|-----|---------|
| `change.before` | The resource config **right now** (null for new resources) |
| `change.after` | The resource config as it will look **after apply** |
| `change.actions` | What Terraform will do: `create`, `update`, `delete`, etc. |

CloudSentry evaluates `change.after` because that is the **final state that
will be deployed**. Checking the target state catches misconfigurations
before they exist.

### How do exit codes gate the pipeline?

`cloudsentry-cli scan` uses standard Unix exit codes:

| Exit code | Meaning |
|-----------|---------|
| `0` | No findings at or above the `--fail-on` threshold → **pipeline continues** |
| `1` | At least one finding meets or exceeds the threshold → **pipeline halts** |

GitHub Actions (and most CI systems) treat any non-zero exit as a step
failure and stop the job. This means `terraform apply` is **never reached**
when CloudSentry finds a problem.

---

## ⚙️ Composite GitHub Action

Use the built-in composite action to add scanning to any workflow in one step:

```yaml
- name: CloudSentry scan
  uses: TJtech1210/cloudsentry/.github/actions/cloudsentry-scan@main
  with:
    input: terraform/tfplan.json
    fail_on: HIGH
    output: cloudsentry_report.json
    version: "0.1.0"   # pin a PyPI version; omit for latest; "git" for local source
```

See `.github/workflows/terraform-pipeline.yml` for a full end-to-end example.
