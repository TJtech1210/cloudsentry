import sys
findings = ["PII", "MFA", "Weak Credentials"] 
high_risk_exists = False

for finding in findings:
  print(finding)
  if "High risk" in finding:
    high_risk_exists = True

if high_risk_exists:
  sys.exit(1)
else:
  sys.exit(0)




