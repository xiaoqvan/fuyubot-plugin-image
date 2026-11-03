#!/usr/bin/env python3
"""把 `cargo build --release` 的产物打成 FuyuBot bundle zip。"""

from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLUGIN_ID = "image-plugin"
# platform: (动态库文件名, 额外随包文件)
TARGETS = {
    "windows-x86_64": ("image_plugin.dll", ["image-shot.exe"]),
    "linux-x86_64": ("libimage_plugin.so", ["image-shot"]),
    "macos-aarch64": ("libimage_plugin.dylib", ["image-shot"]),
    "macos-x86_64": ("libimage_plugin.dylib", ["image-shot"]),
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", required=True, choices=sorted(TARGETS))
    parser.add_argument("--version", required=True)
    parser.add_argument("--target-dir", default="target/release")
    args = parser.parse_args()

    lib_name, extras = TARGETS[args.platform]
    release = ROOT / args.target_dir
    lib = release / lib_name
    if not lib.is_file():
        raise SystemExit(f"找不到 {lib}；先 cargo build --release")

    dist = ROOT / "dist"
    bundle = dist / "bundle"
    if bundle.exists():
        shutil.rmtree(bundle)
    bin_dir = bundle / "bin"
    bin_dir.mkdir(parents=True)

    shutil.copy2(lib, bin_dir / lib_name)
    for extra in extras:
        source = release / extra
        if not source.is_file():
            raise SystemExit(f"找不到 {source}")
        shutil.copy2(source, bin_dir / extra)

    manifest = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    manifest["version"] = args.version
    manifest["entry"] = f"bin/{lib_name}"
    manifest["platforms"] = [args.platform]
    (bundle / "plugin.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    archive = dist / f"{PLUGIN_ID}-{args.version}-{args.platform}.zip"
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(bundle.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(bundle))
    print(f"[OK] {archive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
