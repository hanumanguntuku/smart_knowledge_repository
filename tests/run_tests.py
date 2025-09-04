#!/usr/bin/env python3
"""
Test runner script with comprehensive coverage reporting
"""
import subprocess
import sys
import os
from pathlib import Path

# Project root
project_root = Path(__file__).parent.parent
os.chdir(project_root)

# Python executable in virtual environment
python_exe = project_root / "venv" / "Scripts" / "python.exe"

def run_command(cmd, description):
    """Run a command and report results"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=300)
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ {description} - SUCCESS")
        else:
            print(f"❌ {description} - FAILED (exit code: {result.returncode})")
        
        return result.returncode == 0
        
    except subprocess.TimeoutExpired:
        print(f"⏰ {description} - TIMEOUT")
        return False
    except Exception as e:
        print(f"💥 {description} - ERROR: {str(e)}")
        return False

def main():
    """Run comprehensive test suite"""
    print("🧪 Smart Knowledge Repository - Test Suite Runner")
    print(f"📁 Working directory: {project_root}")
    print(f"🐍 Python: {python_exe}")
    
    # Test commands to run
    test_commands = [
        {
            "cmd": f'"{python_exe}" -m pytest tests/unit/ -v --tb=short',
            "description": "Unit Tests"
        },
        {
            "cmd": f'"{python_exe}" -m pytest tests/integration/ -v --tb=short',
            "description": "Integration Tests"
        },
        {
            "cmd": f'"{python_exe}" -m pytest tests/unit/ tests/integration/ --cov=src --cov-report=term-missing --cov-report=html:tests/coverage_html',
            "description": "Coverage Analysis"
        },
        {
            "cmd": f'"{python_exe}" -m pytest tests/unit/ tests/integration/ --html=tests/test_report.html --self-contained-html',
            "description": "HTML Test Report"
        }
    ]
    
    results = {}
    
    for test_command in test_commands:
        success = run_command(test_command["cmd"], test_command["description"])
        results[test_command["description"]] = success
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUITE SUMMARY")
    print(f"{'='*60}")
    
    total_tests = len(results)
    passed_tests = sum(1 for success in results.values() if success)
    
    for test_name, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\n🎯 Overall: {passed_tests}/{total_tests} test suites passed")
    
    # Reports
    print(f"\n📋 Generated Reports:")
    coverage_html = project_root / "tests" / "coverage_html" / "index.html"
    test_report = project_root / "tests" / "test_report.html"
    
    if coverage_html.exists():
        print(f"📊 Coverage Report: {coverage_html}")
    
    if test_report.exists():
        print(f"🧪 Test Report: {test_report}")
    
    # Exit with error code if any tests failed
    if passed_tests < total_tests:
        sys.exit(1)
    else:
        print("\n🎉 All test suites completed successfully!")

if __name__ == "__main__":
    main()
