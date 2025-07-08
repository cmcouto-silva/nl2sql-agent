#!/usr/bin/env python3
"""Simple terminal chat interface for testing the NL2SQL API."""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

import httpx
from loguru import logger

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class TerminalChatClient:
    """Simple terminal chat client for testing the NL2SQL API."""

    def __init__(self, base_url: str = "http://localhost:8000") -> None:
        """Initialize the chat client."""
        self.base_url = base_url
        self.session_id = f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    async def check_health(self) -> bool:
        """Check if the API is healthy."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.base_url}/health")
                if response.status_code == 200:
                    health_data = response.json()
                    print(f"🔄 API Health: {health_data['status']}")
                    print(
                        f"🔄 Database: {'✅ Connected' if health_data['database_connected'] else '❌ Disconnected'}"  # noqa: E501
                    )
                    return health_data["database_connected"]
                else:
                    print(f"❌ API health check failed: {response.status_code}")
                    return False
        except Exception as e:
            print(f"❌ Failed to connect to API: {e}")
            return False

    async def send_message(self, message: str) -> str:
        """Send a message to the chat API."""
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.base_url}/chat/",
                    json={"message": message, "session_id": self.session_id},
                )

                if response.status_code == 200:
                    response_data = response.json()
                    return response_data["message"]
                else:
                    return f"❌ API Error: {response.status_code} - {response.text}"

        except Exception as e:
            return f"❌ Connection Error: {e}"

    async def run_chat_loop(self) -> None:
        """Run the interactive chat loop."""
        print("🤖 NL2SQL Terminal Chat Interface")
        print("=" * 50)
        print(f"Session ID: {self.session_id}")
        print("Type 'quit', 'exit', or 'bye' to end the session")
        print("=" * 50)

        # Check API health first
        if not await self.check_health():
            print("❌ API is not healthy. Please start the API server first.")
            print("Run: python -m nl2sql.api.main")
            return

        print("\n💬 Chat started! Ask me anything about your database.\n")

        while True:
            try:
                # Get user input
                user_input = input("You: ").strip()

                # Check for exit commands
                if user_input.lower() in ["quit", "exit", "bye", "q"]:
                    print("\n👋 Goodbye!")
                    break

                if not user_input:
                    continue

                # Send message and get response
                print("🤖 Thinking...")
                response = await self.send_message(user_input)
                print(f"Bot: {response}\n")

            except KeyboardInterrupt:
                print("\n\n👋 Chat interrupted. Goodbye!")
                break
            except Exception as e:
                print(f"❌ Unexpected error: {e}")
                break


async def main() -> None:
    """Main function to run the terminal chat."""
    # Configure logging
    logger.remove()  # Remove default handler
    logger.add(
        sys.stderr,
        level="INFO",
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level}</level> | {message}"
        ),
    )

    # Create and run chat client
    client = TerminalChatClient()
    await client.run_chat_loop()


if __name__ == "__main__":
    asyncio.run(main())
