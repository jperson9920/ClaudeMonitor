#!/usr/bin/env python3
"""
Syntax validation and structure test for claude_scraper.py
Does not require dependencies to be installed
"""

import ast
import sys


def validate_python_syntax(filename):
    """Validate Python syntax"""
    try:
        with open(filename, 'r') as f:
            source = f.read()
        ast.parse(source)
        return True, "Syntax valid"
    except SyntaxError as e:
        return False, f"Syntax error: {e}"


def check_required_methods(filename):
    """Check that all required methods exist"""
    with open(filename, 'r') as f:
        source = f.read()

    required_methods = [
        'create_driver',
        'manual_login',
        'save_session',
        'load_session',
        'check_session_valid',
        'navigate_to_usage_page',
        'extract_usage_data',
        '_parse_extracted_data',
        '_parse_plain_text',
        'poll_usage',
        'close',
        'main'
    ]

    missing = []
    for method in required_methods:
        if f'def {method}(' not in source:
            missing.append(method)

    if missing:
        return False, f"Missing methods: {', '.join(missing)}"
    return True, f"All {len(required_methods)} required methods found"


def main():
    """Run validation tests"""
    filename = 'claude_scraper.py'

    print("="*70)
    print("Claude Scraper Validation Tests")
    print("="*70)

    tests = [
        ("Python Syntax", lambda: validate_python_syntax(filename)),
        ("Required Methods", lambda: check_required_methods(filename)),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n{test_name}...", end=' ')
        try:
            success, message = test_func()
            if success:
                print(f"✓ PASS")
                print(f"  {message}")
                passed += 1
            else:
                print(f"✗ FAIL")
                print(f"  {message}")
                failed += 1
        except Exception as e:
            print(f"✗ ERROR")
            print(f"  {e}")
            failed += 1

    print("\n" + "="*70)
    print(f"Results: {passed} passed, {failed} failed")
    print("="*70)

    return 0 if failed == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
