"""
Pytest configuration and fixtures for EncoreProAI tests
"""

import pytest
import asyncio
import os
import asyncpg
from typing import AsyncGenerator, Generator
import json
from datetime import datetime, timedelta

# No path manipulation needed - tests run from project root


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def database_url():
    """Database URL for testing"""
    return os.getenv("DATABASE_URL", "postgresql://encore:secure_password@localhost:5433/encoreproai")


@pytest.fixture
def cube_config():
    """Cube.js configuration - fails if environment variables not set"""
    cube_url = os.getenv("CUBE_URL")
    cube_secret = os.getenv("CUBE_SECRET")
    
    if not cube_url:
        pytest.fail("CUBE_URL environment variable is required")
    if not cube_secret:
        pytest.fail("CUBE_SECRET environment variable is required")
    
    return {
        "url": cube_url,
        "secret": cube_secret
    }


@pytest.fixture
def openai_api_key():
    """OpenAI API key for LLM tests - fails if not set"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.fail("OPENAI_API_KEY environment variable is required for LLM tests")
    return api_key


@pytest.fixture
def test_tenant_id():
    """Test tenant ID"""
    return "test_tenant"


@pytest.fixture
def real_tenant_id():
    """Real tenant ID from environment for Cube.js tests - fails if not set"""
    tenant_id = os.getenv("DEFAULT_TENANT_ID")
    if not tenant_id:
        pytest.fail("DEFAULT_TENANT_ID environment variable is required for Cube.js tests")
    return tenant_id


@pytest.fixture
async def test_db(database_url: str) -> AsyncGenerator[asyncpg.Connection, None]:
    """Create test database connection and clean up after tests"""
    conn = await asyncpg.connect(database_url)
    
    # Set up test data
    await conn.execute("DELETE FROM entities WHERE tenant_id = 'test_tenant'")
    
    yield conn
    
    # Clean up
    await conn.execute("DELETE FROM entities WHERE tenant_id = 'test_tenant'")
    await conn.close()


# Removed complex sample_entities fixture - tests should create their own data as needed


