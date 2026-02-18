# CloudSentry v2 - Quick Start Guide

## 🎯 What's New in v2

CloudSentry v2 adds **Terraform Plan Scanning** - the ability to detect security issues in your infrastructure **before** deployment!

### Key Features

✅ Scan Terraform plans before applying changes  
✅ Modular check system - easily add new security checks  
✅ S3 public bucket detection  
✅ Clear, actionable security findings  
✅ CI/CD ready with exit codes  

---

## 🚀 Quick Start

### 1. Scan a Terraform Plan

```bash
# Generate a Terraform plan
terraform plan -out=tfplan
terraform show -json tfplan > tfplan.json

# Scan with CloudSentry
python cloudsentry.py --tfplan tfplan.json
```

### 2. Try the Example

```bash
# Scan the included example (intentionally has security issues)
python cloudsentry.py --tfplan example_tfplan.json
```

**Expected Output:**
```
INFO | Starting Terraform plan scan: example_tfplan.json
INFO | Loading 1 check module(s): s3_checks
WARNING | PUBLIC S3 DETECTED: aws_s3_bucket.public_bucket has ACL=public-read
ERROR | High risk detected in Terraform plan — failing CI
```

### 3. View the Report

```bash
cat cloudsentry_report.json
```

**Sample Report:**
```json
{
  "tool": "CloudSentry",
  "mode": "tfplan",
  "summary": {
    "total_findings": 2,
    "high": 2
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

## 🔍 Current Security Checks

### S3 Bucket Security

| Check | Severity | Description |
|-------|----------|-------------|
| Public ACL | HIGH | Detects `public-read` or `public-read-write` ACLs |
| Public Access Block | HIGH | Detects disabled public access block settings |

---

## 🔧 Adding Your Own Checks

Create a new file in `checks/` directory:

```python
# checks/ec2_checks.py

def run_check(resources):
    """Check for EC2 security issues"""
    findings = []
    
    for resource in resources:
        if resource.get('type') == 'aws_instance':
            # Your security logic here
            pass
    
    return findings
```

CloudSentry will **automatically discover and run** your new check!

---

## 📊 CI/CD Integration

### GitHub Actions Example

```yaml
- name: Scan Terraform Plan
  run: |
    terraform plan -out=tfplan
    terraform show -json tfplan > tfplan.json
    python cloudsentry.py --tfplan tfplan.json
```

### Exit Codes

- `0` = ✅ No high-risk issues (CI passes)
- `1` = ❌ High-risk issues found (CI fails)

---

## 📚 Additional Resources

- **README.md** - Complete project documentation
- **v2_LEARNING_NOTES.md** - Deep dive into Python & DevOps concepts
- **EXAMPLE_README.md** - Details about the example Terraform plan
- **test_cloudsentry.py** - Run comprehensive tests

---

## 🧪 Running Tests

```bash
# Run all tests
python test_cloudsentry.py

# Expected: ✅ All tests PASSED
```

---

## ❓ Common Questions

**Q: Can I still scan live AWS resources?**  
A: Yes! CloudSentry v2 maintains full backward compatibility.

```bash
CLOUDSENTRY_MODE=aws python cloudsentry.py  # Scan live AWS
python cloudsentry.py --tfplan plan.json     # Scan Terraform plan
```

**Q: How do I add checks for other AWS resources?**  
A: Create a new file like `checks/rds_checks.py` with a `run_check()` function. CloudSentry will automatically find and run it!

**Q: What if my Terraform plan has no issues?**  
A: CloudSentry will exit with code 0 and report zero findings.

---

## 🎓 Learning Path

1. **Start here**: Run the example and explore the output
2. **Next**: Read `v2_LEARNING_NOTES.md` for in-depth explanations
3. **Then**: Try creating your own security check
4. **Finally**: Integrate into your CI/CD pipeline

---

**Built with ❤️ for DevSecOps learning**
