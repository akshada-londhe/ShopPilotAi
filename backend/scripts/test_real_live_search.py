import json
import urllib.request
import time

url = 'http://localhost:3001/api/search'
query = 'Skincare for dry skin'
print(f'=== Testing Real Search for: "{query}" ===')
req = urllib.request.Request(url, data=json.dumps({'query': query}).encode('utf-8'), headers={'Content-Type': 'application/json'}, method='POST')

t0 = time.time()
with urllib.request.urlopen(req) as resp:
    raw = resp.read().decode('utf-8')
    lines = raw.split('\n\n')
    events = [json.loads(l.replace('data: ', '')) for l in lines if l.startswith('data: ')]
    print(f'Received {len(events)} events in {time.time()-t0:.2f}s:')
    for idx, e in enumerate(events, 1):
        evt_type = e.get('event')
        if evt_type == 'progress':
            print(f'  [{idx}] Progress ({e["payload"].get("stage")}): {e["payload"].get("message")}')
        elif evt_type == 'result':
            products = e['payload'].get('products', [])
            print(f'  [{idx}] RESULT RECEIVED: {len(products)} products found!')
            for p in products[:3]:
                print(f'      - {p.get("name")} | Price: {p.get("fields", {}).get("price", {}).get("value")}')
