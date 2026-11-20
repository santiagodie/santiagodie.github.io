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
                                   (places; titles, where the CV names an entry
                                   otherwise), cv.nationality, section labels. The
                                   thesis and honours come from the site's Education
                                   entry (education.items[].thesis, .honors).
                                   A missing or empty one falls back to the site's text.
                                   A leading "TODO:" (wording not yet approved) is
                                   printed without the marker and listed in the log.

The phone number is only in the CV: it comes from the CV_PHONE environment variable
(locally, Santiago's environment; in CI, the GitHub Actions secret CV_PHONE, passed only
to the "Make the CV (PDF)" step), and a Spanish number is printed as +34 ddd dd dd dd.
Without it the CV goes without a phone and the log says so. The intermediate page, the only file with the number besides the PDFs, is
written to a temporary folder outside dist/ and deleted when the script ends.

Each page is a self-contained HTML file (fonts and photo inlined), printed by Chrome
headless (A4, no header or footer) to dist/cv/CV-SantiagoDie-{EN,ES,FR}.pdf. The PDF's
Info dictionary (title, author, subject, creator, producer, dates) is written from scratch
in an incremental update (Chrome's own bytes are left untouched; its Info, whose Creator
is a user agent full of parentheses, is not reused).

Checks, any failure exits non-zero and fails the deploy: exactly one page; under 300 KB;
a photo in the Spanish and French CVs and none in the English one; the title and the
language set; the links present (site, LinkedIn, email, projects, and the phone when
there is one; with a phone, the text layer must carry it, logged as yes/no only); the last Info dictionary read back by a small parser (every string
and the dictionary closed, each field as written); with CV_PHONE, the number appears in
no other file of dist/. When pdftotext is installed, the text layer is read back too
(name, email and the section titles in order), as an ATS would read it. When qpdf is
installed, `qpdf --check` must report 0 warnings (without it the check is skipped and
the log says so). In CI (the CI variable set) both tools are required: the workflows
install qpdf and poppler-utils, and a missing one fails the run.

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
from datetime import date, datetime, timezone
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
AUTHOR = "Santiago Die Morejón"
SUBJECT = {"en": "Curriculum vitae", "es": "Currículum vítae", "fr": "Curriculum vitae"}
CREATOR = "santiagodie.com · make_cv.py"
PRODUCER = "Skia/PDF (Chrome headless), Info by make_cv.py"
MAX_KB = 300
PAGES = 1
WITH_PHOTO = {"es", "fr"}  # owner's decision: the English CV goes without the photo
# Skill groups on the CV, by position in i18n skills.groups (the site's order; lot 22):
# language and LLMs, computer vision, ML and data, backend and deployment, other
# languages, AI-assisted development: the six the site shows before "More skills". The
# rest (frontend, models and demos, knowledge management, coursework languages, other,
# quantum) stay on the site only.
SKILL_GROUPS = [0, 1, 2, 3, 4, 5]
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
    # Lot 22 (owner): the head keeps the site and LinkedIn; GitHub and Hugging Face stay
    # on the site (Contact, sameAs) and in the projects' links.
    items = [(None, location),
             (page, short_url(site["url"])),
             (person["linkedin"], short_url(person["linkedin"]))]
    if phone:
        items.append(("tel:" + re.sub(r"[^\d+]", "", phone), format_phone(phone)))
    items.append(("mailto:" + person["email"], person["email"]))
    return items


def format_phone(phone):
    """A Spanish number (9 digits, with or without +34) as "+34 ddd dd dd dd"; any other
    number as given."""
    raw = re.sub(r"[\s().-]", "", phone)
    match = re.fullmatch(r"(?:\+34|0034)?(\d{9})", raw)
    if not match:
        return phone
    d = match.group(1)
    return f"+34 {d[:3]} {d[3:5]} {d[5:7]} {d[7:]}"


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
    summary = t.take(cv.get("summary"), "cv.summary")
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
    # Lot 23: cv.education.titles, where a CV entry names its title otherwise than the
    # site (the Baccalauréat with its series); an empty string keeps the site's title.
    titles = cv["education"].get("titles", [])
    for index, item in enumerate(s["education"]["items"]):
        place = places[index] if index < len(places) else ""
        org = item["org"]
        city = place.split(",")[0].strip()
        if city and org.endswith(", " + city):
            org = org[: -len(", " + city)]
        title = (titles[index] if index < len(titles) else "") or item["title"]
        if ":" in item.get("text", ""):  # "Mención en Gestión del Conocimiento: ..."
            track = item["text"].split(":")[0].strip()
            # In English the specialisation keeps its capitals ("Knowledge Management
            # specialisation"); in Spanish and French it follows the comma in lower case.
            title += ", " + (track if lang == "en" else track[:1].lower() + track[1:])
        period = years(item["period"])  # lot 22: no "(expected)" after the end year
        # Lot 22: the thesis and the honours, from the site's own Education entry.
        thesis = t.take(item.get("thesis"), f"education.items[{index}].thesis")
        honors = t.take(item.get("honors"), f"education.items[{index}].honors")
        extra = f'<div class="row"><span>{esc(thesis)}</span><span></span></div>' if thesis else ""
        if honors:
            extra += f'<div class="row"><span>{esc(labels["honors"])}{colon}{esc(honors)}</span><span></span></div>'
        rows.append(f'<div class="entry"><div class="row"><b>{esc(org)}</b><b>{esc(place)}</b></div>'
                    f'<div class="row"><span>{esc(title)}</span><span class="date">{esc(period)}</span></div>{extra}</div>')
    out.append(f'<section><h2>{esc(labels["education"])}</h2>{"".join(rows)}</section>')

    # Skills: technical groups, languages, certifications, nationality
    groups = s["skills"]["groups"]
    lines = []
    for index in SKILL_GROUPS:
        if index < len(groups):
            group = groups[index]
            items = [i for i in group["items"] if i and not TODO.match(i)]
            if items:
                lines.append(f'{group["name"]}{colon}{", ".join(items)}')
    spoken = s["skills"]["languages"]
    # Lot 23: on one line, "Languages: Spanish (native), French (...)". A level that
    # brings its own note, "bilingual (educated in ...)", loses those parentheses here
    # ("French (bilingual, educated in ...)"), so they do not nest. In Spanish and
    # French a language name is lower case after the colon.
    def spoken_item(l):
        name = l["name"] if lang == "en" else l["name"][:1].lower() + l["name"][1:]
        level = l["level"]
        if level.endswith(")") and " (" in level:
            level = level[:-1].replace(" (", ", ", 1)
        return f"{name} ({level})"
    lines.append(f'{spoken["title"]}{colon}' + ", ".join(spoken_item(l) for l in spoken["items"]))
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


def pdf_literal(value):
    """A PDF literal string, with backslash and both parentheses escaped. Plain ASCII
    only; anything else goes as a hex UTF-16 string (pdf_text_string)."""
    if not value.isascii():
        return pdf_text_string(value)
    return "(" + value.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)") + ")"


def pdf_date(moment):
    return moment.strftime("D:%Y%m%d%H%M%SZ")


def info_fields(lang, created):
    """The whole Info dictionary, written from scratch: nothing of Chrome's is copied
    (its Creator, a user agent full of parentheses, is what broke the dictionary)."""
    now = pdf_date(datetime.now(timezone.utc))
    return {
        "Title": TITLE,
        "Author": AUTHOR,
        "Subject": SUBJECT[lang],
        "Creator": CREATOR,
        "Producer": PRODUCER,
        "CreationDate": created or now,
        "ModDate": now,
    }


def set_info(pdf_path, lang):
    """Append an incremental update with a new Info dictionary (Chrome's bytes are left
    untouched; readers use the last trailer). It takes the number of Chrome's Info
    object, so that one is superseded and the file holds a single live Info. Chrome's
    creation date is kept if it can be read cleanly."""
    data = pdf_path.read_bytes()
    trailer = data[data.rfind(b"trailer"):]
    size = int(re.search(rb"/Size (\d+)", trailer).group(1))
    root = re.search(rb"/Root (\d+) 0 R", trailer).group(1).decode()
    chrome_info = re.search(rb"/Info (\d+) 0 R", trailer)
    number = int(chrome_info.group(1)) if chrome_info else size
    created = None
    try:
        old = read_info(data)
        if re.fullmatch(r"D:\d{4,14}.*", old.get("CreationDate", "")):
            created = old["CreationDate"]
    except CVError:
        pass  # Chrome's dictionary is replaced anyway
    xref_prev = int(re.findall(rb"startxref\s+(\d+)", data)[-1])
    body = [f"/{key} {pdf_literal(value)}" for key, value in info_fields(lang, created).items()]
    obj = f"{number} 0 obj\n<< {' '.join(body)} >>\nendobj\n".encode("ascii")
    offset = len(data) + 1  # after the newline below
    xref = f"xref\n{number} 1\n{offset:010d} 00000 n \n".encode()
    xref_at = offset + len(obj)
    tail = (f"trailer\n<< /Size {max(size, number + 1)} /Root {root} 0 R /Info {number} 0 R /Prev {xref_prev} >>\n"
            f"startxref\n{xref_at}\n%%EOF\n").encode()
    pdf_path.write_bytes(data + b"\n" + obj + xref + tail)


# A minimal reader for the Info dictionary, standard library only. It walks the last
# /Info object token by token, so an unclosed string or dictionary is an error here
# instead of a PdfStreamError in the ATS that reads the CV.

DELIMS = b"()<>[]{}/%"
SPACE = b" \t\r\n\f\0"
ESCAPES = {ord("n"): b"\n", ord("r"): b"\r", ord("t"): b"\t", ord("b"): b"\b", ord("f"): b"\f"}


def _literal(data, i):
    """data[i] is "(": returns (bytes, index after the closing ")")."""
    out, depth, i = bytearray(), 1, i + 1
    while i < len(data):
        c = data[i]
        if c == 0x5C:  # backslash
            i += 1
            if i >= len(data):
                break
            e = data[i]
            if e in ESCAPES:
                out += ESCAPES[e]
            elif 0x30 <= e <= 0x37:
                j = i
                while j < len(data) and j < i + 3 and 0x30 <= data[j] <= 0x37:
                    j += 1
                out.append(int(data[i:j], 8) & 0xFF)
                i = j - 1
            elif e in b"\r\n":  # line continuation
                if e == 0x0D and data[i + 1:i + 2] == b"\n":
                    i += 1
            else:
                out.append(e)
        elif c == 0x28:
            depth += 1
            out.append(c)
        elif c == 0x29:
            depth -= 1
            if depth == 0:
                return bytes(out), i + 1
            out.append(c)
        else:
            out.append(c)
        i += 1
    raise CVError("an Info string opens and never closes")


def _decode(raw):
    if raw[:2] == b"\xfe\xff":
        return raw[2:].decode("utf-16-be")
    return raw.decode("latin-1")


def read_info(data):
    """The last trailer's Info dictionary as {key: text}. Raises CVError when its strings
    or the dictionary itself are not closed, or when a key has no value."""
    trailer = data[data.rfind(b"trailer"):]
    ref = re.search(rb"/Info\s+(\d+)\s+(\d+)\s+R", trailer)
    if not ref:
        raise CVError("the trailer has no /Info")
    starts = list(re.finditer(rb"(?<![0-9])" + ref.group(1) + rb"\s+" + ref.group(2) + rb"\s+obj", data))
    if not starts:
        raise CVError(f"the Info object {ref.group(1).decode()} is not in the file")
    i = starts[-1].end()
    while i < len(data) and data[i] in SPACE:
        i += 1
    if data[i:i + 2] != b"<<":
        raise CVError("the Info object is not a dictionary")
    i += 2
    fields, key = {}, None
    while True:
        while i < len(data) and data[i] in SPACE:
            i += 1
        if i >= len(data):
            raise CVError("the Info dictionary opens and never closes")
        if data[i:i + 2] == b">>":
            i += 2
            break
        c = data[i]
        if c == 0x28:
            value, i = _literal(data, i)
            value = _decode(value)
        elif c == 0x3C:
            end = data.find(b">", i)
            if end < 0:
                raise CVError("an Info hex string opens and never closes")
            hexes = re.sub(rb"\s", b"", data[i + 1:end])
            if not re.fullmatch(rb"[0-9A-Fa-f]*", hexes):
                raise CVError("an Info hex string has non-hex bytes")
            value, i = _decode(bytes.fromhex((hexes + b"0" * (len(hexes) % 2)).decode())), end + 1
        elif c == 0x2F:
            j = i + 1
            while j < len(data) and data[j] not in SPACE and data[j] not in DELIMS:
                j += 1
            name, i = data[i + 1:j].decode("latin-1"), j
            if key is None:
                key = name
                continue
            value = "/" + name
        elif c == 0x29:
            raise CVError("the Info dictionary has a stray ')'")
        else:  # number, reference or keyword
            m = re.match(rb"(\d+\s+\d+\s+R|[^\s()<>\[\]{}/%]+)", data[i:])
            if not m:
                raise CVError(f"the Info dictionary has an unexpected byte at {i}")
            value, i = m.group(1).decode("latin-1"), i + m.end()
        if key is None:
            raise CVError("the Info dictionary has a value without a key")
        fields[key], key = value, None
    if key is not None:
        raise CVError(f"the Info key /{key} has no value")
    if not re.match(rb"\s*endobj", data[i:]):
        raise CVError("the Info dictionary is not followed by endobj")
    return fields


def qpdf_check(pdf_path):
    """qpdf --check, when qpdf is installed: None if it is not, else the list of its
    warnings and errors (empty when the file is clean)."""
    tool = shutil.which("qpdf")
    if not tool:
        return None
    done = subprocess.run([tool, "--check", str(pdf_path)], capture_output=True, timeout=60)
    # The exit code decides: 0 is clean, 3 is warnings, 2 is errors. The text is only
    # quoted; its closing note ("...the file may still contain errors that qpdf cannot
    # detect", wrapped over two lines) is not a warning.
    if done.returncode == 0:
        return []
    lines = (done.stdout + done.stderr).decode("utf-8", errors="replace").splitlines()
    found = [line.strip() for line in lines if re.match(r"\s*(WARNING|ERROR)|.*: (warning|error)", line, re.I)]
    return found or [f"qpdf exited with {done.returncode}"]


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


def check(pdf_path, lang, links, headings, name, email, phone=""):
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
    try:
        info = read_info(data)
        wrong = [k for k, v in info_fields(lang, None).items()
                 if k not in ("CreationDate", "ModDate") and info.get(k) != v]
        wrong += [k for k in ("CreationDate", "ModDate") if not str(info.get(k, "")).startswith("D:")]
        if wrong:
            problems.append("Info dictionary: wrong or missing " + ", ".join(wrong))
        info_note = "Info parsed"
    except CVError as error:
        problems.append(f"Info dictionary: {error}")
        info_note = "Info broken"
    qpdf = qpdf_check(pdf_path)
    if qpdf is None and os.environ.get("CI"):
        problems.append("qpdf is not installed, and in CI its check must run (the workflow installs it)")
        qpdf_note = "qpdf missing"
    elif qpdf is None:
        qpdf_note = "qpdf not installed (check skipped)"
    elif qpdf:
        problems.append(f"qpdf --check: {len(qpdf)} warning(s): " + " | ".join(qpdf[:5]))
        qpdf_note = "qpdf failed"
    else:
        qpdf_note = "qpdf 0 warnings"
    text = read_text(pdf_path)
    reading = "text layer not read (no pdftotext)"
    if text is None and os.environ.get("CI"):
        problems.append("pdftotext is not installed, and in CI the text layer must be read (the workflow installs poppler-utils)")
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
        if phone:  # said as yes/no: the number itself never reaches the log
            present = format_phone(phone) in flat
            if not present:
                problems.append("the phone is not in the text layer")
            reading += f", phone present: {'yes' if present else 'no'}"
    if problems:
        raise CVError(f"{pdf_path.name}: " + "; ".join(problems))
    return (f"{pdf_path.relative_to(ROOT).as_posix()}  {kb:.0f} KB, {pages} page, {images} image(s), "
            f"lang {lang}, {len(links)} links, {reading}, {info_note}, {qpdf_note}")


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
            set_info(out, code)
            written.add(out)
            labels = s["cv"]["labels"]
            headings = [labels[k] for k in ("experience", "projects", "education", "skills")]
            print(check(out, code, expected_links(site, s, projects, code, phone), headings,
                        site["person"]["name"], site["person"]["email"], phone))
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
