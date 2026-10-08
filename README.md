# Bangla AI Python SDK (`bangla-ai-sdk`)

![Async](https://img.shields.io/badge/async-supported-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI version](https://img.shields.io/badge/pypi-0.1.1-orange.svg)](https://pypi.org/project/bangla-ai-sdk/)

Official Python SDK for the **Bangla AI Gateway**. Easily connect your Python applications to state-of-the-art Bengali language AI microservices:
- 💬 **Large Language Model (LLM)**: Multi-branch conversation trees and token-by-token SSE streaming.
- 📄 **Document OCR**: High-accuracy Bengali document parsing with layout detection, bounding boxes, and Markdown output.
- 🎙️ **Speech-to-Text (ASR)**: Nemotron Bengali ASR for offline audio files, YouTube transcription, and real-time streams.
- 🔊 **Speech Synthesis (TTS)**: Higgs TTS 3 (4B) neural voice synthesis returning 24 kHz WAV/PCM audio and zero-shot voice cloning.
- 🗣️ **Speech-to-Speech (STS)**: LiveKit SFU room token minting and custom voice clone references.

---

## 🚀 Features

- **✅ Sync & Async Clients**: Built on top of `httpx`, providing parallel `BanglaAI` and `AsyncBanglaAI` interfaces.
- **⚡ Real-Time Streaming**: First-class Server-Sent Events (SSE) streaming for LLM tokens and 24 kHz raw PCM audio chunks for TTS.
- **🛡️ Robust Error Handling**: Clean RFC 7807 typed exceptions (`RateLimitError`, `AuthenticationError`, `UpstreamServiceError`, etc.) with automatic retry on transient failures.
- **🔐 Flexible Authentication**: Auto-discovers credentials from `BANGLA_AI_API_KEY` environment variables or `.env` file via `python-dotenv`.
- **📦 PyPI Deploy Ready**: Out-of-the-box PEP 621 `pyproject.toml`, automated GitHub Actions workflow, and smoke verification suite.

---

## 📦 Installation

```bash
pip install bangla-ai-sdk
```

Or for local development / installation from source:

```bash
git clone https://github.com/jayeeed/bangla-ai-sdk-python.git
cd bangla-ai-sdk-python
pip install -e .
```

---

## ⚡ Quick Start

### 1. Configure Environment

Copy [.env.example](.env.example) to `.env` and set your API key:

```bash
cp .env.example .env
```

```env
BANGLA_AI_API_KEY="sk_live_your_gateway_api_key_here"
BANGLA_AI_BASE_URL="https://banglai.acimisai.com"
```

### 2. Run Code

#### Synchronous Example
```python
from dotenv import load_dotenv
from bangla_ai import BanglaAI

load_dotenv()

# Automatically reads BANGLA_AI_API_KEY from .env / environment
client = BanglaAI()

# 1. Check identity
me = client.me.get()
print(f"Logged in as: {me.display_name} ({me.email}) - Tier: {me.plan}")

# 2. Chat with the Bengali LLM
chat = client.chats.create(title="Introduction")
reply = client.chats.turns.create(chat.id, content="বাংলা ব্যাকরণ অনুযায়ী সমাস কাকে বলে?")
print("AI:", reply)
```

#### Asynchronous Example
```python
import asyncio
from dotenv import load_dotenv
from bangla_ai import AsyncBanglaAI

load_dotenv()

async def main():
    async with AsyncBanglaAI() as client:
        chat = await client.chats.create(title="Async Chat")
        
        print("Stream: ", end="", flush=True)
        async for chunk in client.chats.turns.stream(chat.id, content="কৃত্রিম বুদ্ধিমত্তা সম্পর্কে সংক্ষেপে বলুন।"):
            if chunk.text:
                print(chunk.text, end="", flush=True)
        print()

asyncio.run(main())
```

---

## 🧪 Smoke Testing

Run the included verification script to test your gateway connection and verify sync and async operations:

```bash
python test.py
```

---

## 📖 Complete Modality Guide

### 1. LLM & Conversational Chat

#### Token-by-Token Streaming (Server-Sent Events)
```python
chat = client.chats.create(
    title="Programming Tutorial",
    instructions="আপনি একজন অভিজ্ঞ পাইথন প্রোগ্রামার। প্রাতিষ্ঠানিক বাংলায় উত্তর দিন।"
)

# Stream tokens in real time
for chunk in client.chats.turns.stream(chat.id, content="পাইথনে ডেকোরেটর কী এবং এটি কীভাবে কাজ করে?"):
    if chunk.text:
        print(chunk.text, end="", flush=True)
print()
```

#### Uploading Chat Attachments (PDF / Images)
```python
# Upload document to MinIO
att = client.chats.attachments.upload(chat.id, "invoice.pdf")
print(f"Attached: {att.filename} ({att.size_bytes} bytes)")

# Submit message referencing the attachment
reply = client.chats.turns.create(
    chat.id,
    content="এই ইনভয়েসের মোট টাকার পরিমাণ কত?",
    attachment_ids=[att.id]
)
print("AI:", reply)
```

---

### 2. Document OCR

#### Synchronous Document OCR (Single-Page / Fast Scan)
```python
result = client.ocr.process("nid_card.jpg")
print("Extracted Markdown:\n", result.markdown)

# Inspect individual layout regions
for page in result.pages:
    for region in page.regions:
        print(f"[{region.label}] ({region.box_2d}): {region.text}")
```

#### Asynchronous Multi-Page Document OCR with Auto-Polling
```python
# Submits to Celery queue, polls until complete, and returns the result
job = client.ocr.wait_for_job("contract_30_pages.pdf", poll_interval=2.0)
print("Finished OCR in:", job.result.timing.total_elapsed_ms, "ms")
print(job.result.markdown)
```

---

### 3. Speech-to-Text (ASR)

#### Audio File Transcription (with Diarization)
```python
result = client.asr.transcribe("meeting_recording.wav", diarize=True)
print("Transcript:", result.text)
print(f"Duration: {result.duration_seconds}s | Processed in: {result.processing_time_ms}ms")
```

#### YouTube Video Audio Transcription
```python
yt_result = client.asr.transcribe_youtube(
    url="https://www.youtube.com/watch?v=example_video_id",
    diarize=True
)
print("Video Title:", yt_result.title)
print("Diarization:", yt_result.diarization_text)
```

#### Real-Time PCM16 Audio Stream
```python
# 1. Initialize streaming session
session = client.asr.create_stream(sample_rate=16000)

# 2. Stream 16kHz mono PCM chunks
chunk = client.asr.stream_chunk(
    session_id=session.session_id,
    pcm_bytes=pcm_buffer,
    chunk_sequence=1
)
print("Partial:", chunk.partial_text)

# 3. Finalize stream
client.asr.finish_stream(session.session_id)
```

---

### 4. Speech Synthesis (TTS)

#### Full WAV Audio Synthesis
```python
# Save speech directly to file
client.tts.synthesize_to_file(
    text="স্বাগতম! বাংলা এআই প্ল্যাটফর্মে আপনাকে স্বাগতম।",
    output_path="welcome.wav",
    voice="female"
)
```

#### Real-Time PCM Stream (24 kHz 16-bit Mono)
```python
# Stream PCM bytes directly for audio players
for pcm_chunk in client.tts.stream_pcm("বাংলা ভাষার জন্য উচ্চগতির কণ্ঠ রূপান্তর প্রযুক্তি।"):
    send_to_audio_hardware(pcm_chunk)
```

#### Zero-Shot Voice Cloning
```python
from bangla_ai.types import CustomReferenceAudio

# Clone a voice from reference audio base64
custom_ref = CustomReferenceAudio(
    audio_base64="UklGRiQAAABXQVZFZm10IBAAAA...",
    transcript="রেফারেন্স অডিওতে বলা বাক্য"
)

audio_bytes = client.tts.advanced(
    input="ক্লোন করা কণ্ঠস্বরে তৈরি বাক্য।",
    custom_reference=custom_ref
)
```

---

### 5. Speech-to-Speech (STS) & LiveKit WebRTC

```python
# 1. Upload a cloned voice sample
voice_ref = client.sts.upload_voice_reference("my_voice.wav")
print(f"Voice Reference ID: {voice_ref.reference_id}")

# 2. Mint LiveKit Room Token
room_access = client.sts.get_livekit_token(reference_id=voice_ref.reference_id)
print("LiveKit URL:", room_access.url)
print("Access Token:", room_access.token)
print("Allocated Room:", room_access.room)

# Pass `url` and `token` to any LiveKit Client SDK (JavaScript, iOS, Android, Python)
```

---

### 6. Managing Profile & Developer API Keys

```python
# Update display name
client.me.update(display_name="Rahim Ahmed")

# Provision a new API key
new_key = client.api_keys.create(
    name="Crawler-Key",
    scopes=["ocr", "asr"],
    expires_in_days=30
)
print("New Plaintext Key (save this now):", new_key.raw_api_key)

# List all keys
for key in client.api_keys.list():
    print(f"{key.id}: {key.name} [{key.key_prefix}...] - Active: {key.is_active}")

# Revoke a key
client.api_keys.delete(new_key.id)

# Mint single-use WebSocket ticket (valid for 30 seconds)
ticket = client.ws_tickets.create(target="asr_call")
print("WebSocket Ticket:", ticket.ticket)
```

---

## 🛡️ Error Handling

All API errors raise typed exceptions inheriting from `BanglaAIError`:

```python
from bangla_ai import BanglaAI
from bangla_ai.exceptions import (
    AuthenticationError,
    RateLimitError,
    NotFoundError,
    UpstreamServiceError,
    APIConnectionError,
)

client = BanglaAI(api_key="sk_live_invalid")

try:
    client.me.get()
except AuthenticationError:
    print("Invalid or expired API Key.")
except RateLimitError as e:
    print(f"Rate limited! Retry after {e.retry_after} seconds.")
except UpstreamServiceError:
    print("GPU microservice temporarily unavailable.")
except APIConnectionError:
    print("Network connectivity issue.")
```

---

## 🚀 Automated PyPI Deployment

This SDK includes a pre-configured GitHub Actions workflow in [`.github/workflows/pypi-publish.yml`](.github/workflows/pypi-publish.yml).

To publish automatically to PyPI:
1. Add your PyPI API token to your repository secrets as `PYPI_API_TOKEN` under **Settings > Secrets and variables > Actions**.
2. Bump the `version` field in `pyproject.toml` and `bangla_ai/_version.py`.
3. Push to `main`:
   ```bash
   git add .
   git commit -m "release: v0.1.1"
   git push origin main
   ```
4. GitHub Actions will build and publish the wheel and source distribution directly to PyPI.

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
