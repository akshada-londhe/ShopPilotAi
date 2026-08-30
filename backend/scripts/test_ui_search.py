"""Test searching and getting real products via Next.js UI search API proxy."""

import json
import urllib.request
import time

FRONTEND_SEARCH_URL = "http://localhost:3001/api/search"
QUERY = "wireless noise canceling headphones under 3000 with good bass"

print(f"=== Testing UI Search via Next.js Proxy ({FRONTEND_SEARCH_URL}) ===")
print(f"Query: \"{QUERY}\"\n")

payload = json.dumps({"query": QUERY}).encode("utf-8")
req = urllib.request.Request(
    FRONTEND_SEARCH_URL,
    data=payload,
    headers={"Content-Type": "application/json"},
    method="POST"
)

start_time = time.time()

try:
    with urllib.request.urlopen(req) as resp:
        print(f"HTTP Status: {resp.status}")
        content = resp.read().decode("utf-8")
        
        lines = content.split("\n\n")
        events = []
        for line in lines:
            if line.startswith("data: "):
                try:
                    event_data = json.loads(line.replace("data: ", ""))
                    events.append(event_data)
                except Exception:
                    pass

        print(f"\nReceived {len(events)} SSE events in {time.time() - start_time:.2f}s:")
        
        for idx, evt in enumerate(events, 1):
            event_type = evt.get("event")
            if event_type == "progress":
                msg = evt.get("payload", {}).get("message", "")
                stage = evt.get("payload", {}).get("stage", "")
                print(f"  [{idx}] SSE Progress ({stage}): {msg}")
            elif event_type == "result":
                payload_data = evt.get("payload", {})
                products = payload_data.get("products", [])
                synthesis = payload_data.get("synthesis", "")
                print(f"\n  [OK] SSE Result Received!")
                print(f"      Total Products Found: {len(products)}")
                print(f"\n--- AI Synthesis ('Why this is best for you') ---")
                print(synthesis.strip())
                print("\n--- Real Product Recommendations ---")
                for p_idx, prod in enumerate(products, 1):
                    name = prod.get("name", "Product")
                    fields = prod.get("fields", {})
                    category = fields.get("category", {}).get("value", "N/A")
                    price = fields.get("price", {}).get("value", "N/A")
                    merchant = fields.get("merchant", {}).get("value", fields.get("store", {}).get("value", "Store"))
                    url = fields.get("source_url", {}).get("value", "N/A")
                    image = fields.get("image_url", {}).get("value", fields.get("image", {}).get("value", "N/A"))
                    soft_score = prod.get("soft_score", 0)
                    
                    print(f"\n  Product #{p_idx}: {name}")
                    print(f"    Category:   {category}")
                    print(f"    Price:      {price}")
                    print(f"    Merchant:   {merchant}")
                    print(f"    Relevance:  {soft_score * 100:.1f}%")
                    print(f"    Store Link: {url}")
                    print(f"    Image Link: {image}")
                    print(f"    Matched:    {', '.join(prod.get('matched_constraints', []))}")
                    
except Exception as err:
    print(f"Error executing UI search: {err}")
