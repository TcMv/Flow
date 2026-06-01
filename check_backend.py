import os, httpx

token = os.environ["VERCEL_TOKEN"]
pid = "prj_xrcdweOKTdKHldxOsBAl2ggs9aB1"

# Get backend env vars
r = httpx.get(f"https://api.vercel.com/v9/projects/{pid}/env", headers={"Authorization": f"Bearer {token}"})
print(f"Env vars ({r.status_code}):")
if r.status_code == 200:
    for e in r.json().get("envs", []):
        print(f"  {e['key']}: {e['target']}")

# Get deployments
r = httpx.get(f"https://api.vercel.com/v6/deployments?projectId={pid}&limit=3", headers={"Authorization": f"Bearer {token}"})
print(f"\nDeployments ({r.status_code}):")
if r.status_code == 200:
    for d in r.json().get("deployments", []):
        print(f"  {d['url']}: {d['state']} — created: {d.get('createdAt','?')}")
