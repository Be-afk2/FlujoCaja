"""Integra assets de terceros (Tailwind, fuentes, Font Awesome) en web/vendor y web/fonts.

Requiere internet en la máquina de desarrollo. Uso:
    python scripts/vendor_assets.py
"""
import pathlib
import re
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
WEB = ROOT / "web"
VENDOR = WEB / "vendor"
FONTS = WEB / "fonts"
CSS = WEB / "css"

CHROME_UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
)
HEADERS = {"User-Agent": CHROME_UA}

TAILWIND_URL = "https://cdn.tailwindcss.com"

FONTS = [
    ("hanken-grotesk", "https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@600;700&display=swap"),
    ("inter", "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"),
    ("jetbrains-mono", "https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@500;600&display=swap"),
    ("public-sans", "https://fonts.googleapis.com/css2?family=Public+Sans:wght@300;400;500;600;700;900&display=swap"),
    ("noto-sans", "https://fonts.googleapis.com/css2?family=Noto+Sans:wght@400;500;700&display=swap"),
    ("material-symbols", "https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap"),
]

FONTAWESOME_VERSION = "6.4.0"
FONTAWESOME_CSS_URL = f"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/{FONTAWESOME_VERSION}/css/all.min.css"


def fetch(url: str) -> bytes:
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=120) as r:
        return r.read()


def download(url: str, dest: pathlib.Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        print(f"ya existe: {dest.name}")
        return
    with open(dest, "wb") as f:
        f.write(fetch(url))
    print(f"descargado: {dest} ({dest.stat().st_size} bytes)")


def vendor_tailwind() -> None:
    VENDOR.mkdir(parents=True, exist_ok=True)
    download(TAILWIND_URL, VENDOR / "tailwind.js")


def vendor_fonts() -> None:
    FONTS_DIR = WEB / "fonts"
    CSS_DIR = WEB / "css"
    FONTS_DIR.mkdir(parents=True, exist_ok=True)
    CSS_DIR.mkdir(parents=True, exist_ok=True)
    chunks = ["/* Fuentes generadas por scripts/vendor_assets.py — reemplazan los CDN */"]
    for slug, css_url in FONTS:
        css = fetch(css_url).decode("utf-8")
        urls = re.findall(r"url\((https://[^)]+)\)", css)
        for idx, u in enumerate(urls):
            suffix = pathlib.Path(u.split("?")[0]).suffix or ".woff2"
            local = f"../fonts/{slug}-{idx + 1}{suffix}"
            download(u, FONTS_DIR / f"{slug}-{idx + 1}{suffix}")
            css = css.replace(u, local)
        chunks.append(f"\n/* ===== {slug} ===== */\n" + css)
    (CSS_DIR / "fonts.css").write_text("\n".join(chunks), encoding="utf-8")
    print(f"fonts.css generado: {CSS_DIR / 'fonts.css'}")


def vendor_fontawesome() -> None:
    base = f"https://cdnjs.cloudflare.com/ajax/libs/font-awesome/{FONTAWESOME_VERSION}"
    css_bytes = fetch(FONTAWESOME_CSS_URL)
    css = css_bytes.decode("utf-8")
    dest_css = WEB / "vendor" / "fontawesome" / "css" / "all.min.css"
    dest_css.parent.mkdir(parents=True, exist_ok=True)
    dest_css.write_bytes(css_bytes)
    print(f"descargado: {dest_css}")
    refs = set(re.findall(r"url\(([^)]+)\)", css))
    for ref in sorted(refs):
        if ref.startswith("data:") or ref.startswith("http"):
            continue
        rel = ref.lstrip("../")
        download(f"{base}/{rel}", WEB / "vendor" / "fontawesome" / rel)


def main() -> None:
    vendor_tailwind()
    vendor_fonts()
    vendor_fontawesome()
    print("Vendoring completo.")


if __name__ == "__main__":
    main()