import os, httpx

token = os.environ["VERCEL_TOKEN"]
pid = "prj_xrcdweOKTdKHldxOsBAl2ggs9aB1"

# Get env vars with decryption
r = httpx.get(f"https://api.vercel.com/v9/projects/{pid}/env?decrypt=true", headers={"Authorization": f"Bearer {token}"})
print(f"Status: {r.status_code}")
if r.status_code == 200:
    for env in r.json().get("envs", []):
        val = env.get("value", "")
        masked = val[:50] + "..." if len(val) > 50 else val
        print(f"  {env['key']} = {masked}")
    
    # Check if DATABASE_URL has correct format
    db_url = [e for e in r.json()["envs"] if e["key"] == "DATABASE_URL"]
    if db_url:
        print(f"\nDB URL starts with: {db_url[0]['value'][:40]}...")
        
    # Check ENCRYPTION_KEY
    ek = [e for e in r.json()["envs"] if e["key"] == "ENCRYPTION_KEY"]
    if ek:
        print(f"Encryption key: {ek[0]['value'][:20]}...")
else:
    print(r.text[:500])
