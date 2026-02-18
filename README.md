# 🛡️ CloudSentry

[![CI](https://github.com/TJtech1210/cloudsentry/actions/workflows/cloudsentry-ci.yml/badge.svg?branch=main)](https://github.com/TJtech1210/cloudsentry/actions)
[![Python](https://img.shields.io/badge/python-3.10-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
![Security Gate](https://img.shields.io/badge/security-CI%20Enforced-red)


## Overview

**CloudSentry** is a CI-based cloud security gate that analyzes cloud security conditions and enforces pass/fail decisions automatically inside GitHub Actions.

It is designed to block insecure changes before they reach deployment, not just report them after the fact.

**NEW in v2:** CloudSentry now supports scanning Terraform plan files to detect security issues before infrastructure is deployed!

---

## 🚀 Features

### AWS Resource Scanning (v1)
- Scans live AWS resources (IAM users, EC2 security groups)
- Detects misconfigured IAM access keys and MFA settings
- Identifies overly permissive security groups
- Runs in mock mode for testing or AWS mode for production

### Terraform Plan Scanning (v2)
- **Pre-deployment security**: Scan Terraform plans before applying changes
- **Modular check system**: Easily add new security checks
- **S3 Security Checks**: Detect public S3 buckets and misconfigured access blocks
- **Clear, actionable warnings**: Each finding includes resource, issue, and recommendation

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

## 📖 Usage

### Scanning Terraform Plans

CloudSentry can scan Terraform plan JSON files to detect security issues before deployment:

```bash
# Generate a Terraform plan in JSON format
terraform plan -out=tfplan
terraform show -json tfplan > tfplan.json

# Scan the plan with CloudSentry
python cloudsentry.py --tfplan tfplan.json
```

Example output:
```
2026-02-18 13:43:04,653 | INFO | Starting Terraform plan scan: tfplan.json
2026-02-18 13:43:04,653 | INFO | Successfully loaded Terraform plan JSON
2026-02-18 13:43:04,653 | INFO | Found 4 resource change(s) in plan
2026-02-18 13:43:04,653 | INFO | Loading 1 check module(s): s3_checks
2026-02-18 13:43:04,653 | WARNING | PUBLIC S3 DETECTED: aws_s3_bucket.public_bucket has ACL=public-read
2026-02-18 13:43:04,654 | ERROR | High risk detected in Terraform plan — failing CI
```

### Scanning Live AWS Resources

For scanning existing AWS infrastructure:

```bash
# Mock mode (for testing without AWS credentials)
CLOUDSENTRY_MODE=mock python cloudsentry.py

# AWS mode (requires valid AWS credentials)
CLOUDSENTRY_MODE=aws python cloudsentry.py
```

### Understanding the Output

CloudSentry generates a `cloudsentry_report.json` file with detailed findings:

```json
{
  "tool": "CloudSentry",
  "mode": "tfplan",
  "scan_time": "2026-02-18T13:43:04.654232+00:00",
  "summary": {
    "total_findings": 2,
    "high": 2,
    "medium": 0,
    "low": 0
  },
  "findings": [
    {
      "resource": "aws_s3_bucket.public_bucket",
      "issue": "S3 bucket configured with public ACL: public-read",
      "severity": "HIGH",
      "recommendation": "Use private ACL and configure bucket policy..."
    }
  ]
}
```

---

## 🔍 Security Checks (Current)

### Terraform Plan Checks (v2)

#### S3 Bucket Security
- **Public ACL Detection**: Flags S3 buckets with `public-read` or `public-read-write` ACLs
- **Public Access Block**: Detects S3 buckets with disabled public access block settings
  - `block_public_acls`
  - `block_public_policy`
  - `ignore_public_acls`
  - `restrict_public_buckets`

### AWS Resource Checks (v1)

#### IAM Risks
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

## 🔧 Extending CloudSentry with New Checks

CloudSentry v2 uses a modular architecture that makes it easy to add new security checks.

### Adding a New Check Module

1. Create a new file in the `checks/` directory (e.g., `checks/ec2_checks.py`)
2. Implement a `run_check(resources)` function that:
   - Takes a list of Terraform resources
   - Returns a list of findings
3. CloudSentry will automatically discover and run your new check!

Example check module structure:

```python
# checks/example_checks.py
def run_check(resources):
    """Check for security issues in resources"""
    findings = []
    
    for resource in resources:
        resource_type = resource.get('type', '')
        resource_address = resource.get('address', '')
        change = resource.get('change', {})
        after = change.get('after', {})
        
        # Your security logic here
        if resource_type == 'aws_example_resource':
            if after.get('dangerous_setting') == 'enabled':
                findings.append({
                    'resource': resource_address,
                    'issue': 'Dangerous setting enabled',
                    'severity': 'HIGH',
                    'recommendation': 'Disable this setting'
                })
    
    return findings
```

See `checks/s3_checks.py` for a complete working example.

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

##Status: frozen and production-ready.

```python
USE_MOCK = True
