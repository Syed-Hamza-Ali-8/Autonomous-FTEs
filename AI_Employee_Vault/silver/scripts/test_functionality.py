#!/usr/bin/env python3
"""
Comprehensive Silver Tier Functionality Test

Tests all components without requiring external credentials:
- Python syntax validation
- Import testing
- Configuration validation
- Basic class initialization
- File structure verification
"""

import sys
import os
from pathlib import Path
import importlib.util
import yaml

# Colors
class Colors:
    GREEN = '\033[0;32m'
    RED = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'

def print_header(text):
    print(f"\n{Colors.BLUE}{'=' * 60}{Colors.NC}")
    print(f"{Colors.BLUE}{text}{Colors.NC}")
    print(f"{Colors.BLUE}{'=' * 60}{Colors.NC}\n")

def print_success(text):
    print(f"{Colors.GREEN}✅ {text}{Colors.NC}")

def print_error(text):
    print(f"{Colors.RED}❌ {text}{Colors.NC}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.NC}")

def test_python_syntax():
    """Test all Python files for syntax errors."""
    print_header("Testing Python Syntax")

    vault_path = Path("/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault")
    silver_path = vault_path / "silver"

    python_files = list(silver_path.rglob("*.py"))
    errors = []

    for py_file in python_files:
        try:
            with open(py_file, 'r') as f:
                compile(f.read(), str(py_file), 'exec')
        except SyntaxError as e:
            errors.append((py_file, str(e)))

    if errors:
        print_error(f"Found {len(errors)} syntax errors:")
        for file, error in errors:
            print(f"  {file}: {error}")
        return False
    else:
        print_success(f"All {len(python_files)} Python files have valid syntax")
        return True

def test_imports():
    """Test if key modules can be imported."""
    print_header("Testing Module Imports")

    modules_to_test = [
        ("silver.src.utils.logger", "Logger utilities"),
        ("silver.src.utils.yaml_parser", "YAML parser"),
        ("silver.src.utils.file_utils", "File utilities"),
    ]

    sys.path.insert(0, "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault")

    success_count = 0
    for module_name, description in modules_to_test:
        try:
            importlib.import_module(module_name)
            print_success(f"{description}: {module_name}")
            success_count += 1
        except ImportError as e:
            print_error(f"{description}: {module_name} - {e}")
        except Exception as e:
            print_warning(f"{description}: {module_name} - {e}")

    return success_count == len(modules_to_test)

def test_yaml_configs():
    """Test YAML configuration files."""
    print_header("Testing YAML Configuration Files")

    vault_path = Path("/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault")

    yaml_files = [
        vault_path / "silver/config/watcher_config.yaml",
        vault_path / "silver/config/approval_rules.yaml",
        vault_path / "silver/config/schedules/schedules.yaml",
    ]

    success_count = 0
    for yaml_file in yaml_files:
        if not yaml_file.exists():
            print_warning(f"File not found: {yaml_file.name}")
            continue

        try:
            with open(yaml_file, 'r') as f:
                yaml.safe_load(f)
            print_success(f"Valid YAML: {yaml_file.name}")
            success_count += 1
        except yaml.YAMLError as e:
            print_error(f"Invalid YAML: {yaml_file.name} - {e}")

    return success_count == len([f for f in yaml_files if f.exists()])

def test_file_structure():
    """Test that all expected files exist."""
    print_header("Testing File Structure")

    vault_path = Path("/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault")

    expected_files = {
        "Python Modules": [
            "silver/src/utils/logger.py",
            "silver/src/utils/yaml_parser.py",
            "silver/src/utils/file_utils.py",
            "silver/src/approval/approval_manager.py",
            "silver/src/approval/approval_checker.py",
            "silver/src/approval/approval_notifier.py",
            "silver/src/planning/plan_generator.py",
            "silver/src/planning/task_analyzer.py",
            "silver/src/planning/plan_tracker.py",
            "silver/src/actions/action_executor.py",
            "silver/src/actions/email_sender.py",
            "silver/src/actions/whatsapp_sender.py",
            "silver/src/scheduling/scheduler.py",
            "silver/src/scheduling/schedule_manager.py",
        ],
        "Scripts": [
            "silver/scripts/startup.sh",
            "silver/scripts/shutdown.sh",
            "silver/scripts/health_check.py",
            "silver/scripts/test_approval.py",
            "silver/scripts/test_actions.py",
            "silver/scripts/test_scheduler.py",
            "silver/scripts/test_integration.py",
        ],
        "Configuration": [
            "silver/config/watcher_config.yaml",
            "silver/config/approval_rules.yaml",
            "silver/config/schedules/schedules.yaml",
            "silver/config/.env.example",
        ],
        "Documentation": [
            "silver/README.md",
            "silver/IMPLEMENTATION_PROGRESS.md",
            "silver/TROUBLESHOOTING.md",
            "silver/SESSION_SUMMARY.md",
        ],
        "Agent Skills": [
            ".claude/skills/create-plans.md",
            ".claude/skills/execute-actions.md",
            ".claude/skills/schedule-tasks.md",
        ],
    }

    all_found = True
    for category, files in expected_files.items():
        print(f"\n{category}:")
        found = 0
        for file in files:
            file_path = vault_path / file
            if file_path.exists():
                print_success(f"  {file}")
                found += 1
            else:
                print_error(f"  {file} - NOT FOUND")
                all_found = False
        print(f"  Found: {found}/{len(files)}")

    return all_found

def test_vault_folders():
    """Test that vault workspace folders exist."""
    print_header("Testing Vault Workspace Folders")

    vault_path = Path("/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault")

    required_folders = [
        "Needs_Action",
        "Pending_Approval",
        "Approved",
        "Rejected",
        "Plans",
        "Tasks",
        "In_Progress",
        "Done",
        "Failed",
        "Logs",
    ]

    all_exist = True
    for folder in required_folders:
        folder_path = vault_path / folder
        if folder_path.exists():
            print_success(f"{folder}/")
        else:
            print_warning(f"{folder}/ - NOT FOUND (will be created on first run)")
            all_exist = False

    return all_exist

def test_basic_initialization():
    """Test basic class initialization without external dependencies."""
    print_header("Testing Basic Class Initialization")

    sys.path.insert(0, "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault")

    tests = []

    # Test utility functions
    try:
        from silver.src.utils.logger import setup_logging, get_logger
        setup_logging(log_level="INFO", log_format="text")
        logger = get_logger("test")
        print_success("Logger initialization")
        tests.append(True)
    except Exception as e:
        print_error(f"Logger initialization: {e}")
        tests.append(False)

    # Test YAML parser
    try:
        from silver.src.utils.yaml_parser import parse_frontmatter, serialize_frontmatter
        test_content = """---
id: test_123
status: pending
---
# Test Content
This is a test."""
        frontmatter, body = parse_frontmatter(test_content)
        assert frontmatter['id'] == 'test_123'
        assert 'Test Content' in body
        print_success("YAML parser functionality")
        tests.append(True)
    except Exception as e:
        print_error(f"YAML parser: {e}")
        tests.append(False)

    # Test file utils
    try:
        from silver.src.utils.file_utils import ensure_directory_exists
        from pathlib import Path
        test_dir = Path("/tmp/silver_test")
        ensure_directory_exists(test_dir)
        assert test_dir.exists()
        test_dir.rmdir()
        print_success("File utilities functionality")
        tests.append(True)
    except Exception as e:
        print_error(f"File utilities: {e}")
        tests.append(False)

    return all(tests)

def main():
    """Run all tests."""
    print_header("Silver Tier Comprehensive Functionality Test")

    results = {
        "Python Syntax": test_python_syntax(),
        "Module Imports": test_imports(),
        "YAML Configs": test_yaml_configs(),
        "File Structure": test_file_structure(),
        "Vault Folders": test_vault_folders(),
        "Basic Initialization": test_basic_initialization(),
    }

    # Summary
    print_header("Test Summary")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = f"{Colors.GREEN}✅ PASSED{Colors.NC}" if result else f"{Colors.RED}❌ FAILED{Colors.NC}"
        print(f"{test_name}: {status}")

    print(f"\n{Colors.BLUE}Results: {passed}/{total} tests passed{Colors.NC}")

    if passed == total:
        print(f"\n{Colors.GREEN}🎉 All tests passed! Silver tier is ready for deployment.{Colors.NC}")
        return 0
    else:
        print(f"\n{Colors.YELLOW}⚠️  Some tests failed. Review errors above.{Colors.NC}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
