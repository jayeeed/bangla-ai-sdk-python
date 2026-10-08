import asyncio
import os
import sys

# Load variables from local .env file if python-dotenv is installed
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Ensure local bangla_ai package is imported if running from source repo
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from bangla_ai import AsyncBanglaAI, BanglaAI
from bangla_ai.exceptions import APIConnectionError, AuthenticationError, BanglaAIError


def mask_key(key: str) -> str:
    if not key:
        return "<not set>"
    if len(key) <= 8:
        return "***"
    return f"{key[:6]}...{key[-4:]}"


def test_sync(api_key: str, base_url: str):
    print("\n" + "=" * 60)
    print("🚀 1. Testing Synchronous Client (BanglaAI)")
    print("=" * 60)

    client = BanglaAI(api_key=api_key or None, base_url=base_url)

    # 1.1 Gateway Liveness & Health
    print("\n--- 1.1 Checking Gateway Health (/healthz & /readyz) ---")
    try:
        health = client.health()
        print(f"✅ Health status: {health}")
        ready = client.ready()
        print(f"✅ Ready status:  {ready}")
    except APIConnectionError as e:
        print(f"❌ Connection failed: Gateway at {base_url} is unreachable ({e}).")
        return
    except Exception as e:
        print(f"⚠️ Health check notice: {type(e).__name__}: {e}")

    if not api_key:
        print("\n⚠️ Skipping authenticated endpoints (BANGLA_AI_API_KEY is not set).")
        print("💡 Tip: Copy .env.example to .env and configure BANGLA_AI_API_KEY to test all features.")
        return

    # 1.2 User Profile
    print("\n--- 1.2 Fetching User Identity (client.me.get) ---")
    try:
        me = client.me.get()
        print(f"✅ Authenticated as: {me.display_name} ({me.email}) | Plan: {me.plan}")
    except AuthenticationError as e:
        print(f"⚠️ Authentication Notice: {e}")
        print("💡 Configure a valid BANGLA_AI_API_KEY in .env to test authenticated routes.")
        return
    except Exception as e:
        print(f"⚠️ Me check notice: {type(e).__name__}: {e}")
        return

    # 1.3 Chat Conversation & Standard Turn
    print("\n--- 1.3 LLM Chat Conversation (Create & Turn) ---")
    try:
        chat = client.chats.create(title="SDK Smoke Test", instructions="বাংলা ব্যাকরণ ও সাধারণ জ্ঞানের উত্তর দিন।")
        print(f"✅ Chat session created: id={chat.id}")

        turn = client.chats.turns.create(chat.id, content="বাংলাদেশের জাতীয় কবি কে?")
        print(f"✅ Response received: {turn.content}")
    except Exception as e:
        print(f"⚠️ Chat turn notice: {type(e).__name__}: {e}")

    # 1.4 Streaming Turn (SSE)
    print("\n--- 1.4 LLM Real-Time Streaming Turn ---")
    try:
        print("Stream output: ", end="", flush=True)
        token_count = 0
        for chunk in client.chats.turns.stream(chat.id, content="এক বাক্যে কৃত্রিম বুদ্ধিমত্তা কী ব্যাখ্যা করুন।"):
            if chunk.text:
                print(chunk.text, end="", flush=True)
                token_count += 1
        print(f"\n✅ Streaming finished successfully ({token_count} chunks received).")
    except Exception as e:
        print(f"\n⚠️ Chat stream notice: {type(e).__name__}: {e}")

    # 1.5 STS LiveKit Token Minting
    print("\n--- 1.5 Speech-to-Speech (STS LiveKit Token) ---")
    try:
        sts_token = client.sts.create_token(room_name="smoke-test-room", participant_name="tester")
        print(f"✅ LiveKit Token generated: room={sts_token.room_name}, url={sts_token.livekit_url}")
    except Exception as e:
        print(f"⚠️ STS token notice: {type(e).__name__}: {e}")

    # 1.6 TTS Voice Discovery
    print("\n--- 1.6 TTS Voice Discovery ---")
    try:
        voices = client.tts.list_voices()
        speakers = voices.get("speakers") or voices.get("voices") or []
        print(f"✅ TTS Voices available: {len(speakers)} voices found.")
    except Exception as e:
        print(f"⚠️ TTS discovery notice: {type(e).__name__}: {e}")


async def test_async(api_key: str, base_url: str):
    print("\n" + "=" * 60)
    print("⚡ 2. Testing Asynchronous Client (AsyncBanglaAI)")
    print("=" * 60)

    async with AsyncBanglaAI(api_key=api_key or None, base_url=base_url) as client:
        # 2.1 Async Health
        print("\n--- 2.1 Async Gateway Health ---")
        try:
            health = await client.health()
            print(f"✅ Async Health: {health}")
        except Exception as e:
            print(f"⚠️ Async Health notice: {type(e).__name__}: {e}")

        if not api_key:
            return

        # 2.2 Verify auth before authenticated async operations
        try:
            await client.me.get()
        except AuthenticationError:
            print("\n⚠️ Skipping async authenticated endpoints (Invalid API key).")
            return
        except Exception as e:
            print(f"⚠️ Async Auth notice: {type(e).__name__}: {e}")
            return

        # 2.3 Async Chat & Streaming
        print("\n--- 2.3 Async Chat Streaming ---")
        try:
            chat = await client.chats.create(title="Async Smoke Test")
            print(f"✅ Async Chat created: id={chat.id}")

            print("Async stream: ", end="", flush=True)
            async for chunk in client.chats.turns.stream(chat.id, content="আজকের আবহাওয়া কেমন হতে পারে সংক্ষেপে বলুন।"):
                if chunk.text:
                    print(chunk.text, end="", flush=True)
            print("\n✅ Async streaming completed.")
        except Exception as e:
            print(f"\n⚠️ Async chat notice: {type(e).__name__}: {e}")

        # 2.4 Async STS Token
        print("\n--- 2.4 Async STS Token Minting ---")
        try:
            token = await client.sts.create_token(room_name="async-room", participant_name="async-user")
            print(f"✅ Async LiveKit Token: room={token.room_name}")
        except Exception as e:
            print(f"⚠️ Async STS notice: {type(e).__name__}: {e}")


def main():
    api_key = os.getenv("BANGLA_AI_API_KEY", "").strip()
    base_url = os.getenv("BANGLA_AI_BASE_URL", "https://banglai.acimisai.com").strip()

    print("╔════════════════════════════════════════════════════════════╗")
    print("║          Bangla AI Python SDK - Verification Suite         ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"Target Gateway URL: {base_url}")
    print(f"Configured API Key: {mask_key(api_key)}")

    # Run Sync Suite
    test_sync(api_key, base_url)

    # Run Async Suite
    asyncio.run(test_async(api_key, base_url))

    print("\n" + "=" * 60)
    print("🎉 Verification run complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
