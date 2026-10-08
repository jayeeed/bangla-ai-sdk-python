"""
Example 5: Real-Time Speech-to-Speech (STS) & LiveKit Room Tokens
"""
import os
from bangla_ai import BanglaAI

client = BanglaAI(
    api_key=os.getenv("BANGLA_AI_API_KEY", "sk_live_test_key"),
    base_url=os.getenv("BANGLA_AI_BASE_URL", "https://banglai.acimisai.com"),
)

def main():
    print("--- 1. Mint LiveKit Room Token ---")
    try:
        # Request room access for conversational mode
        token_info = client.sts.get_livekit_token(
            voice="female",
            mode="conversational"
        )
        print("LiveKit Signaling URL:", token_info.url)
        print("Allocated Room:", token_info.room)
        print("Access Token (JWT):", token_info.token[:30] + "...")
        print("\nPass this URL and Token to livekit-client in React / Flutter / Python to start the call!")
    except Exception as e:
        print("STS error:", e)

if __name__ == "__main__":
    main()
