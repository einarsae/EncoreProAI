#!/usr/bin/env python3
"""
Test environment variables

Run: docker-compose run --rm test python test_env.py
"""

import os

print("🔍 Environment Variables Check")
print("=" * 60)

env_vars = [
    "CUBE_URL",
    "CUBE_SECRET",
    "CUBE_API_URL",
    "CUBE_API_SECRET",
    "DATABASE_URL",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "TENANT_ID"
]

for var in env_vars:
    value = os.getenv(var)
    if value:
        if "KEY" in var or "SECRET" in var or "PASSWORD" in var:
            # Mask sensitive values
            print(f"✅ {var}: {'*' * 10}{value[-4:]}")
        else:
            print(f"✅ {var}: {value}")
    else:
        print(f"❌ {var}: NOT SET")

print("\n" + "=" * 60)
print("Note: CUBE_URL and CUBE_SECRET should be set in the container")
print("They are mapped from CUBE_API_URL and CUBE_API_SECRET in .env")