"""
S3 Security Checks for Terraform Plans

This module implements security checks for AWS S3 buckets in Terraform plan files.
It detects configurations that could make S3 buckets publicly accessible.

Learning Notes:
- Terraform plans use JSON format with "resource_changes" array
- Each resource has "type", "name", and "change" with "after" values
- S3 public access can be configured via ACL or public access block settings
"""

import logging
from typing import List, Dict, Any


def run_check(resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Run S3-specific security checks on Terraform plan resources.
    
    Args:
        resources: List of resource dictionaries from Terraform plan
        
    Returns:
        List of security findings
        
    Learning Note:
        This function is called by the check loader in __init__.py
        It follows a standard interface so checks can be added easily.
    """
    findings = []
    
    for resource in resources:
        resource_type = resource.get('type', '')
        resource_name = resource.get('name', 'unknown')
        resource_address = resource.get('address', f"{resource_type}.{resource_name}")
        
        # Get the planned state (what will be created/modified)
        change = resource.get('change', {})
        after = change.get('after', {})
        
        # Check for S3 bucket resources
        if resource_type == 'aws_s3_bucket':
            # Check for public ACL
            acl = after.get('acl', '')
            if acl in ['public-read', 'public-read-write']:
                findings.append({
                    'resource': resource_address,
                    'issue': f'S3 bucket configured with public ACL: {acl}',
                    'severity': 'HIGH',
                    'recommendation': 'Use private ACL and configure bucket policy with specific permissions instead'
                })
                logging.warning(f"PUBLIC S3 DETECTED: {resource_address} has ACL={acl}")
        
        # Check for S3 bucket public access block configuration
        elif resource_type == 'aws_s3_bucket_public_access_block':
            # When public access block is disabled, bucket can be made public
            block_public_acls = after.get('block_public_acls', True)
            block_public_policy = after.get('block_public_policy', True)
            ignore_public_acls = after.get('ignore_public_acls', True)
            restrict_public_buckets = after.get('restrict_public_buckets', True)
            
            if not block_public_acls or not block_public_policy or \
               not ignore_public_acls or not restrict_public_buckets:
                disabled_settings = []
                if not block_public_acls:
                    disabled_settings.append('block_public_acls')
                if not block_public_policy:
                    disabled_settings.append('block_public_policy')
                if not ignore_public_acls:
                    disabled_settings.append('ignore_public_acls')
                if not restrict_public_buckets:
                    disabled_settings.append('restrict_public_buckets')
                
                findings.append({
                    'resource': resource_address,
                    'issue': f'S3 public access block disabled: {", ".join(disabled_settings)}',
                    'severity': 'HIGH',
                    'recommendation': 'Enable all S3 public access block settings to prevent accidental public exposure'
                })
                logging.warning(f"PUBLIC S3 RISK: {resource_address} has disabled settings: {disabled_settings}")
    
    return findings
