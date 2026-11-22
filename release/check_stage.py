import hashlib,json,sys
from pathlib import Path
target=sys.argv[1]
arch={"x86_64-pc-windows-msvc":"amd64-v2","aarch64-pc-windows-msvc":"arm64"}[target]
base=Path("source")
lock=json.loads((base/"distribution.lock.json").read_text())
expected = lock["core"]["windows"][arch]["exe_sha256"]
defines = (base / "src-tauri/packages/windows/core-hashes.nsh").read_text().splitlines()
for name, define in (("verge-mihomo", "MIHOMO_SHA256"), ("verge-mihomo-alpha", "MIHOMO_ALPHA_SHA256")):
    sidecar = base / "src-tauri/sidecar" / f"{name}-{target}.exe"
    with sidecar.open("rb") as binary:
        digest = hashlib.file_digest(binary, "sha256").hexdigest()
    if digest != expected or f'!define {define} "{expected}"' not in defines:
        raise ValueError(f"{name} or its installer hash differs from the locked stable release")
config=base/"src-tauri/tauri.conf.json"
document=json.loads(config.read_text(encoding="utf-8"))
settings=document["plugins"]["updater"]
official="github.com/clash-verge-rev/clash-verge-rev/releases/"
if not settings["endpoints"] or not all(official in url for url in settings["endpoints"]): raise ValueError("Review changed upstream updater endpoints")
settings["pubkey"]=Path("control/release/updater.pub").read_text().strip()
settings["endpoints"]=[url.replace(official,"github.com/vertno/clash-verge-rev/releases/") for url in settings["endpoints"]]
config.write_text(json.dumps(document,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
print("Both staged cores and installer hashes verified:",arch,expected)
