# CloudSentry v2: Learning Notes

Welcome! This file accompanies the v2 development branch. Whenever a new feature or core commit is made, you'll find an explanation here.

---

## Table of Contents
- [Intro & Vision for v2](#intro)
- [Feature Summaries: What & Why](#features)
- [How-to Run & Experiment](#howto)
- [Python & DevOps Concepts](#concepts)
- [Links & Further Reading](#links)

---

## <a name="intro"></a>Intro & Vision for v2

CloudSentry v2 transforms the project into a pre-deployment (IaC-focused) security gate—moving beyond AWS scans to scanning "terraform plan" files, with modular security checks you can expand as you learn. The goal: real DevSecOps, not just read-only reports.

### Why Terraform Plan Scanning?

Traditional cloud security tools scan resources **after** they're deployed. CloudSentry v2 scans your infrastructure **before** it's created by analyzing Terraform plan files. This "shift-left" approach catches security issues during development, not in production.

Benefits:
- **Prevent mistakes before they happen**: Catch public S3 buckets before creation
- **Faster feedback loop**: Developers know immediately if their IaC has issues
- **CI/CD integration**: Automatically fail builds with security problems
- **Cost savings**: No need to deploy, scan, and tear down test infrastructure

---

## <a name="features"></a>Feature Summaries

### v2.0: Terraform Plan Scanning and Modular Architecture

**What changed:**
- Added `--tfplan` CLI argument to accept Terraform plan JSON files
- Created modular `checks/` directory for organizing security checks
- Implemented S3 public bucket detection (ACL and public access block)
- Updated CLI to support both AWS scanning and Terraform plan modes

**Files added/modified:**
- `checks/__init__.py`: Check loader with dynamic module discovery
- `checks/s3_checks.py`: S3-specific security checks
- `cloudsentry.py`: Updated with argparse and Terraform plan parsing
- `README.md`: New usage examples and documentation
- `.gitignore`: Ignore test files and generated reports

**How it works:**

1. **User runs**: `python cloudsentry.py --tfplan tfplan.json`
2. **CloudSentry parses** the JSON to extract `resource_changes` array
3. **Check loader discovers** all `*_checks.py` modules in `checks/` directory
4. **Each check runs** against the resources, returning findings
5. **Results are aggregated** and a report is generated
6. **Exit code is set** based on severity (HIGH = fail CI)

---

## <a name="howto"></a>How-to Run & Experiment

### Generating a Terraform Plan for Scanning

First, create a Terraform plan and convert it to JSON:

```bash
# Initialize Terraform
terraform init

# Generate a plan file
terraform plan -out=tfplan

# Convert the plan to JSON format
terraform show -json tfplan > tfplan.json
```

### Scanning the Plan

```bash
# Scan the Terraform plan
python cloudsentry.py --tfplan tfplan.json

# The exit code indicates pass/fail
echo $?  # 0 = pass, 1 = fail
```

### Understanding the Output

CloudSentry logs each step:
```
INFO | Starting Terraform plan scan: tfplan.json
INFO | Successfully loaded Terraform plan JSON
INFO | Found 4 resource change(s) in plan
INFO | Loading 1 check module(s): s3_checks
INFO | Running check: s3_checks
WARNING | PUBLIC S3 DETECTED: aws_s3_bucket.public_bucket has ACL=public-read
ERROR | High risk detected in Terraform plan — failing CI
```

The JSON report provides structured data:
```json
{
  "tool": "CloudSentry",
  "mode": "tfplan",
  "summary": {
    "total_findings": 2,
    "high": 2
  },
  "findings": [...]
}
```

### Testing with Sample Data

A test Terraform plan is included for experimentation:

```bash
python cloudsentry.py --tfplan test_tfplan.json
```

This sample plan intentionally includes security issues to demonstrate detection.

---

## <a name="concepts"></a>Python & DevOps Concepts

### 1. Argument Parsing with `argparse`

**What it is**: Python's standard library for parsing command-line arguments.

**Why we use it**: CloudSentry needs to accept different inputs (AWS scan vs. Terraform plan).

**How it works**:
```python
parser = argparse.ArgumentParser(description='...')
parser.add_argument('--tfplan', type=str, help='Path to Terraform plan')
args = parser.parse_args()

if args.tfplan:
    # Scan Terraform plan
else:
    # Scan AWS resources
```

**Learning resource**: [Python argparse docs](https://docs.python.org/3/library/argparse.html)

---

### 2. JSON Parsing and Dictionary Navigation

**What it is**: Working with JSON data structures in Python.

**Why we use it**: Terraform plans are JSON files with nested dictionaries and arrays.

**How it works**:
```python
with open('tfplan.json', 'r') as f:
    tfplan = json.load(f)  # Parse JSON to Python dict

# Navigate nested structure
resources = tfplan.get('resource_changes', [])
for resource in resources:
    resource_type = resource.get('type', '')
    after = resource.get('change', {}).get('after', {})
```

**Key methods**:
- `dict.get(key, default)`: Safe dictionary access with fallback
- `json.load()`: Parse JSON from file
- `json.dump()`: Write Python objects as JSON

---

### 3. Dynamic Module Loading with `importlib`

**What it is**: Loading Python modules at runtime by name.

**Why we use it**: CloudSentry discovers check modules automatically without hardcoding names.

**How it works**:
```python
import importlib

# List files in checks/ directory
for filename in os.listdir('checks/'):
    if filename.endswith('_checks.py'):
        module_name = filename[:-3]  # Remove .py
        
        # Load the module dynamically
        module = importlib.import_module(f'checks.{module_name}')
        
        # Call its run_check() function
        if hasattr(module, 'run_check'):
            findings = module.run_check(resources)
```

**Benefits**:
- Add new checks by creating files (no code changes needed)
- Extensible architecture
- Separation of concerns

---

### 4. Package Structure with `__init__.py`

**What it is**: Special files that make directories into Python packages.

**Why we use it**: The `checks/` directory is a package containing multiple modules.

**How it works**:
```
checks/
├── __init__.py       # Makes 'checks' a package
├── s3_checks.py      # S3 security checks
└── ec2_checks.py     # EC2 security checks (future)
```

**In code**:
```python
from checks import load_and_run_checks  # Import from package
```

**Learning resource**: [Python Packages](https://docs.python.org/3/tutorial/modules.html#packages)

---

### 5. Terraform Plan JSON Structure

**What it is**: The output format from `terraform show -json tfplan`.

**Why we need it**: To understand which resources will be created/modified.

**Key structure**:
```json
{
  "format_version": "1.2",
  "terraform_version": "1.5.0",
  "resource_changes": [
    {
      "address": "aws_s3_bucket.my_bucket",
      "type": "aws_s3_bucket",
      "name": "my_bucket",
      "change": {
        "actions": ["create"],
        "before": null,
        "after": {
          "bucket": "my-bucket-name",
          "acl": "public-read"
        }
      }
    }
  ]
}
```

**What we extract**:
- `resource_changes`: Array of planned changes
- `type`: Resource type (e.g., `aws_s3_bucket`)
- `change.after`: The final state after applying the plan
- `address`: Unique resource identifier

---

### 6. Exit Codes and CI Integration

**What it is**: Process exit status used by shells and CI systems.

**Why we use it**: To signal pass/fail to CI pipelines.

**How it works**:
```python
if high_risk_exists:
    logging.error("High risk detected — failing CI")
    sys.exit(1)  # Non-zero = failure

logging.info("No high risk detected — passing CI")
sys.exit(0)  # Zero = success
```

**In CI**:
```bash
python cloudsentry.py --tfplan tfplan.json
if [ $? -ne 0 ]; then
    echo "Security scan failed!"
    exit 1
fi
```

---

### 7. Exception Handling and Error Messages

**What it is**: Gracefully handling errors and providing helpful messages.

**Why we use it**: Files might not exist, JSON might be invalid, etc.

**How it works**:
```python
try:
    with open(args.tfplan, 'r') as f:
        tfplan = json.load(f)
except FileNotFoundError:
    logging.error(f"File not found: {args.tfplan}")
    sys.exit(1)
except json.JSONDecodeError as e:
    logging.error(f"Invalid JSON: {e}")
    sys.exit(1)
```

**Best practices**:
- Catch specific exceptions (not bare `except:`)
- Log helpful error messages
- Exit with appropriate codes

---

### 8. Type Hints and Documentation

**What it is**: Python type annotations and docstrings.

**Why we use it**: Makes code more readable and maintainable.

**How it works**:
```python
from typing import List, Dict, Any

def run_check(resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Run security checks on resources.
    
    Args:
        resources: List of resource dictionaries from Terraform
        
    Returns:
        List of security findings
    """
    findings = []
    # ... implementation ...
    return findings
```

**Benefits**:
- IDE autocomplete and type checking
- Self-documenting code
- Easier to understand for learners

---

## <a name="links"></a>Links & Further Reading

### Terraform
- [Terraform Plan JSON Format](https://www.terraform.io/internals/json-format)
- [Terraform Show Command](https://www.terraform.io/cli/commands/show)
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)

### Python
- [argparse Documentation](https://docs.python.org/3/library/argparse.html)
- [importlib for Dynamic Imports](https://docs.python.org/3/library/importlib.html)
- [Python JSON Module](https://docs.python.org/3/library/json.html)
- [Python Type Hints](https://docs.python.org/3/library/typing.html)

### AWS Security
- [S3 Access Control](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-overview.html)
- [S3 Block Public Access](https://docs.aws.amazon.com/AmazonS3/latest/userguide/access-control-block-public-access.html)
- [AWS Security Best Practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)

### DevSecOps
- [Shift-Left Security](https://www.devsecops.org/)
- [Infrastructure as Code Security](https://www.cisecurity.org/insights/blog/infrastructure-as-code-security-best-practices)

---

**Happy Learning! 🚀**

As you continue developing CloudSentry v2, remember:
1. Start simple, iterate gradually
2. Test each component independently
3. Document as you learn
4. Security is a journey, not a destination

*This document will be updated with each major v2 feature addition.*