"""Quick script to check engine alerts."""
import httpx
import time
import json

time.sleep(10)
r = httpx.get("http://localhost:8000/alerts")
alerts = r.json()
print(f"Total alerts: {len(alerts)}")
for a in alerts:
    print(f"  [{a['type']}] {a['message'][:120]}")
print()
print("Full JSON:")
print(json.dumps(alerts, indent=2))
