"""Refresh the upstream updater manifests when a release is missing from either feed."""
import json,subprocess,sys
repo="vertno/clash-verge-rev"
def gh(*args):
    return subprocess.run(["gh",*args],text=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
def latest():
    p=gh("api",f"repos/{repo}/releases/latest")
    if p.returncode:
        if "HTTP 404" in p.stderr: return None
        raise RuntimeError(p.stderr)
    r=json.loads(p.stdout)
    if r["tag_name"]=="updater" or "<!-- distribution " not in (r["body"] or ""): raise ValueError("Latest is not an application release")
    return r
def valid(rel):
    version = rel["tag_name"].removeprefix("v")
    for name in ("update.json", "update-proxy.json"):
        result = gh("release", "download", "updater", "-R", repo, "-p", name, "-O", "-")
        if result.returncode:
            return False
        try:
            manifest = json.loads(result.stdout)
        except ValueError:
            return False
        if not isinstance(manifest, dict):
            return False
        reported = manifest.get("version") or manifest.get("name")
        if reported not in (version, "v" + version):
            return False
        for target in ("windows-x86_64-nsis", "windows-aarch64-nsis"):
            entry = (manifest.get("platforms") or {}).get(target) or {}
            if not entry.get("url") or not entry.get("signature"):
                return False
    return True

if __name__=="__main__":
    import os
    rel=latest()
    if sys.argv[1]=="check":
        ok=not rel or valid(rel)
        with open(os.environ["GITHUB_OUTPUT"],"a") as f:
            print("repair="+str(not ok).lower(),file=f)
            if rel: print("tag="+rel["tag_name"],file=f)
    elif not rel or not valid(rel): raise ValueError("Native update feeds do not yet advertise the published version")
