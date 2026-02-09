import sys
import logging
import os
import json
from datetime import datetime, timezone, timedelta

# -----------------------------
# Logging Setup
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

MODE = os.getenv("CLOUDSENTRY_MODE", "mock")
USE_MOCK = MODE == "mock"

# -----------------------------
# AWS Clients (only if needed)
# -----------------------------
if not USE_MOCK:
    import boto3
    iam = boto3.client("iam")
    ec2 = boto3.client("ec2")

# -----------------------------
# IAM Data
# -----------------------------
if USE_MOCK:
    iam_users = [
        {
            "UserName": "test-admin",
            "HasAdminAccess": True,
            "HasMFA": False,
            "AccessKeys": [
                {
                    "LastRotated": datetime.now(timezone.utc) - timedelta(days=120)
                }
            ]
        }
    ]
else:
    iam_users = []

    for user in iam.list_users()["Users"]:
        username = user["UserName"]

        mfa = iam.list_mfa_devices(UserName=username)["MFADevices"]
        keys = iam.list_access_keys(UserName=username)["AccessKeyMetadata"]

        access_keys = [{"LastRotated": k["CreateDate"]} for k in keys]

        iam_users.append({
            "UserName": username,
            "HasAdminAccess": False,
            "HasMFA": bool(mfa),
            "AccessKeys": access_keys
        })

# -----------------------------
# Security Groups
# -----------------------------
if USE_MOCK:
    security_groups = [
        {
            "GroupId": "sg-0123",
            "IpPermissions": [
                {
                    "FromPort": 22,
                    "IpRanges": [{"CidrIp": "0.0.0.0/0"}]
                }
            ]
        }
    ]
else:
    security_groups = ec2.describe_security_groups()["SecurityGroups"]

# -----------------------------
# Findings Engine
# -----------------------------
findings = []
severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
high_risk_exists = False

# -----------------------------
# IAM Access Key Rotation
# -----------------------------
ROTATION_THRESHOLD_DAYS = 90
now = datetime.now(timezone.utc)

for user in iam_users:
    for key in user.get("AccessKeys", []):
        if (now - key["LastRotated"]).days > ROTATION_THRESHOLD_DAYS:
            findings.append({
                "resource": f"iam_user:{user['UserName']}",
                "issue": "Access key not rotated in over 90 days",
                "severity": "HIGH",
                "recommendation": "Rotate or remove unused access keys"
            })
            severity_counts["HIGH"] += 1

# -----------------------------
# IAM MFA
# -----------------------------
for user in iam_users:
    if user["HasAdminAccess"] and not user["HasMFA"]:
        findings.append({
            "resource": f"iam_user:{user['UserName']}",
            "issue": "Admin access without MFA",
            "severity": "HIGH",
            "recommendation": "Enable MFA"
        })
        severity_counts["HIGH"] += 1

# -----------------------------
# Security Group Checks
# -----------------------------
for sg in security_groups:
    for rule in sg.get("IpPermissions", []):
        if rule.get("FromPort") in [22, 3389]:
            for ip in rule.get("IpRanges", []):
                if ip.get("CidrIp") == "0.0.0.0/0":
                    findings.append({
                        "resource": f"security_group:{sg['GroupId']}",
                        "issue": f"Port {rule['FromPort']} open to the world",
                        "severity": "HIGH",
                        "recommendation": "Restrict CIDR or use SSM"
                    })
                    severity_counts["HIGH"] += 1

# -----------------------------
# Logging
# -----------------------------
for f in findings:
    logging.info(f"{f['severity']} | {f['resource']} | {f['issue']}")
    if f["severity"] == "HIGH":
        high_risk_exists = True

# -----------------------------
# JSON REPORT (ALWAYS WRITTEN)
# -----------------------------
report = {
    "tool": "CloudSentry",
    "mode": MODE,
    "scan_time": datetime.now(timezone.utc).isoformat(),
    "summary": {
        "total_findings": len(findings),
        "high": severity_counts["HIGH"],
        "medium": severity_counts["MEDIUM"],
        "low": severity_counts["LOW"]
    },
    "findings": findings
}

with open("cloudsentry_report.json", "w") as f:
    json.dump(report, f, indent=2)

# -----------------------------
# EXIT
# -----------------------------
if high_risk_exists:
    logging.error("High risk detected — failing CI")
    sys.exit(1)

logging.info("No high risk detected — passing CI")
sys.exit(0)
