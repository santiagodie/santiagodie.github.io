"""Make the CV PDFs (one A4 page per language) with Chrome, in the Harvard layout.

Runs at every deploy, right after `python tools/build.py` (and locally the same way).
Standard library only. The CV is not a print of the page: it has its own template (here)
and stylesheet (tools/cv/cv.css), but every fact comes from the same files as the site,
so a change on the site reaches the CV at the next deploy:

  name, email, profiles, address   data/site.json
  experience, education, skills,   i18n/<lang>.json (experience.items, education.items,
  languages, certifications        education.certifications, skills)
  projects                         data/projects.json (the featured ones, in order)
  the CV's own texts               i18n/<lang>.json under cv.*: summary, the bullets of
                                   each experience (cv.experience.<id>.bullets) and
                                   project (cv.projects.<id>.bullets), cv.education
                                   (honours, places), cv.nationality, section labels.
                                   A missing or empty one falls back to the site's text.
                                   A leading "TODO:" (wording not yet approved) is
                                   printed without the marker and listed in the log.

The phone number is only in the CV: it comes from the CV_PHONE environment variable
(locally, Santiago's environment; in CI, the GitHub Actions secret CV_PHONE, passed only
to the "Make the CV (PDF)" step). Without it the CV goes without a phone and the log
says so. The intermediate page, the only file with the number besides the PDFs, is
written to a temporary folder outside dist/ and deleted when the script ends.

Each page is a self-contained HTML file (fonts and photo inlined), printed by Chrome
headless (A4, no header or footer) to dist/cv/CV-SantiagoDie-{EN,ES,FR}.pdf. The PDF's
title is set with an incremental update (Chrome's own bytes are left untouched).

Checks, any failure exits non-zero and fails the deploy: exactly one page; under 300 KB;
a photo in the Spanish and French CVs and none in the English one; the title and the
language set; the links present (site, LinkedIn, GitHub, email, projects, and the phone
when there is one); with CV_PHONE, the number appears in no other file of dist/. When
pdftotext is installed, the text layer is read back too (name, email and the section
titles in order), as an ATS would read it.

Usage: python tools/make_cv.py [--chrome PATH] [--only LANG]
"""
import argparse
import base64
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DIST = ROOT / "dist"
OUT = DIST / "cv"
CSS = ROOT / "tools" / "cv" / "cv.css"
FONTS = [  # (family, weight, style, file in fonts/print/): STIX Two Text, the template's face
    ("STIX Two Text", "400", "normal", "stix-two-text-regular.woff2"),
    ("STIX Two Text", "400", "italic", "stix-two-text-italic.woff2"),
    ("STIX Two Text", "700", "normal", "stix-two-text-bold.woff2"),
]
TITLE = "Santiago Die Morejón · CV"
MAX_KB = 300
PAGES = 1
WITH_PHOTO = {"es", "fr"}  # owner's decision: the English CV goes without the photo
# Skill groups on the CV, by position in i18n skills.groups (the site's order): ML and
# deep learning, MLOps and DevOps, data, vision/language/LLM, other languages. The rest
# (knowledge management, backend, frontend, other, quantum) stay on the site only.
SKILL_GROUPS = [0, 1, 2, 3, 7]
TODO = re.compile(r"^TODO\s*:?\s*")
CHROMES = [
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
]


class CVError(Exception):
    pass


def file_name(code):
    return f"CV-SantiagoDie-{code.upper()}.pdf"


def find_chrome(given):
    for candidate in ([given] if given else []) + CHROMES:
        path = shutil.which(candidate) or (candidate if Path(candidate).exists() else None)
        if path:
            return path
    raise CVError("Chrome not found (tried google-chrome, chromium and the usual paths); "
                  "install it or pass --chrome PATH")


def load(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


# Content ------------------------------------------------------------------

class Texts:
    """The CV's own texts, with the site's as fallback; remembers what is still TODO."""

    def __init__(self, lang):
        self.lang = lang
        self.pending = []

    def take(self, value, where):
        value = str(value or "").strip()
        if TODO.match(value):
            self.pending.append(where)
            value = TODO.sub("", value)
        return value

    def bullets(self, values, fallback, where):
        lines = [self.take(v, f"{where}[{i}]") for i, v in enumerate(values or [])]
        lines = [line for line in lines if line]
        return lines or ([fallback] if fallback else [])


def esc(value):
    return html.escape(str(value), quote=True)


def short_url(url):
    return re.sub(r"^https?://(www\.)?", "", url).rstrip("/")


def years(period):
    """"2021 – 2027" -> "2021–2027"; "Promoción 2020" -> "2020"."""
    found = re.findall(r"\d{4}", period)
    return "–".join(found) if found else period


def contact_items(site, s, lang, phone):
    person = site["person"]
    parts = [p.strip() for p in s["contact"]["location"].split(",")]
    location = ", ".join([parts[0], parts[-1]]) if len(parts) > 1 else parts[0]
    page = site["url"] + next(l["path"] for l in site["languages"] if l["code"] == lang)
    items = [(None, location),
             (page, short_url(site["url"])),
             (person["linkedin"], short_url(person["linkedin"])),
             (person["github"], short_url(person["github"]))]
    if phone:
        items.append(("tel:" + re.sub(r"[^\d+]", "", phone), phone))
    items.append(("mailto:" + person["email"], person["email"]))
    return items


def project_link(project):
    demo = project.get("demo")
    if isinstance(demo, dict) and demo.get("type") == "web":
        return demo["url"]
    for part in project.get("parts", []):
        if part.get("demo", {}).get("type") == "web":
            return part["demo"]["url"]
    return project["repo"]


def render_html(site, s, projects, lang, phone, t):
    cv = s["cv"]
    labels = cv["labels"]
    colon = " : " if lang == "fr" else ": "  # French puts a space before the colon
    out = []

    # Head
    contact = ' <span class="sep">•</span> '.join(
        f'<span><a href="{esc(href)}">{esc(shown)}</a></span>' if href else f"<span>{esc(shown)}</span>"
        for href, shown in contact_items(site, s, lang, phone))
    photo = ""
    if lang in WITH_PHOTO:
        data = base64.b64encode((ROOT / site["person"]["image"]).read_bytes()).decode()
        photo = f'<img class="photo" src="data:image/jpeg;base64,{data}" alt="{esc(s["contact"]["photoAlt"])}">'
    out.append(f'<header class="head"><div class="head__text"><h1 class="name">{esc(site["person"]["name"])}</h1>'
               f'<p class="contact">{contact}</p></div>{photo}</header>')
    summary = t.take(cv.get("summary"), "cv.summary") or t.take(cv.get("profile"), "cv.profile")
    out.append(f'<p class="summary">{esc(summary)}</p>')

    # Experience
    rows = []
    for item in s["experience"]["items"]:
        if TODO.match(str(item.get("title", ""))):
            continue
        own = cv.get("experience", {}).get(item["id"], {})
        lines = t.bullets(own.get("bullets"), t.take(item.get("text"), f"experience.{item['id']}.text"),
                          f"cv.experience.{item['id']}.bullets")
        rows.append(f'<div class="entry"><div class="row"><b>{esc(item["org"])}</b><b>{esc(item["place"])}</b></div>'
                    f'<div class="row"><span>{esc(item["title"])}</span><span class="date">{esc(item["period"])}</span></div>'
                    + "<ul>" + "".join(f"<li>{esc(line)}</li>" for line in lines) + "</ul></div>")
    if rows:
        out.append(f'<section><h2>{esc(labels["experience"])}</h2>{"".join(rows)}</section>')

    # Projects: the featured ones
    rows = []
    for project in projects:
        if not project.get("featured"):
            continue
        own = cv.get("projects", {}).get(project["id"], {})
        lines = t.bullets(own.get("bullets"), project["description"][lang], f"cv.projects.{project['id']}.bullets")
        link = project_link(project)
        rows.append(f'<div class="entry"><div class="row"><b>{esc(project["title"][lang])}</b>'
                    f'<a class="link" href="{esc(link)}">{esc(short_url(link))}</a></div>'
                    + "<ul>" + "".join(f"<li>{esc(line)}</li>" for line in lines) + "</ul></div>")
    if rows:
        out.append(f'<section><h2>{esc(labels["projects"])}</h2>{"".join(rows)}</section>')

    # Education
    rows = []
    places = cv["education"]["places"]
    for index, item in enumerate(s["education"]["items"]):
        place = places[index] if index < len(places) else ""
        org = item["org"]
        city = place.split(",")[0].strip()
        if city and org.endswith(", " + city):
            org = org[: -len(", " + city)]
        title = item["title"]
        if ":" in item.get("text", ""):  # "Mención en Gestión del Conocimiento: ..."
            track = item["text"].split(":")[0].strip()
            title += ", " + track[:1].lower() + track[1:]
        period = years(item["period"])
        end = re.findall(r"\d{4}", period)
        if end and int(end[-1]) > date.today().year - (date.today().month < 7):
            period += f' ({cv["education"]["expected"]})'
        honors = t.take(cv["education"].get("honors"), "cv.education.honors") if index == 0 else ""
        extra = f'<div class="row"><span>{esc(labels["honors"])}{colon}{esc(honors)}</span><span></span></div>' if honors else ""
        rows.append(f'<div class="entry"><div class="row"><b>{esc(org)}</b><b>{esc(place)}</b></div>'
                    f'<div class="row"><span>{esc(title)}</span><span class="date">{esc(period)}</span></div>{extra}</div>')
    out.append(f'<section><h2>{esc(labels["education"])}</h2>{"".join(rows)}</section>')

    # Additional skills: technical groups, languages, certifications, nationality
    groups = s["skills"]["groups"]
    lines = []
    for index in SKILL_GROUPS:
        if index < len(groups):
            group = groups[index]
            items = [i for i in group["items"] if i and not TODO.match(i)]
            if items:
                lines.append(f'{group["name"]}{colon}{", ".join(items)}')
    spoken = s["skills"]["languages"]
    lines.append(f'{spoken["title"]}{colon}' + ", ".join(f'{l["name"]} ({l["level"]})' for l in spoken["items"]))
    certs = s["education"]["certifications"]
    if certs["items"]:
        lines.append(f'{certs["title"]}{colon}' + (" ; " if lang == "fr" else "; ").join(certs["items"]))
    nationality = t.take(cv.get("nationality"), "cv.nationality")
    if nationality:
        lines.append(f'{cv["nationalityLabel"]}{colon}{nationality}')
    out.append(f'<section class="skills"><h2>{esc(labels["skills"])}</h2><ul>'
               + "".join(f"<li>{esc(line)}</li>" for line in lines) + "</ul></section>")

    faces = "\n".join(
        f'@font-face {{ font-family: "{family}"; font-weight: {weight}; font-style: {style}; '
        f'src: url(data:font/woff2;base64,{base64.b64encode((ROOT / "fonts" / "print" / name).read_bytes()).decode()}) format("woff2"); }}'
        for family, weight, style, name in FONTS)
    css = CSS.read_text(encoding="utf-8")
    return (f'<!doctype html>\n<html lang="{lang}">\n<head>\n<meta charset="utf-8">\n<title>{esc(TITLE)}</title>\n'
            f'<style>\n{faces}\n{css}</style>\n</head>\n<body>\n<main>\n' + "\n".join(out) + "\n</main>\n</body>\n</html>\n")


def expected_links(site, s, projects, lang, phone):
    links = [href for href, _ in contact_items(site, s, lang, phone) if href]
    links += [project_link(p) for p in projects if p.get("featured")]
    return links


# PDF ----------------------------------------------------------------------

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


def pdf_uris(data):
    found = set()
    for raw in re.findall(rb"/URI\s*\(((?:\\.|[^\\)])*)\)", data):
        found.add(re.sub(rb"\\(.)", rb"\1", raw).decode("latin-1"))
    return found


def read_text(pdf_path):
    tool = shutil.which("pdftotext")
    if not tool:
        return None
    done = subprocess.run([tool, "-enc", "UTF-8", str(pdf_path), "-"], capture_output=True, timeout=60)
    return done.stdout.decode("utf-8", errors="replace") if done.returncode == 0 else None


def check(pdf_path, lang, links, headings, name, email):
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
    if pages != PAGES:
        problems.append(f"has {pages} pages (it must have exactly {PAGES})")
    if lang in WITH_PHOTO and images < 1:
        problems.append("has no photo, and the Spanish and French CVs carry one")
    if lang not in WITH_PHOTO and images > 0:
        problems.append(f"has {images} image(s), and the English CV goes without the photo")
    if not has_lang:
        problems.append(f"its language is not set to {lang!r}")
    if not has_title:
        problems.append("its title is not set")
    missing = [link for link in links if link not in pdf_uris(data)]
    if missing:
        problems.append("links missing: " + ", ".join(missing))
    text = read_text(pdf_path)
    reading = "text layer not read (no pdftotext)"
    if text is not None:
        flat = re.sub(r"\s+", " ", text)
        for needed in (name, email):
            if needed not in flat:
                problems.append(f"the text layer has no {needed!r}")
        at = 0  # the titles are printed in capitals; each one after the previous
        for heading in headings:
            at = flat.find(heading.upper(), at)
            if at < 0:
                problems.append("the section titles are not in the text layer in order")
                break
        reading = "text layer in order"
    if problems:
        raise CVError(f"{pdf_path.name}: " + "; ".join(problems))
    return (f"{pdf_path.relative_to(ROOT).as_posix()}  {kb:.0f} KB, {pages} page, {images} image(s), "
            f"lang {lang}, {len(links)} links, {reading}")


def phone_elsewhere(phone, written):
    """Files of dist/ (other than the CVs) that contain the phone number, in any spacing."""
    digits = re.sub(r"\D", "", phone)
    forms = {phone.encode(), digits.encode()}
    if len(digits) > 9:
        forms.add(digits[-9:].encode())  # without the country code
    hits = []
    for path in DIST.rglob("*"):
        if path.is_file() and path not in written:
            data = path.read_bytes()
            if any(form in data for form in forms):
                hits.append(path.relative_to(ROOT).as_posix())
    return hits


def warn(message):
    if os.environ.get("GITHUB_ACTIONS"):
        print(f"::warning title=CV::{message}")
    else:
        print(f"make_cv: warning: {message}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chrome")
    ap.add_argument("--only", help="make only this language (for local checks)")
    args = ap.parse_args()
    chrome = find_chrome(args.chrome)
    if not (DIST / "index.html").exists():
        raise CVError("dist/ is empty: run python tools/build.py first")
    site = load("data/site.json")
    projects = load("data/projects.json")["projects"]
    phone = os.environ.get("CV_PHONE", "").strip()
    if not phone:
        warn("CV_PHONE is not set: the CV goes without a phone number")
    OUT.mkdir(parents=True, exist_ok=True)
    all_codes = [l["code"] for l in site["languages"]]
    codes = [code for code in all_codes if not args.only or code == args.only]
    names = {file_name(code) for code in all_codes}
    for old in OUT.glob("*.pdf"):  # earlier names (cv-santiago-die-xx.pdf) are removed
        if old.name not in names:
            old.unlink()
    sandbox = ["--no-sandbox"] if sys.platform.startswith("linux") and os.environ.get("CI") else []
    written = set()
    work = Path(tempfile.mkdtemp(prefix="sd-cv-"))  # outside dist/, deleted below
    try:
        for code in codes:
            s = load(f"i18n/{code}.json")
            t = Texts(code)
            page = work / f"cv-{code}.html"
            page.write_text(render_html(site, s, projects, code, phone, t), encoding="utf-8")
            out = OUT / file_name(code)
            cmd = [chrome, "--headless=new", "--disable-gpu", "--no-first-run", "--no-default-browser-check",
                   *sandbox, f"--user-data-dir={work / ('profile-' + code)}", "--run-all-compositor-stages-before-draw",
                   "--virtual-time-budget=5000", "--no-pdf-header-footer", f"--print-to-pdf={out}", page.as_uri()]
            try:
                done = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, timeout=180)
            finally:
                page.unlink(missing_ok=True)
            if done.returncode != 0 or not out.exists():
                raise CVError(f"Chrome could not print the {code} CV (exit {done.returncode}): "
                              + done.stderr.decode(errors="replace")[-400:])
            set_title(out, TITLE)
            written.add(out)
            labels = s["cv"]["labels"]
            headings = [labels[k] for k in ("experience", "projects", "education", "skills")]
            print(check(out, code, expected_links(site, s, projects, code, phone), headings,
                        site["person"]["name"], site["person"]["email"]))
            if t.pending:
                print(f"  {code}: wording still marked TODO (printed as is): {', '.join(t.pending)}")
        if phone:
            hits = phone_elsewhere(phone, written)
            if hits:
                raise CVError("the phone number is in files of dist/ other than the CV: " + ", ".join(hits))
            print("phone: in the CVs only")
    finally:
        shutil.rmtree(work, ignore_errors=True)


if __name__ == "__main__":
    try:
        main()
    except CVError as error:
        sys.exit(f"make_cv: {error}")
