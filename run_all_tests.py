#!/usr/bin/env python3
"""
Master test runner for EncoreProAI

Run all tests: docker-compose run --rm test python run_all_tests.py
Run unit tests: docker-compose run --rm test python run_all_tests.py unit
Run integration tests: docker-compose run --rm test python run_all_tests.py integration
"""

import subprocess
import sys
import os


def check_environment():
    """Check required environment variables"""
    required_vars = ['CUBE_URL', 'CUBE_SECRET', 'OPENAI_API_KEY']
    missing = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    
    if missing:
        print(f"⚠️  Missing environment variables: {', '.join(missing)}")
        print("   Some tests will be skipped")
    else:
        print("✅ All environment variables set")
    
    return len(missing) == 0


def run_tests(marker=None):
    """Run pytest with optional marker"""
    cmd = ['python', '-m', 'pytest', 'tests/', '-v']
    
    if marker:
        cmd.extend(['-m', marker])
    
    print(f"🧪 Running: {' '.join(cmd)}")
    print("=" * 60)
    
    result = subprocess.run(cmd)
    
    return result.returncode == 0


def main():
    """Main test runner"""
    print("🚀 EncoreProAI Test Suite")
    print("=" * 60)
    
    # Check environment
    env_ok = check_environment()
    
    # Determine which tests to run
    if len(sys.argv) > 1:
        marker = sys.argv[1]
        if marker not in ['unit', 'integration']:
            print(f"❌ Invalid marker: {marker}")
            print("   Use 'unit', 'integration', or no argument for all tests")
            sys.exit(1)
    else:
        marker = None
    
    # Run tests
    success = run_tests(marker)
    
    if success:
        print("\n✅ All tests passed!")
    else:
        print("\n❌ Some tests failed")
        sys.exit(1)


if __name__ == "__main__":
    main()