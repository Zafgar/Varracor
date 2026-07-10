# tools/asset_scan.py
"""
Puuttuvien assettien skanneri.

Käy läpi kaikki .py-tiedostot, kerää "assets/..."-polkuviittaukset ja
tarkistaa mitkä tiedostot puuttuvat levyltä. Tuottaa MISSING_ASSETS.md
-raportin, josta näkee suoraan mihin polkuun ja millä nimellä kuvat,
äänet ja musiikki pitää laittaa.

Aja projektin juuresta:
    python tools/asset_scan.py
"""
import os
import re
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Tunnistettavat tiedostotyypit
TYPE_BY_EXT = {
    ".png": "kuva", ".jpg": "kuva", ".jpeg": "kuva", ".bmp": "kuva", ".gif": "kuva",
    ".wav": "ääni", ".ogg": "ääni",
    ".mp3": "musiikki",
    ".mp4": "video", ".avi": "video",
    ".ttf": "fontti", ".otf": "fontti",
}

# "assets/..." merkkijonoliteraalit (myös f-stringien staattiset osat)
ASSET_RE = re.compile(r"""["'](assets/[^"']+)["']""")


def scan():
    static_refs = defaultdict(set)   # polku -> {viittaavat tiedostot}
    dynamic_refs = defaultdict(set)  # {}-muuttujia sisältävä polku -> {tiedostot}

    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__", ".git", "assets")]
        for fn in filenames:
            if not fn.endswith(".py"):
                continue
            fpath = os.path.join(dirpath, fn)
            rel_src = os.path.relpath(fpath, ROOT)
            if rel_src == os.path.join("tools", "asset_scan.py"):
                continue  # älä skannaa itseäsi
            try:
                text = open(fpath, encoding="utf-8").read()
            except Exception:
                continue
            for match in ASSET_RE.finditer(text):
                path = match.group(1)
                ext = os.path.splitext(path)[1].lower()
                # Ilman tunnettua päätettä kyseessä on pohjapolku, josta
                # koodi rakentaa variantit (esim. _idle.png / _hit.png)
                if "{" in path or path.endswith("/") or ext not in TYPE_BY_EXT:
                    dynamic_refs[path].add(rel_src)
                else:
                    static_refs[path].add(rel_src)

    missing = {p: srcs for p, srcs in static_refs.items()
               if not os.path.exists(os.path.join(ROOT, p))}
    present = len(static_refs) - len(missing)
    return static_refs, missing, dynamic_refs, present


def write_report(static_refs, missing, dynamic_refs, present):
    out = os.path.join(ROOT, "MISSING_ASSETS.md")
    by_dir = defaultdict(list)
    for path, srcs in sorted(missing.items()):
        top = "/".join(path.split("/")[:2])  # esim. assets/ui
        by_dir[top].append((path, srcs))

    lines = []
    lines.append("# Puuttuvat assetit")
    lines.append("")
    lines.append("Generoitu komennolla `python tools/asset_scan.py` — aja uudelleen")
    lines.append("aina kun lisäät tiedostoja, niin lista pysyy ajan tasalla.")
    lines.append("")
    lines.append(f"- Koodissa viitattuja tiedostoja: **{len(static_refs)}**")
    lines.append(f"- Löytyy levyltä: **{present}**")
    lines.append(f"- Puuttuu: **{len(missing)}**")
    lines.append("")
    lines.append("Laita tiedosto täsmälleen alla olevaan polkuun (suhteessa pelin")
    lines.append("juurikansioon), niin peli löytää sen automaattisesti — koodia ei")
    lines.append("tarvitse muuttaa. Peli toimii myös ilman näitä (procedural fallback).")
    lines.append("")

    for top in sorted(by_dir):
        lines.append(f"## {top}/ ({len(by_dir[top])} kpl)")
        lines.append("")
        lines.append("| Tiedosto | Tyyppi | Käytetään tiedostossa |")
        lines.append("|---|---|---|")
        for path, srcs in by_dir[top]:
            ext = os.path.splitext(path)[1].lower()
            ftype = TYPE_BY_EXT.get(ext, ext or "?")
            src_list = ", ".join(sorted(srcs)[:3])
            if len(srcs) > 3:
                src_list += f" (+{len(srcs) - 3} muuta)"
            lines.append(f"| `{path}` | {ftype} | {src_list} |")
        lines.append("")

    if dynamic_refs:
        lines.append("## Dynaamiset polut")
        lines.append("")
        lines.append("Nämä polut rakennetaan koodissa muuttujista (esim. framet 1..N),")
        lines.append("joten tarkkaa tiedostolistaa ei voi päätellä automaattisesti.")
        lines.append("Katso viittaava koodi nähdäksesi mitä nimiä odotetaan:")
        lines.append("")
        for path, srcs in sorted(dynamic_refs.items()):
            lines.append(f"- `{path}` — {', '.join(sorted(srcs)[:2])}")
        lines.append("")

    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out


def main():
    static_refs, missing, dynamic_refs, present = scan()
    out = write_report(static_refs, missing, dynamic_refs, present)
    print(f"Viitattuja assetteja: {len(static_refs)}, puuttuu: {len(missing)}")
    print(f"Raportti: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
