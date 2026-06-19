"""
Deploy a single-page site to Netlify via the file-digest API (correct MIME types).
Needs NETLIFY_AUTH_TOKEN (env or .netlify_token file). Each call = new Netlify site.
"""
import os, time, hashlib, requests

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://api.netlify.com/api/v1"


def _token():
    f = os.path.join(HERE, ".netlify_token")
    if os.path.exists(f):
        return open(f).read().strip()
    t = os.environ.get("NETLIFY_AUTH_TOKEN")
    if not t:
        raise RuntimeError("No Netlify token: create .netlify_token or set NETLIFY_AUTH_TOKEN")
    return t


def deploy_html(html, site_name=None, extra_files=None):
    """
    html: index.html content (str). site_name: optional unique subdomain.
    extra_files: optional {"/path": str|bytes}.
    Returns (live_url, site_id). Uses digest deploy so .html serves as text/html.
    """
    h = {"Authorization": f"Bearer {_token()}"}
    site = requests.post(f"{API}/sites", headers=h, json=({"name": site_name} if site_name else {}), timeout=60)
    site.raise_for_status()
    site = site.json()
    sid = site["id"]

    files = {"/index.html": html.encode("utf-8") if isinstance(html, str) else html}
    for p, data in (extra_files or {}).items():
        files["/" + p.lstrip("/")] = data.encode("utf-8") if isinstance(data, str) else data

    digests = {p: hashlib.sha1(b).hexdigest() for p, b in files.items()}
    dep = requests.post(f"{API}/sites/{sid}/deploys", headers=h, json={"files": digests}, timeout=60)
    dep.raise_for_status()
    dep = dep.json()
    did = dep["id"]

    required = set(dep.get("required") or [])
    for p, b in files.items():
        if digests[p] in required:            # only upload what Netlify asks for
            up = requests.put(f"{API}/deploys/{did}/files{p}", headers={**h, "Content-Type": "application/octet-stream"},
                              data=b, timeout=120)
            up.raise_for_status()

    url = site.get("ssl_url") or site.get("url")
    return url, sid


if __name__ == "__main__":
    demo = "<!doctype html><html><head><title>Render test</title></head><body style='font-family:sans-serif;padding:4rem'><h1>If you see a heading (not code), MIME is fixed ✅</h1></body></html>"
    url, sid = deploy_html(demo)
    print("LIVE:", url, "site_id:", sid)
    time.sleep(4)
    import subprocess
    print(subprocess.run(["curl", "-sI", url], capture_output=True, text=True).stdout.split("content-type")[0][:0] or "")
