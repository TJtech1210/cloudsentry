# 🛡️ CloudSentry

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

<img width="666" height="404" alt="Screenshot 2026-01-18 235148" src="https://github.com/user-attachments/assets/ffa85fb4-20b4-4493-a08e-9dd6f61ab5d9" />


Developer → CI → CloudSentry → Decision Gate



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

```python
USE_MOCK = True
