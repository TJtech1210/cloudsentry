📝 CloudSentry – Learning Notes

This file captures what I learned and why it matters while building CloudSentry.
It’s meant to be reviewed, expanded, and linked to docs over time.

1️⃣ GitHub Actions (CI/CD)
What I learned

GitHub Actions runs workflows based on events like push

A workflow is made of jobs

Jobs run on runners (Linux VM by default)

Steps run top to bottom

The exit code of a script decides pass/fail

Key YAML concepts
on:
  push:


➡ Runs workflow on every push

jobs:
  cloud_scan:
    runs-on: ubuntu-latest


➡ Defines a job and the OS it runs on

- uses: actions/checkout@v4


➡ Pulls repo code onto the runner

- uses: actions/setup-python@v5


➡ Ensures Python exists before running scripts

- run: python cloudsentry.py


➡ Executes the security gate
➡ Exit code controls CI outcome

Why it matters

CI/CD is automation + enforcement

Security checks must run before deployment

Pipelines should fail early, not report late

2️⃣ Exit Codes (Core CI Logic)
What I learned

sys.exit(0) = success (CI passes)

sys.exit(1) = failure (CI stops)

Exit codes are the enforcement mechanism

Key code
sys.exit(1)


➡ Stops the pipeline

sys.exit(0)


➡ Allows the pipeline to continue

Why it matters

Logging explains

Exit codes decide

Never mix the two

3️⃣ Python Logging (Observability)
What I learned

print() is for debugging

logging is for systems and security tools

Logs give time + severity + message

Key code
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


➡ Sets global logging format
➡ Makes CI output readable and professional

logging.info("message")
logging.error("message")


➡ INFO = normal behavior
➡ ERROR = security failure

Why it matters

CI logs are the “UI”

Security tools must be readable

Logs scale as rules grow

4️⃣ Mocking Cloud Data (Safe Testing)
What I learned

Mocking lets me test logic without AWS access

Logic should not change between mock and real

Only the data source changes

Key pattern
USE_MOCK = True

if USE_MOCK:
    iam_users = [...]
else:
    iam_users = iam.list_users()

Why it matters

Prevents accidental AWS calls

Avoids credential issues

Makes CI deterministic

5️⃣ Security Findings Engine
What I learned

Findings should be structured

Severity drives enforcement

One gate controls the outcome

Key structure
findings.append({
    "resource": "...",
    "issue": "...",
    "severity": "HIGH",
    "recommendation": "..."
})

if finding["severity"] == "HIGH":
    high_risk_exists = True

Why it matters

Easy to add new rules

Same logic works for many checks

Scales like real security tools

6️⃣ IAM Security Concepts
What I learned

Admin access without MFA is high risk

Long-lived users increase attack surface

IAM checks are cloud state, not IaC

Example logic
if user.get("HasAdminAccess") and not user.get("HasMFA"):

Why it matters

Security+ concepts map directly to cloud

Cloud security is identity-first

7️⃣ Network Security Concepts
What I learned

0.0.0.0/0 means open to the world

SSH (22) and RDP (3389) are high-risk ports

Security groups are a major attack surface

Example logic
if cidr == "0.0.0.0/0" and from_port in [22, 3389]:

Why it matters

Network exposure causes real breaches

Simple rules catch major risks

8️⃣ CI Security Gate Design
What I learned

Security should block, not warn

CI is the best enforcement point

Prevention > detection

Mental model
Checks → Findings → Logs → Exit Code → CI Decision

Why it matters

This is how real pipelines work

Reporting alone is security theater

9️⃣ How This Fits the Flagship Project

CloudSentry = security gate

Secure-Infra-Pipeline = delivery platform

CloudSentry runs before tfsec and Terraform

This creates layered security:

Cloud state checks

IaC static analysis

Deployment enforcement

🔗 Docs to Add Later

(Add links here as you learn more)

GitHub Actions docs

Python logging docs

AWS IAM docs

tfsec rules

Terraform AWS provider

Final takeaway

CloudSentry taught me:

CI/CD fundamentals

Security enforcement

Cloud identity risks

How real security tools are structured

This is not a toy project.
