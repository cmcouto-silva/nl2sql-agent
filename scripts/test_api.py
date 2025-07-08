#!/usr/bin/env python3
"""Simple API testing script for the NL2SQL API."""

import asyncio
import json

import httpx


async def test_health() -> None:
    """Test the health endpoint."""
    print("🔍 Testing Health Endpoint...")
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/health")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print()


async def test_root() -> None:
    """Test the root endpoint."""
    print("🔍 Testing Root Endpoint...")
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:8000/")
        print(f"Status: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        print()


async def test_chat() -> None:
    """Test the chat endpoint."""
    print("🔍 Testing Chat Endpoint...")
    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(
            "http://localhost:8000/chat/",
            json={"message": "Hello! How are you?", "session_id": "test_123"},
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Message: {data['message']}")
            print(f"Session ID: {data['session_id']}")
            print(f"Metadata: {json.dumps(data.get('metadata', {}), indent=2)}")
        else:
            print(f"Error: {response.text}")
        print()


async def test_chat_sql() -> None:
    """Test the chat endpoint with SQL query."""
    print("🔍 Testing Chat Endpoint with SQL Query...")
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            "http://localhost:8000/chat/",
            json={
                "message": "Show me the first 5 customers",
                "session_id": "test_sql_123",
            },
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Message: {data['message'][:200]}...")
            print(f"Session ID: {data['session_id']}")
            print(f"Metadata: {json.dumps(data.get('metadata', {}), indent=2)}")
        else:
            print(f"Error: {response.text}")
        print()


async def main() -> None:
    """Run all tests."""
    print("🧪 NL2SQL API Test Suite")
    print("=" * 50)

    try:
        await test_health()
        await test_root()
        await test_chat()
        await test_chat_sql()
        print("✅ All tests completed!")
    except Exception as e:
        print(f"❌ Test failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
