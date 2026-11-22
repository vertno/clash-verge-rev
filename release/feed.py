"""Check both native update manifests against the two signed Windows installers."""
import json,subprocess,sys,tempfile
from pathlib import Path
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
    with tempfile.TemporaryDirectory() as d:
        for name in ["update.json","update-proxy.json"]:
            p=gh("release","download","updater","-R",repo,"-D",d,"-p",name)
            if p.returncode: return False
            data=json.loads((Path(d)/name).read_text())
            if (data.get("version") or data.get("name") or "").removeprefix("v")!=rel["tag_name"].removeprefix("v"): return False
            for cpu,key in (("x64","windows-x86_64-nsis"),("arm64","windows-aarch64-nsis")):
                asset,=[a for a in rel["assets"] if a["name"].endswith(cpu+"-setup.exe")]
                row=data["platforms"][key]
                expected=("https://update.hwdns.net/" if "proxy" in name else "")+asset["browser_download_url"]
                if row["url"]!=expected: return False
                sig=asset["name"]+".sig"
                if not (Path(d)/sig).exists() and gh("release","download",rel["tag_name"],"-R",repo,"-D",d,"-p",sig).returncode: return False
                if row["signature"].strip()!=(Path(d)/sig).read_text().strip(): return False
    return True
if __name__=="__main__":
    import os
    rel=latest()
    if sys.argv[1]=="check":
        ok=not rel or valid(rel)
        with open(os.environ["GITHUB_OUTPUT"],"a") as f:
            print("repair="+str(not ok).lower(),file=f)
            if rel: print("tag="+rel["tag_name"],file=f)
    elif not rel or not valid(rel): raise ValueError("Native update feeds are missing or do not match signed assets")
