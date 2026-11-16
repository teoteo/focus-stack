#!/usr/bin/env python3
"""Compila fs-rawstat (tools/rawstat/rawstat.cpp + LibRaw da third_party/LibRaw) come binario universale
arm64 + x86_64 per macOS 13 o successivi.

    python3 tools/rawstat/build.py            → build/rawstat/fs-rawstat
    python3 tools/rawstat/build.py --out DIR  → DIR/fs-rawstat

I file di LibRaw sono quelli del blocco LIB_OBJECTS di Makefile.dist (versione senza thread: ogni misura è un
processo a sé), come fa Focus Fusion con la sua copia della stessa versione. Gli oggetti compilati restano in
build/rawstat/obj e si ricompilano solo se il sorgente cambia. Serve Xcode o i Command Line Tools (clang++).
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIBRAW = ROOT / "third_party" / "LibRaw"
TOOL = Path(__file__).resolve().parent / "rawstat.cpp"
FLAGS = ["-O2", "-w", "-std=c++11", "-arch", "arm64", "-arch", "x86_64", "-mmacosx-version-min=13.0",
         "-DLIBRAW_NOTHREADS", "-DLIBRAW_NODLL", f"-I{LIBRAW}"]


def libraw_sources() -> list[Path]:
    mk = (LIBRAW / "Makefile.dist").read_text()
    objects, inside = [], False
    for line in mk.splitlines():
        if line.startswith("LIB_OBJECTS="):
            inside = True
        if inside:
            for tok in line.split():
                tok = tok.rstrip("\\")
                if tok.startswith("object/") and tok.endswith(".o"):
                    objects.append(tok[len("object/"):-2])
            if not line.rstrip().endswith("\\"):
                break
    if len(objects) < 50:
        sys.exit(f"Lista dei sorgenti di LibRaw incompleta ({len(objects)}): manca il sottomodulo? "
                 "git submodule update --init")
    srcs = []
    for o in objects:
        rule = next((l for l in mk.splitlines() if l.startswith(f"object/{o}.o:")), None)
        if not rule:
            sys.exit(f"Regola mancante per {o}")
        srcs.append(LIBRAW / rule.split(":", 1)[1].split()[0])
    return srcs


def compile_one(src: Path, obj: Path) -> None:
    if obj.exists() and obj.stat().st_mtime >= src.stat().st_mtime:
        return
    obj.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(["clang++", *FLAGS, "-c", str(src), "-o", str(obj)], check=True)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "build" / "rawstat"))
    out = Path(ap.parse_args().out)
    objdir = ROOT / "build" / "rawstat" / "obj"
    srcs = libraw_sources()
    jobs = [(s, objdir / (s.stem + ".o")) for s in srcs] + [(TOOL, objdir / "rawstat.o")]
    with ThreadPoolExecutor(max_workers=os.cpu_count() or 4) as ex:
        list(ex.map(lambda j: compile_one(*j), jobs))
    out.mkdir(parents=True, exist_ok=True)
    exe = out / "fs-rawstat"
    subprocess.run(["clang++", *FLAGS, *(str(o) for _, o in jobs), "-o", str(exe),
                    "-framework", "ImageIO", "-framework", "CoreGraphics", "-framework", "CoreFoundation"], check=True)
    subprocess.run(["strip", "-x", str(exe)], check=True)
    print(f"{exe} ({exe.stat().st_size // 1024} KB, {len(srcs)} file di LibRaw)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
