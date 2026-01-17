# CloudSentry

CloudSentry is a lightweight cloud security checker that runs automatically in CI to catch risky behavior early.

## What it does (v1)
CloudSentry analyzes cloud-related data, prints a security report, and fails the build if risk is detected.

This project focuses on:
- automation over dashboards
- early detection instead of cleanup
- simple rules that are easy to explain

## Why this exists
Cloud security issues are often discovered too late.
CloudSentry is designed to run **before changes are merged**, so problems are caught early.

## How it works (high level)
- Runs automatically on pull requests
- Executes a Python-based security check
- Outputs findings to the CI logs
- Fails the workflow when risk is found

## Current status
🚧 Initial setup  
- Repository created  
- GitHub Actions workflow in progress  
- Security logic coming next  

## Tech (intentionally minimal)
- GitHub Actions
- Python
- Linux-based CI runner

More tools will be added only when they are required.
