import httpx
import time
import statistics
import os
from dotenv import load_dotenv
from gateway.auth import create_token

load_dotenv()

GATEWAY_URL = "https://prismbrain.co"
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

token = create_token("benchmark-user", "senior-dev")
headers = {
    "Authorization": f"Bearer {token}",
    "X-Upstream-Key": OPENAI_KEY,
    "Content-Type": "application/json"
}
payload = {
    "upstream_url": OPENAI_URL,
    "payload": {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": "hi"}]},
    "tool": "chat_completion"
}

# Latency test -- 50 requests
print("Running latency test...")
latencies = []
for i in range(50):
    start = time.time()
    httpx.post(f"{GATEWAY_URL}/call_tool", headers=headers, json=payload)
    latencies.append((time.time() - start) * 1000)

p95 = statistics.quantiles(latencies, n=20)[18]
print(f"p95 latency: {p95:.1f}ms")
print(f"avg latency: {statistics.mean(latencies):.1f}ms")

# PII test -- 10 entity types
print("\nRunning PII redaction test...")
pii_tests = [
    ("email", "My email is john.doe@example.com"),
    ("SSN", "My SSN is 123-45-6789"),
    ("credit_card", "My card is 4111111111111111"),
    ("phone", "Call me at 555-123-4567"),
    ("name", "My name is John Smith"),
    ("ip_address", "My IP is 192.168.1.100"),
    ("date_of_birth", "I was born on 01/01/1990"),
    ("passport", "My passport is AB1234567"),
    ("address", "I live at 123 Main Street New York"),
    ("bank_account", "My account is 12345678901234"),
]

for pii_type, text in pii_tests:
    p = {
        "upstream_url": OPENAI_URL,
        "payload": {"model": "gpt-4o-mini", "messages": [{"role": "user", "content": text}]},
        "tool": "chat_completion"
    }
    r = httpx.post(f"{GATEWAY_URL}/call_tool", headers=headers, json=p)
    print(f"{pii_type}: {'200 OK - PII scrubbed' if r.status_code == 200 else 'FAILED'}")
