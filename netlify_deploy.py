"""
Deploy a single-page site to Netlify via the file-digest API (correct MIME types).
Needs NETLIFY_AUTH_TOKEN (env or .netlify_token file). Each call = new Netlify site.
"""
import os, re, time, hashlib, secrets, requests

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


def slugify(name, maxlen=37):
    """Business name -> Netlify subdomain. e.g. 'Lily Med Spa' -> 'lily-med-spa'.
    Netlify subdomains: lowercase a-z0-9 and hyphens, must start/end alnum, <=63 chars.
    Cap at 37 to leave room for a uniqueness suffix."""
    s = re.sub(r"[^a-z0-9]+", "-", (name or "").lower())
    s = re.sub(r"-{2,}", "-", s).strip("-")
    return s[:maxlen].strip("-") or "site"


def _create_site(headers, site_name):
    """Create a site, preferring `site_name` as the subdomain. Netlify subdomains are
    GLOBALLY unique, so if the name is taken (HTTP 422) append a short suffix and retry;
    final fallback lets Netlify pick a random name so a deploy never hard-fails on naming."""
    candidates = []
    if site_name:
        base = slugify(site_name)
        candidates = [base] + [f"{base}-{secrets.token_hex(2)}" for _ in range(4)]
    candidates.append(None)  # last resort: Netlify-generated random name
    last = None
    for nm in candidates:
        r = requests.post(f"{API}/sites", headers=headers,
                          json=({"name": nm} if nm else {}), timeout=60)
        if r.status_code == 422 and nm is not None:
            last = r           # name taken or invalid -> try the next candidate
            continue
        r.raise_for_status()
        return r.json()
    last.raise_for_status()


def deploy_html(html, site_name=None, extra_files=None):
    """
    html: index.html content (str). site_name: business name -> becomes the subdomain
      (slugified, e.g. 'Lily Med Spa' -> lily-med-spa.netlify.app), unique-suffixed on clash.
    extra_files: optional {"/path": str|bytes}.
    Returns (live_url, site_id). Uses digest deploy so .html serves as text/html.
    """
    h = {"Authorization": f"Bearer {_token()}"}
    site = _create_site(h, site_name)
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
