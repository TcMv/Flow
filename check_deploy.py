import os, httpx

token = os.environ["VERCEL_TOKEN"]

# List projects
r = httpx.get("https://api.vercel.com/v9/projects", headers={"Authorization": f"Bearer {token}"})
if r.status_code == 200:
    for p in r.json().get("projects", []):
        print(f'{p["name"]}: {p["id"]} — framework: {p.get("framework","none")}')
else:
    print(f"Error: {r.status_code} — {r.text[:200]}")

# Get backend deployments
print("\n--- Backend project ---")
# Find backend project
projects = r.json().get("projects", [])
backend = [p for p in projects if p["name"] == "backend"]
if backend:
    pid = backend[0]["id"]
    print(f"Backend project ID: {pid}")
    rd = httpx.get(f"https://api.vercel.com/v1/deployments?projectId={pid}&limit=1&target=production", headers={"Authorization": f"Bearer {token}"})
    if rd.status_code == 200:
        deps = rd.json().get("deployments", [])
        if deps:
            print(f"Latest deploy: {deps[0].get('url')} — state: {deps[0].get('state')}")
        else:
            print("No deployments found")
    else:
        print(f"Error: {rd.status_code} — {rd.text[:200]}")
