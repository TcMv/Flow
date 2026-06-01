import os, httpx

token = os.environ["VERCEL_TOKEN"]
project_id = "prj_aAA4plG7tcxhxfwCoIHAi67X5HsP"

r = httpx.post(
    f"https://api.vercel.com/v10/projects/{project_id}/env",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "key": "VITE_API_URL",
        "value": "https://backend-liard-alpha-17.vercel.app",
        "target": ["production", "preview"],
        "type": "plain"
    }
)
print(f"Status: {r.status_code}")
print(r.text)
