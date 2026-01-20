import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

USE_MOCK = True

# -----------------------------
# AWS Clients (Real Later)
# -----------------------------
if not USE_MOCK:
    import boto3
    iam = boto3.client("iam")
    ec2 = boto3.client("ec2")

# -----------------------------
# Mock IAM Data
# -----------------------------
if USE_MOCK:
    iam_users = [
        {
            "UserName": "test-admin",
            "HasAdminAccess": True,
            "HasMFA": True
        }
    ]
else:
    iam_users = iam.list_users().get("Users", [])

# -----------------------------
# Mock Security Group Data
# -----------------------------
if USE_MOCK:
    security_groups = [
        {
            "GroupId": "sg-0123",
            "GroupName": "open-ssh",
            "IpPermissions": [
                {
                    "FromPort": 22,
                    "ToPort": 22,
                    "IpProtocol": "tcp",
                    "IpRanges": [{"CidrIp": "10.0.0.0/16"
}]
                }
            ]
        }
    ]
else:
    security_groups = ec2.describe_security_groups().get("SecurityGroups", [])

# -----------------------------
# Findings Engine
# -----------------------------
findings = []
high_risk_exists = False

# -----------------------------
# IAM Checks
# -----------------------------
for user in iam_users:
    if user.get("HasAdminAccess") and not user.get("HasMFA"):
        findings.append({
            "resource": f"iam_user:{user['UserName']}",
            "issue": "Admin access without MFA",
            "severity": "HIGH",
            "recommendation": "Enable MFA or remove AdministratorAccess"
        })

# -----------------------------
# Security Group Checks
# -----------------------------
for sg in security_groups:
    for rule in sg.get("IpPermissions", []):
        from_port = rule.get("FromPort")
        to_port = rule.get("ToPort")

        for ip_range in rule.get("IpRanges", []):
            cidr = ip_range.get("CidrIp")

            if cidr == "0.0.0.0/0" and from_port in [22, 3389]:
                findings.append({
                    "resource": f"security_group:{sg['GroupId']}",
                    "issue": f"Port {from_port} open to the world",
                    "severity": "HIGH",
                    "recommendation": "Use SSM Session Manager or restrict CIDR range"
                })

# -----------------------------
# Evaluation + CI Gate
# -----------------------------
for finding in findings:
    logging.info(
        f"{finding['severity']} | {finding['resource']} | {finding['issue']}"
    )
    if finding["severity"] == "HIGH":
        high_risk_exists = True

if high_risk_exists:
    logging.error("High risk detected — failing CI")
    sys.exit(1)
else:
    logging.info("No high risk detected — passing CI")
    sys.exit(0)
