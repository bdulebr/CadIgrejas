import re

log_path = r"C:\Users\MarcosLira\.gemini\antigravity\brain\28038ed3-5edd-4215-bb26-e8a40ae0aa82\.system_generated\logs\transcript.jsonl"

with open(log_path, 'r', encoding='utf-8') as f:
    text = f.read()

match = re.search(r'(.{0,500}class CustomPasswordResetView.{0,1000})', text, re.DOTALL)
if match:
    print(match.group(1).encode('unicode_escape').decode('utf-8'))
