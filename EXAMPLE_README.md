# Example Terraform Plan

This directory contains an example Terraform plan JSON file for testing CloudSentry's Terraform scanning capabilities.

## File: example_tfplan.json

This is a sample Terraform plan that demonstrates various security scenarios:

### Resources Included:

1. **aws_s3_bucket.public_bucket** - ⚠️ HIGH RISK
   - Has `acl: "public-read"` 
   - Will be flagged by CloudSentry

2. **aws_s3_bucket.private_bucket** - ✅ SECURE
   - Has `acl: "private"`
   - Will pass CloudSentry checks

3. **aws_s3_bucket_public_access_block.bad_config** - ⚠️ HIGH RISK
   - All public access block settings disabled
   - Will be flagged by CloudSentry

4. **aws_s3_bucket_public_access_block.good_config** - ✅ SECURE
   - All public access block settings enabled
   - Will pass CloudSentry checks

## Usage

Test CloudSentry with this example:

```bash
python cloudsentry.py --tfplan example_tfplan.json
```

Expected output:
- 2 HIGH severity findings
- Exit code: 1 (failure)

## Creating Your Own Test Plans

To create a Terraform plan JSON from real Terraform code:

```bash
# In your Terraform project directory
terraform plan -out=tfplan
terraform show -json tfplan > tfplan.json

# Scan with CloudSentry
python cloudsentry.py --tfplan tfplan.json
```
