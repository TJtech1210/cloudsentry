"""
CloudSentry Modular Security Checks

This module provides a framework for running security checks on Terraform plan files.
Checks are organized as separate modules that can be easily extended.

Learning Notes:
- __init__.py makes this directory a Python package
- The check loader dynamically discovers and runs all available checks
- Each check module should implement a run_check() function
"""

import importlib
import os
import logging
from typing import List, Dict, Any


def get_available_checks() -> List[str]:
    """
    Discover all available check modules in the checks/ directory.
    
    Returns:
        List of check module names (without .py extension)
    
    Learning Note:
        This uses os.listdir to scan the directory for .py files.
        We filter out __init__.py and __pycache__ to get only check modules.
    """
    checks_dir = os.path.dirname(__file__)
    check_files = []
    
    for filename in os.listdir(checks_dir):
        if filename.endswith('_checks.py'):
            # Remove .py extension to get module name
            check_files.append(filename[:-3])
    
    return check_files


def load_and_run_checks(resources: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Load all available checks and run them against the provided resources.
    
    Args:
        resources: List of resource dictionaries from Terraform plan
        
    Returns:
        List of findings (security issues discovered)
    
    Learning Note:
        importlib.import_module() dynamically loads Python modules at runtime.
        This allows us to add new checks without modifying this loader code.
    """
    all_findings = []
    check_modules = get_available_checks()
    
    logging.info(f"Loading {len(check_modules)} check module(s): {', '.join(check_modules)}")
    
    for module_name in check_modules:
        try:
            # Dynamic import: loads checks.s3_checks, checks.ec2_checks, etc.
            module = importlib.import_module(f'checks.{module_name}')
            
            # Each check module should have a run_check() function
            if hasattr(module, 'run_check'):
                logging.info(f"Running check: {module_name}")
                findings = module.run_check(resources)
                all_findings.extend(findings)
            else:
                logging.warning(f"Check module {module_name} missing run_check() function")
                
        except Exception as e:
            logging.error(f"Error loading check module {module_name}: {e}")
    
    return all_findings
