#!/usr/bin/env python3
"""
Test Coverage Analysis and Setup Script
Analyzes current test coverage and identifies gaps
"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))


def analyze_src_modules():
    """Analyze all modules in src/ directory"""
    src_path = project_root / "src"
    modules = {}
    
    for root, dirs, files in os.walk(src_path):
        # Skip __pycache__ and other non-source directories
        dirs[:] = [d for d in dirs if not d.startswith('__pycache__')]
        
        for file in files:
            if file.endswith('.py') and not file.startswith('__'):
                file_path = Path(root) / file
                relative_path = file_path.relative_to(src_path)
                module_name = str(relative_path).replace(os.sep, '.').replace('.py', '')
                modules[module_name] = file_path
    
    return modules


def analyze_existing_tests():
    """Analyze existing test files"""
    tests_path = project_root / "tests"
    existing_tests = {
        'unit': [],
        'integration': []
    }
    
    # Unit tests
    unit_path = tests_path / "unit"
    if unit_path.exists():
        for test_file in unit_path.glob("test_*.py"):
            existing_tests['unit'].append(test_file.stem)
    
    # Integration tests
    integration_path = tests_path / "integration"
    if integration_path.exists():
        for test_file in integration_path.glob("test_*.py"):
            existing_tests['integration'].append(test_file.stem)
    
    return existing_tests


def identify_coverage_gaps():
    """Identify modules that need test coverage"""
    modules = analyze_src_modules()
    existing_tests = analyze_existing_tests()
    
    # Extract module names from tests
    tested_modules = set()
    for test_list in existing_tests.values():
        for test_name in test_list:
            # Remove 'test_' prefix to get module name
            module_name = test_name.replace('test_', '')
            tested_modules.add(module_name)
    
    # Group modules by package
    packages = {}
    for module_name, file_path in modules.items():
        parts = module_name.split('.')
        package = parts[0] if len(parts) > 1 else 'root'
        if package not in packages:
            packages[package] = []
        packages[package].append(module_name)
    
    # Identify untested modules
    untested = []
    for module_name in modules.keys():
        base_name = module_name.split('.')[-1]  # Get just the filename part
        if not any(base_name in test for test in tested_modules):
            untested.append(module_name)
    
    return packages, untested, tested_modules


def generate_coverage_report():
    """Generate comprehensive coverage analysis report"""
    print("🧪 Smart Knowledge Repository - Test Coverage Analysis")
    print("=" * 60)
    
    modules = analyze_src_modules()
    existing_tests = analyze_existing_tests()
    packages, untested, tested_modules = identify_coverage_gaps()
    
    print(f"\n📊 Module Analysis:")
    print(f"   Total source modules: {len(modules)}")
    print(f"   Total unit tests: {len(existing_tests['unit'])}")
    print(f"   Total integration tests: {len(existing_tests['integration'])}")
    
    print(f"\n📁 Packages and Modules:")
    for package, module_list in packages.items():
        print(f"   {package}/ ({len(module_list)} modules)")
        for module in sorted(module_list):
            tested = any(module.split('.')[-1] in test for test in tested_modules)
            status = "✅" if tested else "❌"
            print(f"     {status} {module}")
    
    print(f"\n🎯 Test Coverage Summary:")
    total_modules = len(modules)
    tested_count = total_modules - len(untested)
    coverage_percent = (tested_count / total_modules * 100) if total_modules > 0 else 0
    
    print(f"   Tested modules: {tested_count}/{total_modules} ({coverage_percent:.1f}%)")
    print(f"   Missing tests: {len(untested)} modules")
    
    if untested:
        print(f"\n❌ Modules needing tests:")
        for module in sorted(untested):
            print(f"     • {module}")
    
    print(f"\n✅ Existing test coverage:")
    for category, tests in existing_tests.items():
        print(f"   {category.title()} tests ({len(tests)}):")
        for test in sorted(tests):
            print(f"     • {test}")
    
    return {
        'total_modules': total_modules,
        'tested_modules': tested_count,
        'coverage_percent': coverage_percent,
        'untested_modules': untested,
        'packages': packages,
        'existing_tests': existing_tests
    }


def generate_test_plan(coverage_data):
    """Generate a plan for additional tests needed"""
    print(f"\n📋 Test Implementation Plan:")
    print("=" * 40)
    
    untested = coverage_data['untested_modules']
    packages = coverage_data['packages']
    
    # Priority categories for testing
    priority_map = {
        'core': 1,      # Critical infrastructure
        'storage': 1,   # Data management
        'search': 1,    # Core functionality
        'ai': 2,        # AI features
        'crawlers': 2,  # Web scraping
        'api': 2,       # API endpoints
        'processors': 3, # Data processing
        'services': 3,  # Additional services
        'migration': 3, # Migration utilities
        'setup': 3,     # Setup scripts
        'scripts': 4,   # Utility scripts
        'ui': 4         # User interface
    }
    
    # Group untested modules by priority
    priority_groups = {}
    for module in untested:
        package = module.split('.')[0]
        priority = priority_map.get(package, 4)
        if priority not in priority_groups:
            priority_groups[priority] = []
        priority_groups[priority].append(module)
    
    for priority in sorted(priority_groups.keys()):
        priority_name = {1: "HIGH", 2: "MEDIUM", 3: "LOW", 4: "OPTIONAL"}[priority]
        modules = priority_groups[priority]
        print(f"\n🎯 Priority {priority} ({priority_name}) - {len(modules)} modules:")
        
        for module in sorted(modules):
            package = module.split('.')[0]
            filename = module.split('.')[-1]
            print(f"   • test_{filename}.py (covers {module})")
    
    return priority_groups


if __name__ == "__main__":
    # Generate coverage analysis
    coverage_data = generate_coverage_report()
    
    # Generate test plan  
    priority_groups = generate_test_plan(coverage_data)
    
    print(f"\n🚀 Next Steps:")
    print("1. Run existing tests: pytest tests/unit tests/integration")
    print("2. Generate coverage report: pytest --cov=src --cov-report=html")
    print("3. Implement high-priority missing tests")
    print("4. Set up CI/CD pipeline with test automation")
    
    print(f"\n💡 Recommended test commands:")
    print("   # Run all tests with coverage")
    print("   pytest --cov=src --cov-report=term-missing")
    print("   # Run only unit tests")
    print("   pytest tests/unit/")
    print("   # Run only integration tests")
    print("   pytest tests/integration/")
    print("   # Run with HTML coverage report")
    print("   pytest --cov=src --cov-report=html")
