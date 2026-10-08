"""
Example 1: LLM Chat, Token-by-Token Streaming, and Attachments
"""
import os
from bangla_ai import BanglaAI

# Initialize client using environment variable BANGLA_AI_API_KEY
client = BanglaAI(
    api_key=os.getenv("BANGLA_AI_API_KEY", "sk_live_test_key"),
    base_url=os.getenv("BANGLA_AI_BASE_URL", "https://banglai.acimisai.com"),
)

def main():
    print("--- 1. Creating Chat Session ---")
    chat = client.chats.create(
        title="Python Data Science Q&A",
        instructions="আপনি একজন অভিজ্ঞ ডেটা বিজ্ঞানী। উত্তর সহজ বাংলায় বুঝিয়ে বলুন।"
    )
    print(f"Chat created: ID = {chat.id}, Title = {chat.title}")

    print("\n--- 2. Streaming Conversation Turn ---")
    prompt = "পান্ডাস (Pandas) লাইব্রেরির মূল কাজ কী?"
    print(f"User: {prompt}\nAssistant: ", end="", flush=True)
    
    for chunk in client.chats.turns.stream(chat.id, content=prompt):
        if chunk.text:
            print(chunk.text, end="", flush=True)
    print("\n")

    print("--- 3. Listing Messages in Thread ---")
    messages = client.chats.messages(chat.id)
    for msg in messages:
        print(f"Turn [{msg.id[:10]}...] {msg.input_content[:20]} -> {msg.output_text[:30]}...")

if __name__ == "__main__":
    main()
