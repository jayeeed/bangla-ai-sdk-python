"""
Example 4: Speech Synthesis (WAV Generation & PCM Streaming)
"""
import os
from bangla_ai import BanglaAI

client = BanglaAI(
    api_key=os.getenv("BANGLA_AI_API_KEY", "sk_live_test_key"),
    base_url=os.getenv("BANGLA_AI_BASE_URL", "https://banglai.acimisai.com"),
)

def main():
    print("--- 1. Discover Models & Voices ---")
    try:
        models = client.tts.models()
        print("Available voices:", models.voices)
        print("Default voice:", models.default_voice)
    except Exception as e:
        print("Model discovery error:", e)

    print("\n--- 2. Synthesize to WAV File ---")
    text = "বাংলা এআই গেটওয়েতে আপনাকে স্বাগতম।"
    output_wav = "output_speech.wav"
    try:
        client.tts.synthesize_to_file(text, output_wav, voice="female")
        print(f"Generated speech saved to: {output_wav}")
        if os.path.exists(output_wav):
            os.remove(output_wav)
    except Exception as e:
        print("TTS error:", e)

    print("\n--- 3. Stream 24 kHz Signed 16-bit PCM Audio ---")
    try:
        total_bytes = 0
        for chunk in client.tts.stream_pcm(text, voice="male"):
            total_bytes += len(chunk)
        print(f"Received total streamed PCM audio: {total_bytes} bytes")
    except Exception as e:
        print("Streaming TTS error:", e)

if __name__ == "__main__":
    main()
