import os, httpx

token = os.environ["VERCEL_TOKEN"]
pid = "prj_xrcdweOKTdKHldxOsBAl2ggs9aB1"

# Get latest deployment
r = httpx.get(f"https://api.vercel.com/v6/deployments?projectId={pid}&limit=1&state=READY", headers={"Authorization": f"Bearer {token}"})
dep_id = r.json()["deployments"][0]["uid"]
print(f"Deployment: {dep_id}")

# Get deployment events (logs)
r = httpx.get(f"https://api.vercel.com/v1/deployments/{dep_id}/events?limit=50", headers={"Authorization": f"Bearer {token}"})
if r.status_code == 200:
    events = r.json()
    if isinstance(events, list):
        for e in events:
            ts = e.get("created", e.get("date", ""))
            txt = e.get("text", e.get("payload", {}).get("message", str(e)))[:300]
            print(f"  [{ts}] {txt}")
    else:
        print(f"  Response: {str(events)[:500]}")
else:
    print(f"Events error: {r.status_code}")
    print(r.text[:500])
