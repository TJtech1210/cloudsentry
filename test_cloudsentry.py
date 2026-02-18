#!/usr/bin/env python3
"""
Simple test script for CloudSentry v2 functionality.
This script validates both AWS and Terraform plan scanning modes.
"""

import subprocess
import sys
import os
import json

def run_command(cmd, expected_exit_code=None):
    """Run a command and check its exit code."""
    print(f"\n{'='*60}")
    print(f"Running: {' '.join(cmd)}")
    print('='*60)
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    print("STDOUT:")
    print(result.stdout)
    
    if result.stderr:
        print("STDERR:")
        print(result.stderr)
    
    print(f"Exit code: {result.returncode}")
    
    if expected_exit_code is not None and result.returncode != expected_exit_code:
        print(f"❌ FAILED: Expected exit code {expected_exit_code}, got {result.returncode}")
        return False
    
    print("✅ PASSED")
    return True

def validate_report(expected_mode, min_findings=0):
    """Validate the generated report."""
    print("\n" + "="*60)
    print("Validating cloudsentry_report.json")
    print("="*60)
    
    if not os.path.exists('cloudsentry_report.json'):
        print("❌ FAILED: Report file not found")
        return False
    
    with open('cloudsentry_report.json', 'r') as f:
        report = json.load(f)
    
    # Check required fields
    required_fields = ['tool', 'mode', 'scan_time', 'summary', 'findings']
    for field in required_fields:
        if field not in report:
            print(f"❌ FAILED: Missing field '{field}' in report")
            return False
    
    # Check mode
    if report['mode'] != expected_mode:
        print(f"❌ FAILED: Expected mode '{expected_mode}', got '{report['mode']}'")
        return False
    
    # Check findings count
    if len(report['findings']) < min_findings:
        print(f"❌ FAILED: Expected at least {min_findings} findings, got {len(report['findings'])}")
        return False
    
    print(f"✅ PASSED: Report contains {len(report['findings'])} finding(s)")
    return True

def main():
    """Run all tests."""
    print("CloudSentry v2 Test Suite")
    print("="*60)
    
    all_passed = True
    
    # Test 1: Help message
    print("\n📋 Test 1: Help message")
    if not run_command(['python', 'cloudsentry.py', '--help'], expected_exit_code=0):
        all_passed = False
    
    # Test 2: Terraform plan scanning with security issues (should fail)
    print("\n📋 Test 2: Terraform plan scanning with security issues")
    if not run_command(['python', 'cloudsentry.py', '--tfplan', 'example_tfplan.json'], expected_exit_code=1):
        all_passed = False
    if not validate_report('tfplan', min_findings=2):
        all_passed = False
    
    # Test 3: AWS mock mode scanning (should fail due to mock issues)
    print("\n📋 Test 3: AWS mock mode scanning")
    env = os.environ.copy()
    env['CLOUDSENTRY_MODE'] = 'mock'
    result = subprocess.run(['python', 'cloudsentry.py'], env=env, capture_output=True, text=True)
    print(f"Exit code: {result.returncode}")
    if result.returncode != 1:
        print(f"❌ FAILED: Expected exit code 1 (mock has issues), got {result.returncode}")
        all_passed = False
    else:
        print("✅ PASSED")
    if not validate_report('mock', min_findings=3):
        all_passed = False
    
    # Test 4: Error handling - missing file
    print("\n📋 Test 4: Error handling - missing file")
    if not run_command(['python', 'cloudsentry.py', '--tfplan', 'nonexistent.json'], expected_exit_code=1):
        all_passed = False
    
    # Final summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    if all_passed:
        print("✅ All tests PASSED")
        return 0
    else:
        print("❌ Some tests FAILED")
        return 1

if __name__ == '__main__':
    sys.exit(main())
