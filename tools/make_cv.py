"""Make the CV PDFs (one per language) from the freshly built site, with Chrome.

Runs at every deploy, right after `python tools/build.py` (and locally the same way),
so the CV can never fall behind the page. Standard library only, no new dependency:
it serves dist/ over HTTP on a free local port for the time it takes (fonts, photo and
absolute paths resolve as on the site), prints each language page with css/print.css
(Chrome headless, A4, no header or footer) to dist/cv/cv-santiago-die-{lang}.pdf, sets
the PDF's title with an incremental update (Chrome's own bytes are left untouched), and
checks every PDF. Any failure exits non-zero, so a broken CV fails the deploy instead
of being published.

Checks: the file exists and weighs under 300 KB; at most two pages; the English CV has
no photo and the Spanish and French ones have one (the images in the PDF); the title is
set and the language is the page's.

Usage: python tools/make_cv.py [--chrome PATH]
"""
import argparse
import functools
import http.server
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
OUT = DIST / "cv"
TITLE = "Santiago Die Morejón · CV"
MAX_KB = 300
MAX_PAGES = 2
WITH_PHOTO = {"es", "fr"}  # owner's decision: the English CV goes without the photo
CHROMES = [
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


class CVError(Exception):
    pass


def find_chrome(given):
    for candidate in ([given] if given else []) + CHROMES:
        path = shutil.which(candidate) or (candidate if Path(candidate).exists() else None)
        if path:
            return path
    raise CVError("Chrome not found (tried google-chrome, chromium and the usual paths); "
                  "install it or pass --chrome PATH")


def pdf_text_string(value):
    """A PDF text string in UTF-16BE with its byte-order mark, as hex."""
    return "<FEFF" + value.encode("utf-16-be").hex().upper() + ">"


def set_title(pdf_path, title):
    """Append an incremental update: a new Info dictionary with the title (keeping
    Chrome's creator, producer and dates). Readers use the last trailer."""
    data = pdf_path.read_bytes()
    trailer = data[data.rfind(b"trailer"):]
    size = int(re.search(rb"/Size (\d+)", trailer).group(1))
    root = re.search(rb"/Root (\d+) 0 R", trailer).group(1).decode()
    info = re.search(rb"/Info (\d+) 0 R", trailer)
    old_info = {}
    if info:
        m = re.search(rb"\n" + info.group(1) + rb" 0 obj\s*<<(.*?)>>\s*endobj", data, re.S)
        if m:
            for key in (b"Creator", b"Producer", b"CreationDate", b"ModDate"):
                v = re.search(rb"/" + key + rb"\s*(\([^)]*\)|<[0-9A-Fa-f]*>)", m.group(1))
                if v:
                    old_info[key.decode()] = v.group(1).decode("latin-1")
    xref_prev = int(re.findall(rb"startxref\s+(\d+)", data)[-1])
    body = [f"/Title {pdf_text_string(title)}"] + [f"/{k} {v}" for k, v in old_info.items()]
    obj = f"{size} 0 obj\n<< {' '.join(body)} >>\nendobj\n".encode("latin-1")
    offset = len(data) + 1  # after the newline below
    xref = f"xref\n{size} 1\n{offset:010d} 00000 n \n".encode()
    xref_at = offset + len(obj)
    tail = (f"trailer\n<< /Size {size + 1} /Root {root} 0 R /Info {size} 0 R /Prev {xref_prev} >>\n"
            f"startxref\n{xref_at}\n%%EOF\n").encode()
    pdf_path.write_bytes(data + b"\n" + obj + xref + tail)


def check(pdf_path, lang):
    """The checks that fail the deploy. Returns a one-line summary."""
    if not pdf_path.exists():
        raise CVError(f"{pdf_path.name}: not written")
    data = pdf_path.read_bytes()
    kb = len(data) / 1024
    pages = len(re.findall(rb"/Type\s*/Page(?![s\w])", data))
    images = len(re.findall(rb"/Subtype\s*/Image", data))
    has_lang = re.search(rb"/Lang\s*\(" + lang.encode() + rb"\)", data) is not None
    has_title = pdf_text_string(TITLE).encode() in data
    problems = []
    if kb >= MAX_KB:
        problems.append(f"weighs {kb:.0f} KB (limit {MAX_KB} KB)")
    if not 1 <= pages <= MAX_PAGES:
        problems.append(f"has {pages} pages (at most {MAX_PAGES})")
    if lang in WITH_PHOTO and images < 1:
        problems.append("has no photo, and the Spanish and French CVs carry one")
    if lang not in WITH_PHOTO and images > 0:
        problems.append(f"has {images} image(s), and the English CV goes without the photo")
    if not has_lang:
        problems.append(f"its language is not set to {lang!r}")
    if not has_title:
        problems.append("its title is not set")
    if problems:
        raise CVError(f"{pdf_path.name}: " + "; ".join(problems))
    return f"{pdf_path.relative_to(ROOT).as_posix()}  {kb:.0f} KB, {pages} pages, {images} image(s), lang {lang}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chrome")
    args = ap.parse_args()
    chrome = find_chrome(args.chrome)
    if not (DIST / "index.html").exists():
        raise CVError("dist/ is empty: run python tools/build.py first")
    site = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(DIST)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    sandbox = ["--no-sandbox"] if sys.platform.startswith("linux") and os.environ.get("CI") else []
    try:
        with tempfile.TemporaryDirectory() as profile:
            for language in site["languages"]:
                code = language["code"]
                out = OUT / f"cv-santiago-die-{code}.pdf"
                url = f"http://127.0.0.1:{port}/{language['path']}"
                cmd = [chrome, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
                       *sandbox, f"--user-data-dir={profile}", "--run-all-compositor-stages-before-draw",
                       "--virtual-time-budget=8000", "--no-pdf-header-footer", f"--print-to-pdf={out}", url]
                done = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=180)
                if done.returncode != 0 or not out.exists():
                    raise CVError(f"Chrome could not print {url} (exit {done.returncode}): "
                                  + done.stderr.decode(errors="replace")[-400:])
                set_title(out, TITLE)
                print(check(out, code))
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    try:
        main()
    except CVError as error:
        sys.exit(f"make_cv: {error}")
