"""Controllo delle traduzioni di Focus Stack.

    python3 tools/i18n_check.py [--lang en] [--list]

Raccoglie le chiavi (i testi italiani) usate da:
- tr("…") nei file backend/*.py (solo argomenti letterali, anche spezzati su più righe);
- t("…"), t('…'), t(`…`) senza ${…} nei file web/*.js;
- web/index.html e web/viewer.html: nodi di testo con lettere (spazi compressi) e attributi
  title, placeholder, aria-label, alt; esclusi <script>, <style> e gli elementi con
  data-i18n-skip. Per un elemento con data-i18n-html la chiave è il suo HTML interno così come
  è scritto nel file, con gli spazi compressi, e i discendenti non si contano a parte.
e le confronta con web/lang/<lingua>-*.json. Stampa le chiavi senza traduzione, quelle tradotte
ma mai usate e le traduzioni con segnaposto {…} diversi dalla chiave. Esce con 1 se mancano
traduzioni o i segnaposto non corrispondono.
"""
from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ATTRS = ("title", "placeholder", "aria-label", "alt")
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
WS = re.compile(r"\s+")


def norm(text: str) -> str:
    return WS.sub(" ", text).strip()


def has_letters(text: str) -> bool:
    return any(c.isalpha() for c in text)


# ---------------------------------------------------------------- Python
def python_keys(warnings: list[str]) -> dict[str, str]:
    keys: dict[str, str] = {}
    for path in sorted((ROOT / "backend").glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            fn = node.func
            name = fn.id if isinstance(fn, ast.Name) else fn.attr if isinstance(fn, ast.Attribute) else None
            if name != "tr" or not node.args:
                continue
            arg = node.args[0]
            where = f"{path.relative_to(ROOT)}:{node.lineno}"
            if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                keys.setdefault(arg.value, where)
            else:
                warnings.append(f"{where}: tr() con argomento non letterale")
    return keys


# ---------------------------------------------------------------- JavaScript
JS_CALL = re.compile(r"(?<![\w$.])t\(\s*(\"(?:\\.|[^\"\\])*\"|'(?:\\.|[^'\\])*'|`(?:\\.|[^`\\])*`)")


def js_unescape(body: str) -> str:
    out, i = [], 0
    simple = {"n": "\n", "t": "\t", "r": "\r", "0": "\0", "b": "\b", "f": "\f", "v": "\v"}
    while i < len(body):
        c = body[i]
        if c != "\\" or i + 1 >= len(body):
            out.append(c)
            i += 1
            continue
        n = body[i + 1]
        if n == "u" and body[i + 2:i + 3] == "{":
            end = body.index("}", i)
            out.append(chr(int(body[i + 3:end], 16)))
            i = end + 1
        elif n == "u":
            out.append(chr(int(body[i + 2:i + 6], 16)))
            i += 6
        elif n == "x":
            out.append(chr(int(body[i + 2:i + 4], 16)))
            i += 4
        elif n == "\n":
            i += 2
        else:
            out.append(simple.get(n, n))
            i += 2
    return "".join(out)


def js_keys(warnings: list[str]) -> dict[str, str]:
    keys: dict[str, str] = {}
    for path in sorted((ROOT / "web").glob("*.js")):
        src = path.read_text(encoding="utf-8")
        for m in JS_CALL.finditer(src):
            lit = m.group(1)
            line = src.count("\n", 0, m.start()) + 1
            where = f"{path.relative_to(ROOT)}:{line}"
            if lit[0] == "`" and "${" in lit:
                warnings.append(f"{where}: t(`…${{…}}…`) con interpolazione: usa segnaposto {{nome}}")
                continue
            keys.setdefault(js_unescape(lit[1:-1]), where)
    return keys


# ---------------------------------------------------------------- HTML
class Collector(HTMLParser):
    def __init__(self, src: str, label: str):
        super().__init__(convert_charrefs=True)
        self.src, self.label = src, label
        self.lines = src.splitlines(keepends=True)
        self.offsets = [0]
        for ln in self.lines:
            self.offsets.append(self.offsets[-1] + len(ln))
        self.stack: list[tuple[str, str]] = []   # (tag, modo: "", "skip", "html")
        self.html_start: int | None = None
        self.html_depth = 0
        self.keys: dict[str, str] = {}

    def _pos(self) -> int:
        line, col = self.getpos()
        return self.offsets[line - 1] + col

    def _where(self) -> str:
        return f"{self.label}:{self.getpos()[0]}"

    def _blocked(self) -> bool:
        return any(mode in ("skip", "html", "code") for _, mode in self.stack)

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        blocked = self._blocked()
        if not blocked:
            for name in ATTRS:
                val = a.get(name)
                if val and has_letters(val):
                    self.keys.setdefault(norm(val), self._where())
        if tag in VOID:
            return
        if blocked:
            mode = "inner"
        elif tag in ("script", "style"):
            mode = "code"
        elif "data-i18n-skip" in a:
            mode = "skip"
        elif "data-i18n-html" in a:
            mode = "html"
            raw = self.get_starttag_text() or ""
            self.html_start = self._pos() + len(raw)
        else:
            mode = ""
        self.stack.append((tag, mode))

    def handle_startendtag(self, tag, attrs):
        if not self._blocked():
            for name in ATTRS:
                val = dict(attrs).get(name)
                if val and has_letters(val):
                    self.keys.setdefault(norm(val), self._where())

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        # chiude fino al tag corrispondente (HTML tollerante)
        while self.stack:
            t, mode = self.stack.pop()
            if mode == "html" and self.html_start is not None:
                inner = self.src[self.html_start:self._pos()]
                if has_letters(inner):
                    self.keys.setdefault(norm(inner), self._where())
                self.html_start = None
            if t == tag:
                break

    def handle_data(self, data):
        if self._blocked():
            return
        text = norm(data)
        if text and has_letters(text):
            self.keys.setdefault(text, self._where())


def html_keys() -> dict[str, str]:
    keys: dict[str, str] = {}
    for name in ("index.html", "viewer.html"):
        path = ROOT / "web" / name
        if not path.exists():
            continue
        c = Collector(path.read_text(encoding="utf-8"), f"web/{name}")
        c.feed(c.src)
        for k, v in c.keys.items():
            keys.setdefault(k, v)
    return keys


# ---------------------------------------------------------------- confronto
PLACEHOLDER = re.compile(r"\{(\w+)(?:[:!][^}]*)?\}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--lang", default="en")
    ap.add_argument("--list", action="store_true", help="elenca anche tutte le chiavi trovate")
    args = ap.parse_args()

    warnings: list[str] = []
    sources = {"server": python_keys(warnings), "script": js_keys(warnings), "html": html_keys()}
    used: dict[str, str] = {}
    for found in sources.values():
        for k, v in found.items():
            used.setdefault(k, v)

    files = sorted((ROOT / "web" / "lang").glob(f"{args.lang}-*.json"))
    trans: dict[str, str] = {}
    for p in files:
        trans.update(json.loads(p.read_text(encoding="utf-8")))

    missing = {k: v for k, v in used.items() if k not in trans}
    unused = sorted(k for k in trans if k not in used)
    bad_ph = [k for k, v in trans.items()
              if set(PLACEHOLDER.findall(k)) != set(PLACEHOLDER.findall(v))]

    print(f"Lingua {args.lang}: {len(used)} chiavi usate "
          f"(server {len(sources['server'])}, script {len(sources['script'])}, html {len(sources['html'])}), "
          f"{len(trans)} traduzioni in {', '.join(p.name for p in files) or 'nessun file'}")
    if args.list:
        for k, v in sorted(used.items(), key=lambda kv: kv[1]):
            print(f"  {v}: {k!r}")
    for w in warnings:
        print("ATTENZIONE", w)
    if missing:
        print(f"\nSenza traduzione ({len(missing)}):")
        for k, v in sorted(missing.items(), key=lambda kv: kv[1]):
            print(f"  {v}: {k!r}")
    if bad_ph:
        print(f"\nSegnaposto diversi dalla chiave ({len(bad_ph)}):")
        for k in bad_ph:
            print(f"  {k!r} → {trans[k]!r}")
    if unused:
        print(f"\nTradotte ma mai usate ({len(unused)}):")
        for k in unused:
            print(f"  {k!r}")
    return 1 if missing or bad_ph else 0


if __name__ == "__main__":
    sys.exit(main())
