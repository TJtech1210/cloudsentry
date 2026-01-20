# 🛡️ CloudSentry

CloudSentry is a CI-based cloud security gate that analyzes AWS IAM state using Python and Boto3 and enforces pass/fail decisions automatically through GitHub Actions.

## Why CloudSentry

CloudSentry demonstrates how cloud security controls can be enforced automatically
inside CI/CD pipelines instead of relying on manual reviews.

This project focuses on:
- Preventing insecure cloud states before deployment
- Using read-only AWS access for safety
- Enforcing security decisions with CI pass/fail gates

## 🔍 What CloudSentry Does

- Runs automatically in GitHub Actions

- Uses Python to analyze AWS IAM (read-only)

- Generates security findings

- Fails CI when high-risk conditions are detected

- Blocks insecure changes before they reach production

## 🧠 How It Works

- A developer pushes code or opens a pull request

- GitHub Actions starts a CI job on a Linux runner

- The repository is checked out

- cloudsentry.py runs

- CloudSentry queries AWS IAM using Boto3

- Findings are generated

- A decision is made:

- High risk → CI fails

- No high risk → CI passes

## 🧱 Architecture Overview
Developer
  ↓
GitHub Repository
  ↓
GitHub Actions (CI)
  ↓
CloudSentry (Python)
  ↓
Boto3 (AWS SDK)
  ↓
AWS IAM (Read-only)
  ↓
Decision Gate
  ├─ sys.exit(1) → CI FAIL
  └─ sys.exit(0) → CI PASS

## 🚦 Security Logic (Current Rule)

CloudSentry fails CI if any finding contains the string:

"High risk"


Example failing finding:

High risk: IAM users exist in account

## 🔐 AWS Permissions

CloudSentry uses read-only AWS permissions.

Minimum IAM permission required:

iam:ListUsers


AWS credentials are provided securely via GitHub Secrets.

## 🛠️ Tools Used

Python

GitHub Actions

AWS IAM

Boto3

Linux (CI runner)

GitHub Secrets

## Logging & Observability

CloudSentry uses Python’s built-in logging to provide clear, structured output
during CI runs.

Logs include:
- Timestamps (when a check ran)
- Severity levels (INFO / ERROR)
- Human-readable findings

Logging is used only for visibility.
Pass/fail decisions are enforced separately using exit codes.

This design allows CloudSentry to scale to multiple security checks without
changing CI enforcement logic.


## Skills Demonstrated

- Cloud security fundamentals (IAM)
- CI/CD with GitHub Actions
- Security automation with Python
- Policy-as-code using exit codes
- Safe AWS access patterns (read-only, mocked testing)

## 🚀 Project Status

✅ CI pipeline working

✅ Pass/fail logic implemented

✅ Real AWS IAM data integrated

⏭️ Next: stronger IAM risk checks

## Running CloudSentry

CloudSentry runs automatically via GitHub Actions on push or pull request.

For local testing:
- Set USE_MOCK_IAM = True
- Run: python cloudsentry.py

