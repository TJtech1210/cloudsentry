# TODO: Replace fake findings with IAM user data using boto3
import boto3
import sys
iam = boto3.client("iam")

response = iam.list_users()
users = response.get("Users", [])

findings = []

if users:
    findings.append("High risk: IAM users exist in account")
else:
    findings.append("No IAM users found")


high_risk_exists = False

for finding in findings:
  print(finding)
  if "High risk" in finding:
    high_risk_exists = True

if high_risk_exists:
  sys.exit(1)
else:
  sys.exit(0)

aws configure





