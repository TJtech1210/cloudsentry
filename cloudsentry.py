import sys
import logging
import os
import json
import argparse
from datetime import datetime, timezone, timedelta

# -----------------------------
# Logging Setup
# -----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

# -----------------------------
# Argument Parsing
# -----------------------------
parser = argparse.ArgumentParser(
    description='CloudSentry: Cloud Security Scanner and Terraform Plan Analyzer',
    formatter_class=argparse.RawDescriptionHelpFormatter,
    epilog='''
Examples:
  # Scan live AWS resources (requires AWS credentials)
  python cloudsentry.py
  
  # Scan a Terraform plan file
  python cloudsentry.py --tfplan tfplan.json
  
  # Use mock mode for testing
  CLOUDSENTRY_MODE=mock python cloudsentry.py
    '''
)
parser.add_argument(
    '--tfplan',
    type=str,
    help='Path to Terraform plan JSON file (from terraform show -json tfplan)',
    metavar='FILE'
)

args = parser.parse_args()

# -----------------------------
# Terraform Plan Scanning Mode
# -----------------------------
if args.tfplan:
    logging.info(f"Starting Terraform plan scan: {args.tfplan}")
    
    try:
        # Load and parse the Terraform plan JSON file
        with open(args.tfplan, 'r') as f:
            tfplan = json.load(f)
        
        logging.info("Successfully loaded Terraform plan JSON")
        
        # Extract resource changes from the plan
        # Terraform plans have a "resource_changes" array with planned resource modifications
        resource_changes = tfplan.get('resource_changes', [])
        
        if not resource_changes:
            logging.warning("No resource changes found in Terraform plan")
        else:
            logging.info(f"Found {len(resource_changes)} resource change(s) in plan")
        
        # Import the modular check loader
        from checks import load_and_run_checks
        
        # Run all available checks on the resources
        findings = load_and_run_checks(resource_changes)
        
        # Count severities
        severity_counts = {"HIGH": 0, "MEDIUM": 0, "LOW": 0}
        high_risk_exists = False
        
        for finding in findings:
            severity = finding.get('severity', 'UNKNOWN')
            if severity in severity_counts:
                severity_counts[severity] += 1
            if severity == 'HIGH':
                high_risk_exists = True
        
        # Log findings
        logging.info(f"Terraform plan scan complete: {len(findings)} finding(s)")
        for f in findings:
            logging.info(f"{f['severity']} | {f['resource']} | {f['issue']}")
        
        # Generate report
        report = {
            "tool": "CloudSentry",
            "mode": "tfplan",
            "scan_time": datetime.now(timezone.utc).isoformat(),
            "terraform_plan": args.tfplan,
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
        
        logging.info("Report saved to cloudsentry_report.json")
        
        # Exit based on severity
        if high_risk_exists:
            logging.error("High risk detected in Terraform plan — failing CI")
            sys.exit(1)
        
        logging.info("No high risk detected in Terraform plan — passing CI")
        sys.exit(0)
        
    except FileNotFoundError:
        logging.error(f"Terraform plan file not found: {args.tfplan}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logging.error(f"Invalid JSON in Terraform plan file: {e}")
        sys.exit(1)
    except Exception as e:
        logging.error(f"Error processing Terraform plan: {e}")
        sys.exit(1)

# -----------------------------
# AWS Scanning Mode (Original)
# -----------------------------
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
