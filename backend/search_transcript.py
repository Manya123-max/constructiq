import json
import re
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

log_dir = r"C:\Users\manya\.gemini\antigravity-ide\brain\fda33c28-181a-485d-b167-c864e8f4e024\.system_generated\logs"
transcript_path = os.path.join(log_dir, "transcript_full.jsonl")

if not os.path.exists(transcript_path):
    transcript_path = os.path.join(log_dir, "transcript.jsonl")

user_messages = []
urls_found = set()

with open(transcript_path, encoding="utf-8", errors="replace") as f:
    for i, line in enumerate(f):
        try:
            row = json.loads(line)
            step_type = row.get("type", "")
            content = str(row.get("content", ""))
            
            for u in re.findall(r'https?://[^\s"\'<>]+', content):
                urls_found.add(u)
                
            if step_type == "USER_INPUT":
                user_messages.append((i, content))
        except Exception:
            pass

print(f"Found {len(user_messages)} user inputs:")
for idx, msg in user_messages:
    print(f"\n--- STEP {idx} ---")
    print(msg[:1000])

print("\n--- ALL URLS FOUND IN TRANSCRIPT ---")
for u in sorted(urls_found):
    print(u)
