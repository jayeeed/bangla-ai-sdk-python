"""
Example 6: Asynchronous Operations with AsyncBanglaAI
"""
import asyncio
import os
from bangla_ai import AsyncBanglaAI

async def main():
    async with AsyncBanglaAI(
        api_key=os.getenv("BANGLA_AI_API_KEY", "sk_live_test_key"),
        base_url=os.getenv("BANGLA_AI_BASE_URL", "https://banglai.acimisai.com"),
    ) as client:
        print("--- 1. Async Health Probes ---")
        try:
            health = await client.health()
            print("Gateway Liveness:", health)
        except Exception as e:
            print("Health check failed:", e)

        print("\n--- 2. Async Chat Creation & Streaming ---")
        try:
            chat = await client.chats.create(title="Async Chat Demo")
            print("Chat created:", chat.id)

            print("Streaming tokens: ", end="", flush=True)
            async for chunk in client.chats.turns.stream(chat.id, content="নমস্কার"):
                if chunk.text:
                    print(chunk.text, end="", flush=True)
            print()
        except Exception as e:
            print("Chat streaming error:", e)

if __name__ == "__main__":
    asyncio.run(main())
