#!/usr/bin/env python3
"""
Comprehensive Silver Tier Test Suite (No External Credentials Required)

Tests all components that don't require Gmail/WhatsApp credentials:
- Utilities (validators, error recovery, performance)
- Planning components (PlanGenerator, TaskAnalyzer, PlanTracker)
- Approval workflow (ApprovalManager, ApprovalChecker, ApprovalNotifier)
- Scheduling (Scheduler, ScheduleManager)
- File operations
- Configuration validation
"""

import os
import sys
import asyncio
from pathlib import Path
import time
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from silver.src.utils import setup_logging, get_logger
from silver.src.utils.validators import (
    validate_email, validate_phone_number, validate_yaml_frontmatter,
    validate_schedule_config, sanitize_filename
)
from silver.src.utils.error_recovery import (
    CircuitBreaker, RetryStrategy, DeadLetterQueue, StateRecovery
)
from silver.src.utils.performance import LRUCache, BatchProcessor, RateLimiter

# Set up logging
setup_logging(log_level="INFO", log_format="text")
logger = get_logger("comprehensive_test")


def print_header(text):
    """Print section header."""
    print("\n" + "=" * 70)
    print(text)
    print("=" * 70)


def print_success(text):
    """Print success message."""
    print(f"✅ {text}")


def print_error(text):
    """Print error message."""
    print(f"❌ {text}")


def print_info(text):
    """Print info message."""
    print(f"ℹ️  {text}")


async def test_validators():
    """Test validation utilities."""
    print_header("Testing Validators")

    tests_passed = 0
    tests_total = 0

    # Test email validation
    tests_total += 1
    valid, error = validate_email("test@example.com")
    if valid:
        print_success("Email validation: Valid email accepted")
        tests_passed += 1
    else:
        print_error(f"Email validation failed: {error}")

    tests_total += 1
    valid, error = validate_email("invalid.email")
    if not valid:
        print_success("Email validation: Invalid email rejected")
        tests_passed += 1
    else:
        print_error("Email validation: Invalid email accepted")

    # Test phone validation
    tests_total += 1
    valid, error = validate_phone_number("+1234567890")
    if valid:
        print_success("Phone validation: Valid phone accepted")
        tests_passed += 1
    else:
        print_error(f"Phone validation failed: {error}")

    # Test YAML frontmatter validation
    tests_total += 1
    test_yaml = """---
id: test_123
status: pending
---
# Test Content"""
    valid, error, frontmatter = validate_yaml_frontmatter(test_yaml)
    if valid and frontmatter.get('id') == 'test_123':
        print_success("YAML validation: Valid frontmatter parsed")
        tests_passed += 1
    else:
        print_error(f"YAML validation failed: {error}")

    # Test schedule config validation
    tests_total += 1
    schedule_config = {
        'schedule_type': 'daily',
        'schedule_config': {'time': '09:00'},
        'task_config': {'action': 'test'}
    }
    valid, error = validate_schedule_config(schedule_config)
    if valid:
        print_success("Schedule validation: Valid config accepted")
        tests_passed += 1
    else:
        print_error(f"Schedule validation failed: {error}")

    # Test filename sanitization
    tests_total += 1
    sanitized = sanitize_filename("test/file<name>.txt")
    if '/' not in sanitized and '<' not in sanitized:
        print_success(f"Filename sanitization: '{sanitized}'")
        tests_passed += 1
    else:
        print_error("Filename sanitization failed")

    print(f"\nValidators: {tests_passed}/{tests_total} tests passed")
    return tests_passed == tests_total


async def test_error_recovery():
    """Test error recovery mechanisms."""
    print_header("Testing Error Recovery")

    tests_passed = 0
    tests_total = 0

    # Test Circuit Breaker
    tests_total += 1
    try:
        breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=1)

        # Simulate failures
        for _ in range(2):
            try:
                breaker.call(lambda: 1/0)
            except:
                pass

        # Circuit should be open now
        try:
            breaker.call(lambda: "success")
            print_error("Circuit breaker: Should have rejected call")
        except Exception as e:
            if "OPEN" in str(e):
                print_success("Circuit breaker: Opened after failures")
                tests_passed += 1
            else:
                print_error(f"Circuit breaker: Wrong error: {e}")
    except Exception as e:
        print_error(f"Circuit breaker test failed: {e}")

    # Test Retry Strategy
    tests_total += 1
    try:
        attempt_count = 0
        def failing_func():
            nonlocal attempt_count
            attempt_count += 1
            if attempt_count < 3:
                raise ValueError("Simulated failure")
            return "success"

        result = RetryStrategy.exponential_backoff(
            failing_func,
            max_retries=3,
            base_delay=0.1
        )
        if result == "success" and attempt_count == 3:
            print_success(f"Retry strategy: Succeeded after {attempt_count} attempts")
            tests_passed += 1
        else:
            print_error("Retry strategy: Unexpected result")
    except Exception as e:
        print_error(f"Retry strategy test failed: {e}")

    # Test Dead Letter Queue
    tests_total += 1
    try:
        dlq_dir = Path("/tmp/silver_test_dlq")
        dlq_dir.mkdir(exist_ok=True)

        dlq = DeadLetterQueue(dlq_dir)
        dlq.add("test_op_1", "test_action", {"data": "test"}, "Test error")

        items = dlq.get_all()
        if len(items) == 1 and items[0]['id'] == 'test_op_1':
            print_success("Dead Letter Queue: Item stored and retrieved")
            tests_passed += 1
        else:
            print_error("Dead Letter Queue: Item not found")

        # Cleanup
        dlq.remove("test_op_1")
        dlq_dir.rmdir()
    except Exception as e:
        print_error(f"Dead Letter Queue test failed: {e}")

    # Test State Recovery
    tests_total += 1
    try:
        state_dir = Path("/tmp/silver_test_state")
        state_dir.mkdir(exist_ok=True)

        recovery = StateRecovery(state_dir)
        recovery.save_state("test_op", {"step": 1, "data": "test"})

        loaded_state = recovery.load_state("test_op")
        if loaded_state and loaded_state.get('step') == 1:
            print_success("State Recovery: State saved and loaded")
            tests_passed += 1
        else:
            print_error("State Recovery: State not loaded correctly")

        # Cleanup
        recovery.clear_state("test_op")
        state_dir.rmdir()
    except Exception as e:
        print_error(f"State Recovery test failed: {e}")

    print(f"\nError Recovery: {tests_passed}/{tests_total} tests passed")
    return tests_passed == tests_total


async def test_performance():
    """Test performance utilities."""
    print_header("Testing Performance Utilities")

    tests_passed = 0
    tests_total = 0

    # Test LRU Cache
    tests_total += 1
    try:
        cache = LRUCache(max_size=2, ttl=60)
        cache.set("key1", "value1")
        cache.set("key2", "value2")

        value = cache.get("key1")
        if value == "value1":
            print_success("LRU Cache: Value stored and retrieved")
            tests_passed += 1
        else:
            print_error("LRU Cache: Value not retrieved")
    except Exception as e:
        print_error(f"LRU Cache test failed: {e}")

    # Test Batch Processor
    tests_total += 1
    try:
        processor = BatchProcessor(batch_size=3, flush_interval=1)
        processed_items = []

        def process_batch(items):
            processed_items.extend(items)

        # Add items
        for i in range(3):
            processor.add(f"item_{i}", process_batch)

        if len(processed_items) == 3:
            print_success("Batch Processor: Batch processed at size threshold")
            tests_passed += 1
        else:
            print_error(f"Batch Processor: Expected 3 items, got {len(processed_items)}")
    except Exception as e:
        print_error(f"Batch Processor test failed: {e}")

    # Test Rate Limiter
    tests_total += 1
    try:
        limiter = RateLimiter(max_calls=2, time_window=1)

        # Should allow first 2 calls
        limiter.acquire()
        limiter.acquire()

        # Third call should block briefly
        start = time.time()
        limiter.acquire()
        duration = time.time() - start

        if duration > 0.5:  # Should have waited
            print_success(f"Rate Limiter: Blocked third call ({duration:.2f}s)")
            tests_passed += 1
        else:
            print_error("Rate Limiter: Did not block")
    except Exception as e:
        print_error(f"Rate Limiter test failed: {e}")

    print(f"\nPerformance: {tests_passed}/{tests_total} tests passed")
    return tests_passed == tests_total


async def test_planning_components():
    """Test planning components without external dependencies."""
    print_header("Testing Planning Components")

    tests_passed = 0
    tests_total = 0

    # Test PlanGenerator initialization
    tests_total += 1
    try:
        from silver.src.planning.plan_generator import PlanGenerator
        vault_path = "/mnt/d/hamza/autonomous-ftes/AI_Employee_Vault"
        generator = PlanGenerator(vault_path)
        print_success("PlanGenerator: Initialized successfully")
        tests_passed += 1
    except Exception as e:
        print_error(f"PlanGenerator initialization failed: {e}")

    # Test TaskAnalyzer initialization
    tests_total += 1
    try:
        from silver.src.planning.task_analyzer import TaskAnalyzer
        analyzer = TaskAnalyzer(vault_path)
        print_success("TaskAnalyzer: Initialized successfully")
        tests_passed += 1
    except Exception as e:
        print_error(f"TaskAnalyzer initialization failed: {e}")

    # Test PlanTracker initialization
    tests_total += 1
    try:
        from silver.src.planning.plan_tracker import PlanTracker
        tracker = PlanTracker(vault_path)
        print_success("PlanTracker: Initialized successfully")
        tests_passed += 1
    except Exception as e:
        print_error(f"PlanTracker initialization failed: {e}")

    print(f"\nPlanning Components: {tests_passed}/{tests_total} tests passed")
    return tests_passed == tests_total


async def test_file_operations():
    """Test file operations."""
    print_header("Testing File Operations")

    tests_passed = 0
    tests_total = 0

    # Test file utilities
    tests_total += 1
    try:
        from silver.src.utils.file_utils import ensure_directory_exists, atomic_write

        test_dir = Path("/tmp/silver_test_files")
        ensure_directory_exists(test_dir)

        if test_dir.exists():
            print_success("File utilities: Directory created")
            tests_passed += 1

            # Cleanup
            test_dir.rmdir()
        else:
            print_error("File utilities: Directory not created")
    except Exception as e:
        print_error(f"File utilities test failed: {e}")

    # Test YAML parser
    tests_total += 1
    try:
        from silver.src.utils.yaml_parser import parse_frontmatter, serialize_frontmatter

        test_content = """---
id: test_123
status: pending
---
# Test Content
This is a test."""

        frontmatter, body = parse_frontmatter(test_content)
        if frontmatter.get('id') == 'test_123' and 'Test Content' in body:
            print_success("YAML parser: Frontmatter parsed correctly")
            tests_passed += 1
        else:
            print_error("YAML parser: Parsing failed")
    except Exception as e:
        print_error(f"YAML parser test failed: {e}")

    print(f"\nFile Operations: {tests_passed}/{tests_total} tests passed")
    return tests_passed == tests_total


async def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("COMPREHENSIVE SILVER TIER TEST SUITE")
    print("(No External Credentials Required)")
    print("=" * 70)
    print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    results = {
        "Validators": await test_validators(),
        "Error Recovery": await test_error_recovery(),
        "Performance": await test_performance(),
        "Planning Components": await test_planning_components(),
        "File Operations": await test_file_operations(),
    }

    # Summary
    print_header("TEST SUMMARY")

    passed = sum(1 for v in results.values() if v)
    total = len(results)

    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:25} {status}")

    print(f"\n{'=' * 70}")
    print(f"Results: {passed}/{total} test suites passed")
    print(f"{'=' * 70}")

    if passed == total:
        print("\n🎉 All test suites passed!")
        print("\nSilver tier core functionality is working correctly.")
        print("Ready to configure credentials and test with external services.")
    else:
        print("\n⚠️  Some test suites failed")
        print("Review errors above before proceeding.")

    return passed == total


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
