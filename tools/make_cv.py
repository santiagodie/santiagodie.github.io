"""Make the CV PDFs (one per language) from the built site, with the system's Chrome.

Development script, not part of the build or the workflow: run it after
`python tools/build.py` whenever the content changes, and commit the PDFs. Standard
library only. It serves dist/ on a local port for the time it takes, prints each
language page with css/print.css (Chrome headless, A4, no header or footer), then
sets the PDF's title ("Santiago Die Morejón · CV") with an incremental update, which
leaves Chrome's own bytes untouched.

Usage: python tools/make_cv.py [--chrome PATH]
Writes assets/cv/cv-santiago-die-{en,es,fr}.pdf (copied to dist/ by the build).
"""
import argparse
import functools
import http.server
import json
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
OUT = ROOT / "assets" / "cv"
TITLE = "Santiago Die Morejón · CV"
CHROMES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "google-chrome", "chromium", "chrome",
]


def find_chrome(given):
    for candidate in ([given] if given else []) + CHROMES:
        path = shutil.which(candidate) or (candidate if Path(candidate).exists() else None)
        if path:
            return path
    sys.exit("make_cv: Chrome not found (use --chrome PATH)")


def pdf_text_string(value):
    """A PDF text string in UTF-16BE with its byte-order mark, as hex."""
    return "<FEFF" + value.encode("utf-16-be").hex().upper() + ">"


def set_title(pdf_path, title, lang):
    """Append an incremental update: a new Info dictionary with the title (keeping
    Chrome's creator, producer and dates). Readers use the last trailer. Returns
    whether Chrome already set the document language (/Lang)."""
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
    return re.search(rb"/Lang\s*\(" + lang.encode(), data) is not None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chrome")
    args = ap.parse_args()
    chrome = find_chrome(args.chrome)
    if not (DIST / "index.html").exists():
        sys.exit("make_cv: build the site first (python tools/build.py)")
    site = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
    OUT.mkdir(parents=True, exist_ok=True)

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *args):
            pass

    handler = functools.partial(Quiet, directory=str(DIST))
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    port = server.server_address[1]
    try:
        with tempfile.TemporaryDirectory() as profile:
            for language in site["languages"]:
                code = language["code"]
                out = OUT / f"cv-santiago-die-{code}.pdf"
                url = f"http://127.0.0.1:{port}/{language['path']}"
                cmd = [chrome, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
                       f"--user-data-dir={profile}", "--run-all-compositor-stages-before-draw",
                       "--virtual-time-budget=8000", "--no-pdf-header-footer", f"--print-to-pdf={out}", url]
                subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
                has_lang = set_title(out, TITLE, code)
                print(f"{out.relative_to(ROOT).as_posix()}  {out.stat().st_size / 1024:.0f} KB"
                      f"  lang {code}: {'yes' if has_lang else 'NOT SET by Chrome'}")
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    main()
