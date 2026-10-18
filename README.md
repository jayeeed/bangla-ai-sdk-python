# Bangla AI Python SDK (`bangla-ai-sdk`)

![Async](https://img.shields.io/badge/async-supported-blue)
![Python](https://img.shields.io/badge/python-3.9+-green)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![PyPI version](https://img.shields.io/badge/pypi-0.2.1-orange.svg)](https://pypi.org/project/bangla-ai-sdk/)

Official Python SDK for the **Bangla AI Gateway**. Easily connect your Python applications to state-of-the-art Bengali language AI microservices:
- 💬 **Large Language Model (LLM)**: Multi-branch conversation trees, message turn history, automatic idempotency keys, and token-by-token SSE streaming.
- 📄 **Document OCR**: High-accuracy Bengali document parsing with layout detection, bounding boxes, synchronous processing, and asynchronous batch jobs.
- 🎙️ **Speech-to-Text (ASR)**: Nemotron Bengali ASR for offline audio files, asynchronous batch jobs, YouTube transcription, and live 16 kHz PCM16 streaming.
- 🔊 **Speech Synthesis (TTS)**: Higgs TTS 3 (4B) neural voice synthesis returning 24 kHz WAV/PCM audio, asynchronous jobs, zero-shot voice cloning, and stateful incremental text sessions.
- 🗣️ **Speech-to-Speech (STS)**: LiveKit SFU WebRTC room token minting and zero-shot custom voice conditioning.
- 🔐 **Auth & API Keys**: User profiles, Google/Firebase authentication synchronization, API keys CRUD, and single-use WebSocket tickets.

---

## 🚀 Features

- **✅ Sync & Async Clients**: Built on top of `httpx`, providing parallel `BanglaAI` and `AsyncBanglaAI` interfaces with 100% feature parity.
- **⚡ Real-Time Streaming**: First-class Server-Sent Events (SSE) streaming for LLM tokens and 24 kHz raw PCM audio chunks for TTS.
- **🔄 Long-Running Async Jobs**: High-level `wait_for_job()` helpers for ASR, OCR, and TTS async batch jobs with automatic polling and error resolution.
- **🎙️ Live ASR Streaming**: Stateful sessions supporting raw 16 kHz mono signed 16-bit PCM chunks with generation-based checkpointing.
- **🗣️ Reusable Voice Cloning**: Upload short reference audio samples once and reuse the generated `voice_id` across TTS and STS.
- **🛡️ Robust Error Handling**: Clean RFC 7807 typed exceptions (`RateLimitError`, `AuthenticationError`, `UpstreamServiceError`, etc.) with automatic exponential backoff retry.
- **🔐 Flexible Authentication**: Auto-discovers credentials from `BANGLA_AI_API_KEY` environment variables or `.env` file via `python-dotenv`.

---

## 📦 Installation

```bash
pip install bangla-ai-sdk
```

Or for local development:

```bash
git clone https://github.com/jayeeed/bangla-ai.git
cd bangla-ai/sdk/python
pip install -e .
```

---

## ⚡ Quick Start

### 1. Configure Environment

Copy `.env.example` to `.env` and set your API key:

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

# Automatically reads BANGLA_AI_API_KEY from environment
client = BanglaAI()

# 1. Check identity
me = client.me.get()
print(f"Logged in as: {me.display_name} ({me.email}) - Tier: {me.plan}")

# 2. Chat with the Bengali LLM
chat = client.chats.create(title="Introduction")
turn = client.chats.turns.create(chat.id, content="বাংলা ব্যাকরণ অনুযায়ী সমাস কাকে বলে?")
print("AI:", turn.content)
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

## 📖 Complete Modality Guide

### 1. LLM & Conversational Chat

#### Token-by-Token Streaming (Server-Sent Events)
```python
chat = client.chats.create(
    title="Programming Tutorial",
    instructions="আপনি একজন অভিজ্ঞ পাইথন প্রোগ্রামার। প্রাতিষ্ঠানিক বাংলায় উত্তর দিন।"
)

# Stream tokens in real time (automatically includes RFC 4122 Idempotency-Key)
for chunk in client.chats.turns.stream(chat.id, content="পাইথনে ডেকোরেটর কী এবং এটি কীভাবে কাজ করে?"):
    if chunk.text:
        print(chunk.text, end="", flush=True)
print()
```

#### Uploading Chat Attachments & Message History
```python
# Upload document to MinIO
att = client.chats.attachments.upload(chat.id, "invoice.pdf")
print(f"Attached: {att.filename} ({att.size_bytes} bytes)")

# Submit message referencing attachment
reply = client.chats.turns.create(
    chat.id,
    content="এই ইনভয়েসের মোট টাকার পরিমাণ কত?",
    attachment_ids=[att.id]
)
print("AI:", reply.content)

# Retrieve full message turn history
history = client.chats.messages(chat.id)
for turn in history:
    print(f"[{turn.status}] User: {turn.input_content} -> AI: {turn.output_text}")

# Fork conversation history into a new branch
branch = client.chats.create_branch(
    chat.id,
    source_branch_id=chat.active_branch_id,
    target_turn_id=reply.turn_id,
    action="regenerate"
)
```

---

### 2. Document OCR

#### Synchronous Document OCR (Single-Page / Fast Scan)
```python
result = client.ocr.process("nid_card.jpg")
print("Extracted Markdown:\n", result.markdown)

# Inspect layout regions and bounding boxes
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

#### Asynchronous Audio Transcription (for Long Files)
```python
# Submit job and poll until completion
job_status = client.asr.wait_for_job("long_lecture_2hours.mp3", diarize=True)
print("Finished ASR:", job_status.result["text"])
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

#### Live 16 kHz PCM16 Streaming
```python
# 1. Start streaming session
session = client.asr.create_stream(sample_rate=16000)

# 2. Feed 16-bit mono PCM chunks as they arrive from microphone
chunk = client.asr.stream_chunk(session.session_id, pcm_bytes)
print("Partial:", chunk.partial_text)
if chunk.final_text:
    print("Final segment:", chunk.final_text)

# 3. Finalize stream
res = client.asr.finish_stream(session.session_id)
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

#### Reusable Voice Cloning & Upload
```python
# Upload 3-10s audio clip to create a reusable voice profile
voice_info = client.tts.create_voice("my_voice_sample.wav", name="My Voice")
voice_id = voice_info.voice_id

# Synthesize speech using the cloned voice ID
audio_bytes = client.tts.synthesize("আমার ক্লোন করা কণ্ঠে এই বাক্যটি বলা হচ্ছে।", voice_id=voice_id)
```

#### Asynchronous Synthesis Batch Jobs
```python
# Enqueue long paragraph and wait for synthesized audio
audio_bytes = client.tts.wait_for_job("দীর্ঘ বাংলা অনুচ্ছেদ যা সিন্থেসাইজ হতে সময় নেয়।")
with open("long_speech.wav", "wb") as f:
    f.write(audio_bytes)
```

#### Incremental Text Streaming Sessions
```python
# Create low-latency incremental session
session = client.tts.create_session(voice="male")

# Feed LLM tokens as they arrive
client.tts.send_session_text(session.session_id, "প্রথম বাক্য।")
client.tts.send_session_text(session.session_id, "দ্বিতীয় বাক্য।")

# Finish session
client.tts.finish_session(session.session_id)
client.tts.delete_session(session.session_id)
```

#### Discover Capabilities & Queue Load
```python
caps = client.tts.capabilities()
print("Supported formats:", caps.response_formats)

queue = client.tts.queue()
print(f"Queue load: {queue.active} active / {queue.capacity} capacity")
```

---

### 5. Speech-to-Speech (STS) & LiveKit WebRTC

```python
# 1. Upload a cloned voice sample
voice_ref = client.sts.upload_voice_reference("my_voice.wav")
print(f"Voice Reference ID: {voice_ref.reference_id}")

# 2. Mint LiveKit Room Token
room_access = client.sts.create_token(reference_id=voice_ref.reference_id, room_name="my-room")
print("LiveKit URL:", room_access.url)
print("Access Token:", room_access.token)
print("Allocated Room:", room_access.room)

# Connect with any LiveKit Client SDK (JavaScript, iOS, Android, Python)
```

---

### 6. Profile, Google Auth & API Keys

```python
# Synchronize Google / Firebase ID token
auth_status = client.auth.sync_google(id_token="firebase_jwt_token_here")
print("Synced User:", auth_status.user.email)

# Update display settings
client.me.update(display_name="Rahim Ahmed", avatar_url="https://example.com/avatar.png")

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

## 🧪 Verification Suite

```bash
python test.py
```

---

## 📄 License

MIT License. See [LICENSE](LICENSE) for details.
