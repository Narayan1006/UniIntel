"""
Full Pipeline Diagnosis Script — uploads sample CSV and polls every stage until complete or error.
"""
import urllib.request
import json
import time
import sys

BASE = "http://localhost:8082/api/v1/enrichment"
CSV_PATH = "Unihack_ Sample Dataset - Input.csv"

# ── Step 1: Upload CSV ────────────────────────────────────────────────────────
print("=" * 60)
print("STEP 1: Uploading sample dataset...")
print("=" * 60)

boundary = "DIAGBOUNDARY001"
with open(CSV_PATH, "rb") as f:
    csv_data = f.read()

body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="file"; filename="sample.csv"\r\n'
    f"Content-Type: text/csv\r\n\r\n"
).encode() + csv_data + f"\r\n--{boundary}--\r\n".encode()

req = urllib.request.Request(
    f"{BASE}/upload",
    data=body,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
)
try:
    with urllib.request.urlopen(req, timeout=30) as r:
        resp = json.loads(r.read().decode())
        print(f"[OK] Upload Response: {json.dumps(resp, indent=2)}")
except Exception as e:
    print(f"[ERROR] Upload failed: {e}")
    sys.exit(1)

# ── Step 2: Poll Status ───────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("STEP 2: Polling pipeline status every 10 seconds...")
print("=" * 60)

last_stage = -1
poll_count = 0
max_polls = 60  # 60 * 10s = 10 minutes max

while poll_count < max_polls:
    time.sleep(10)
    poll_count += 1
    try:
        with urllib.request.urlopen(f"{BASE}/status", timeout=10) as r:
            status = json.loads(r.read().decode())
            
            stage = status.get("stage", "?")
            label = status.get("stage_label", "").encode("ascii", "replace").decode()
            is_running = status.get("is_running")
            error = status.get("error")
            metrics = status.get("metrics")

            if stage != last_stage:
                print(f"\n  [STAGE CHANGE] → Stage {stage}: {label}")
                last_stage = stage
            else:
                print(f"  [{poll_count:02d}] Stage {stage}: {label} | running={is_running}")

            if error:
                print(f"\n[PIPELINE ERROR DETECTED]")
                print(f"  Error: {error}")
                break

            if not is_running and poll_count > 2:
                print(f"\n[PIPELINE COMPLETED!]")
                if metrics:
                    print("Final Metrics:")
                    print(json.dumps(metrics, indent=2))
                break

    except Exception as e:
        print(f"  [Poll Error {poll_count}]: {e}")

print("\n" + "=" * 60)
print("DIAGNOSIS COMPLETE")
print("=" * 60)
