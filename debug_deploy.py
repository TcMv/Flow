"""Quick test to identify what's failing on Vercel."""
import os, httpx

token = os.environ["VERCEL_TOKEN"]
pid = "prj_xrcdweOKTdKHldxOsBAl2ggs9aB1"

# Try to get function invocation logs
r = httpx.get(
    f"https://api.vercel.com/v1/deployments?projectId={pid}&limit=1",
    headers={"Authorization": f"Bearer {token}"}
)
dep_id = r.json()["deployments"][0]["uid"]
print(f"Deployment: {dep_id}")

# Try lambda logs
for path in [
    f"https://api.vercel.com/v1/deployments/{dep_id}/events",
    f"https://api.vercel.com/v2/deployments/{dep_id}/events",
    f"https://api.vercel.com/v1/deployments/{dep_id}/alerts",
]:
    r2 = httpx.get(path, headers={"Authorization": f"Bearer {token}"})
    print(f"{path}: {r2.status_code}")

# Check env vars to make sure they're set correctly
r3 = httpx.get(f"https://api.vercel.com/v9/projects/{pid}/env", headers={"Authorization": f"Bearer {token}"})
print(f"\nEnv vars check:")
for env in r3.json().get("envs", []):
    val = env.get("value", "")
    masked = val[:8] + "..." if len(val) > 8 else "(empty)" if not val else val
    print(f"  {env['key']} = {masked}")
