"""
Example 3: Speech Recognition (Offline Audio & YouTube)
"""
import os
from bangla_ai import BanglaAI

client = BanglaAI(
    api_key=os.getenv("BANGLA_AI_API_KEY", "sk_live_test_key"),
    base_url=os.getenv("BANGLA_AI_BASE_URL", "https://banglai.acimisai.com"),
)

def main():
    print("--- 1. Transcribe YouTube Audio ---")
    try:
        yt_res = client.asr.transcribe_youtube(
            url="https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            include_audio=False,
            diarize=True
        )
        print("Title:", yt_res.title)
        print("Transcript:", yt_res.text)
    except Exception as e:
        print("YouTube transcription error:", e)

    print("\n--- 2. Live PCM16 Streaming Session ---")
    try:
        session = client.asr.create_stream(sample_rate=16000)
        print("Stream session opened:", session.session_id)

        # Simulate 16000 Hz silence chunk
        silence_chunk = b"\x00" * 3200
        chunk_res = client.asr.stream_chunk(session.session_id, silence_chunk, chunk_sequence=1)
        print("Partial transcript received:", chunk_res.transcript)

        finish_res = client.asr.finish_stream(session.session_id)
        print("Stream session closed:", finish_res)
    except Exception as e:
        print("Streaming error:", e)

if __name__ == "__main__":
    main()
