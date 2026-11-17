"""Make the link-preview images (Open Graph), one per language, 1200x627.

What LinkedIn and others show when the site is shared: the monogram, the name, the
headline (the hero's role line, `hero.role` in i18n) and the domain, in the site's
palette and fonts (the local woff2 files), large enough to read in a phone feed
(about 400px wide, a third of the size). Standard library and the system's Chrome
(found as in tools/make_cv.py); deterministic, so the PNGs are committed and the build
only copies them.

Run by hand after the headline changes:  python tools/make_og.py [--out DIR]
Writes og-image.png (English), og-image-es.png and og-image-fr.png.
After publishing, refresh LinkedIn's copy with its Post Inspector.
"""
import argparse
import html
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from make_cv import CVError, find_chrome  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
W, H = 1200, 627
TODO = re.compile(r"^TODO:?\s*")
MONOGRAM = ('<path d="M190 38 H66 A36.0 36.0 0 0 0 66 110 H160 A54.0 54.0 0 0 1 160 218 M24 218 H190 '
            'A90.0 90.0 0 0 0 190 38 M120 38 V80 M120 140 V218"/>')


def page(name, headline, domain):
    font = lambda f: (ROOT / "fonts" / f).as_uri()
    first, _, rest = name.partition(" ")
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face {{ font-family: Hubot; src: url("{font('hubot-sans.woff2')}"); font-weight: 200 900; font-stretch: 75% 125%; }}
@font-face {{ font-family: Mona; src: url("{font('mona-sans.woff2')}"); font-weight: 200 900; }}
@font-face {{ font-family: Mono; src: url("{font('jetbrains-mono.woff2')}"); font-weight: 100 800; }}
html, body {{ margin: 0; width: {W}px; height: {H}px; overflow: hidden; background: #f5f0e1; }}
body {{ position: relative; color: #0b1f3a; }}
.frame {{ position: absolute; inset: 26px; border: 2px solid rgb(201 162 39 / 0.75); border-radius: 18px; }}
.text {{ position: absolute; left: 84px; top: 74px; width: 730px; }}
h1 {{ margin: 0; font: 750 104px/0.92 Hubot; font-stretch: 112%; letter-spacing: -0.035em; }}
p {{ margin: 34px 0 0; max-width: 700px; color: rgb(11 31 58 / 0.86); font: 520 44px/1.2 Mona; letter-spacing: -0.01em; }}
.url {{ position: absolute; left: 84px; bottom: 66px; color: rgb(11 31 58 / 0.74); font: 500 28px Mono; }}
.rule {{ position: absolute; left: 872px; top: 84px; bottom: 84px; width: 2px; background: rgb(201 162 39 / 0.55); }}
svg {{ position: absolute; left: 920px; top: 50%; width: 220px; transform: translateY(-50%); }}
</style></head><body>
<div class="frame"></div>
<div class="text"><h1>{html.escape(first)}<br>{html.escape(rest)}</h1><p>{html.escape(headline)}</p></div>
<div class="url">{html.escape(domain)}</div>
<div class="rule"></div>
<svg viewBox="10 24 290 208" fill="none" stroke="#c9a227" stroke-width="20" stroke-linejoin="round">{MONOGRAM}</svg>
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT))
    ap.add_argument("--chrome")
    args = ap.parse_args()
    chrome = find_chrome(args.chrome)
    site = json.loads((ROOT / "data" / "site.json").read_text(encoding="utf-8"))
    name = site["person"]["name"]
    domain = re.sub(r"^https?://|/$", "", site["url"])
    out = Path(args.out).resolve()  # Chrome writes relative to its own directory
    with tempfile.TemporaryDirectory(ignore_cleanup_errors=True) as tmp:
        for language in site["languages"]:
            code = language["code"]
            strings = json.loads((ROOT / "i18n" / f"{code}.json").read_text(encoding="utf-8"))
            headline = TODO.sub("", strings["hero"]["role"])
            src = Path(tmp) / f"og-{code}.html"
            src.write_text(page(name, headline, domain), encoding="utf-8")
            png = out / ("og-image.png" if code == "en" else f"og-image-{code}.png")
            cmd = [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--no-first-run",
                   f"--user-data-dir={Path(tmp) / 'profile'}", "--force-device-scale-factor=1",
                   f"--window-size={W},{H}", "--virtual-time-budget=3000", f"--screenshot={png}", src.as_uri()]
            done = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=120)
            if done.returncode or not png.exists():
                raise CVError(f"Chrome could not draw {png.name}: " + done.stderr.decode(errors="replace")[-300:])
            print(f"{png.name}: {headline}")


if __name__ == "__main__":
    try:
        main()
    except CVError as error:
        sys.exit(f"make_og: {error}")
