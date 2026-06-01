import os, httpx

token = os.environ["VERCEL_TOKEN"]
pid = "prj_xrcdweOKTdKHldxOsBAl2ggs9aB1"

# Get latest deployment
r = httpx.get(f"https://api.vercel.com/v6/deployments?projectId={pid}&limit=1&state=READY", headers={"Authorization": f"Bearer {token}"})
if r.status_code == 200:
    deps = r.json().get("deployments", [])
    if deps:
        dep_id = deps[0]["uid"]
        print(f"Latest deployment: {deps[0]['url']} (uid: {dep_id})")
        
        # Get deployment logs
        logs = httpx.get(f"https://api.vercel.com/v1/deployments/{dep_id}/logs?limit=20", headers={"Authorization": f"Bearer {token}"})
        print(f"Logs status: {logs.status_code}")
        if logs.status_code == 200:
            entries = logs.json().get("entries", [])
            for e in entries:
                print(f"  [{e.get('created', '?')}] {e.get('text', '')[:200]}")
        else:
            print(f"  {logs.text[:500]}")
else:
    print(f"Error getting deployments: {r.status_code} — {r.text[:500]}")
