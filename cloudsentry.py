# TODO: Replace fake findings with IAM user data using boto3
import sys
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)


USE_MOCK_IAM = True

if not USE_MOCK_IAM:
    import boto3
    iam = boto3.client("iam")

if USE_MOCK_IAM:
    response = {
    "Users": []
}

else:
    response = iam.list_users()
users = response.get("Users", [])

findings = []

if users:
    findings.append("High risk: IAM users exist in account")
else:
    findings.append("No IAM users found")


high_risk_exists = False

for finding in findings:
  logging.info(finding)
  if high_risk_exists:
    logging.error("High risk detected — failing CI")
    sys.exit(1)
else:
    logging.info("No high risk detected — passing CI")
    sys.exit(0)







