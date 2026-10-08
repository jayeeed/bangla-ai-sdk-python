"""
Example 2: Document OCR (Synchronous & Asynchronous Multi-Page)
"""
import os
from bangla_ai import BanglaAI

client = BanglaAI(
    api_key=os.getenv("BANGLA_AI_API_KEY", "sk_live_test_key"),
    base_url=os.getenv("BANGLA_AI_BASE_URL", "https://banglai.acimisai.com"),
)

def main():
    sample_file = "sample_invoice.jpg"

    # Create dummy image if not exists for demonstration
    if not os.path.exists(sample_file):
        with open(sample_file, "wb") as f:
            f.write(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00")

    print("--- 1. Synchronous Single-Page OCR ---")
    try:
        res = client.ocr.process(sample_file)
        print("Markdown Extracted:\n", res.markdown)
        print("Total Pages:", len(res.pages))
    except Exception as e:
        print("OCR process error (expected if mock key):", e)

    print("\n--- 2. Asynchronous Multi-Page OCR with Auto-Polling ---")
    try:
        job = client.ocr.wait_for_job(sample_file, poll_interval=1.0, timeout=30.0)
        print("Completed OCR Job:", job.job_id)
        if job.result:
            print("Job Markdown:\n", job.result.markdown[:100])
    except Exception as e:
        print("OCR job error:", e)

    # Clean up dummy file
    if os.path.exists(sample_file):
        os.remove(sample_file)

if __name__ == "__main__":
    main()
