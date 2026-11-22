import hashlib,json,sys
from pathlib import Path
target=sys.argv[1]
arch={"x86_64-pc-windows-msvc":"amd64-v2","aarch64-pc-windows-msvc":"arm64"}[target]
base=Path("source")
lock=json.loads((base/"distribution.lock.json").read_text())
sidecar=base/"src-tauri/sidecar"/f"verge-mihomo-{target}.exe"
with sidecar.open("rb") as f: digest=hashlib.file_digest(f,"sha256").hexdigest()
if digest!=lock["core"]["windows"][arch]["exe_sha256"]: raise ValueError("Staged core differs from verified release")
hashes=(base/"src-tauri/packages/windows/core-hashes.nsh").read_text()
if digest not in hashes or "MIHOMO_ALPHA_SHA256" in hashes: raise ValueError("Unexpected installer core hashes")
config=base/"src-tauri/tauri.conf.json"
document=json.loads(config.read_text(encoding="utf-8"))
settings=document["plugins"]["updater"]
official="github.com/clash-verge-rev/clash-verge-rev/releases/"
if not settings["endpoints"] or not all(official in url for url in settings["endpoints"]): raise ValueError("Review changed upstream updater endpoints")
settings["pubkey"]=Path("control/release/updater.pub").read_text().strip()
settings["endpoints"]=[url.replace(official,"github.com/vertno/clash-verge-rev/releases/") for url in settings["endpoints"]]
config.write_text(json.dumps(document,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Staged stable core verified:",arch,digest)
