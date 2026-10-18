"""Generate the static, one-page-per-language site into dist/.

Usage:
    python tools/build.py            # build dist/
    python tools/build.py --serve    # build, then serve dist/ on http://localhost:8000
    python tools/build.py --serve --port 8080

Inputs: src/index.html (template), i18n/<lang>.json (all copy), data/projects.json
(projects, with their three languages), data/site.json (URL, profiles, languages),
data/tokens.json (real cl100k_base token ids) and data/llm.json
(the illustrative values of the About chat animation). Python standard library only.

Template syntax:
    {{ key.path }}    text from i18n, escaped; a leading "TODO:" becomes a visible marker
    {{= key.path }}   the same, for attributes (escaped, no markup)
    {{ @name }}       a build value (lang, root, canonical, year...)
    {{ !name }}       an HTML fragment rendered by this script

The build stops with a clear message if any language misses a key or a project misses
a translation, so a page with gaps is never published.
"""
import argparse
import functools
import html
import http.server
import json
import re
import shutil
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
STATIC = ["css", "js", "img", "fonts", "favicon.ico", "favicon.svg", "apple-touch-icon.png", "og-image.png", "og-image-es.png", "og-image-fr.png", "CNAME", "cv"]
ARROW = '<svg class="icon" aria-hidden="true" viewBox="0 0 16 16"><path d="M5 11 11 5M6 5h5v5"/></svg>'
FRAME = '<svg class="frame" aria-hidden="true" focusable="false"><rect pathLength="1"/></svg>'  # traced in on scroll (js/scroll.js)
TODO = re.compile(r"^TODO\s*:?\s*")
# Lists whose length legitimately differs per language.
VARIABLE_LENGTH = set()


class BuildError(Exception):
    pass


def load_json(path):
    try:
        return json.loads((ROOT / path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise BuildError(f"missing file: {path}")
    except json.JSONDecodeError as error:
        raise BuildError(f"{path}: invalid JSON ({error})")


# Validation --------------------------------------------------------------

def compare_keys(reference, other, lang, path=""):
    """Every key in the reference language must exist, with the same shape, in `other`."""
    problems = []
    if isinstance(reference, dict):
        if not isinstance(other, dict):
            return [f"{lang}: '{path}' should be an object"]
        for key, value in reference.items():
            where = f"{path}.{key}" if path else key
            if key not in other:
                problems.append(f"{lang}: missing key '{where}'")
            else:
                problems += compare_keys(value, other[key], lang, where)
    elif isinstance(reference, list):
        if not isinstance(other, list):
            return [f"{lang}: '{path}' should be a list"]
        # Lists of entries (experience, education, skills...) must match the English
        # list item by item, so an entry missing in one language is caught.
        if reference and isinstance(reference[0], dict):
            if path in VARIABLE_LENGTH:
                for index, item in enumerate(other):
                    problems += compare_keys(reference[0], item, lang, f"{path}[{index}]")
                return problems
            if len(other) != len(reference):
                problems.append(f"{lang}: '{path}' has {len(other)} entries, en has {len(reference)}")
            for index, (ref_item, item) in enumerate(zip(reference, other)):
                problems += compare_keys(ref_item, item, lang, f"{path}[{index}]")
    return problems


def validate_model(strings, tokens, model, langs):
    """The token ids must spell the current question and answer of every language, and
    the illustrative data must fit them: one attention weight per question token, and the
    chosen candidate (the first) must be the first answer token."""
    problems = []
    for lang in langs:
        chat, data = strings[lang]["chat"], model.get(lang)
        if lang not in tokens:
            problems.append(f"data/tokens.json has no '{lang}'")
            continue
        for field in ("prompt", "answer"):
            spelled = "".join(token["t"] for token in tokens[lang][field])
            if spelled != chat[field]:
                problems.append(f"{lang}: data/tokens.json spells {spelled!r}, i18n chat.{field} is {chat[field]!r}")
        if not data:
            problems.append(f"data/llm.json has no '{lang}'")
            continue
        if len(data["attention"]) != len(tokens[lang]["prompt"]):
            problems.append(f"{lang}: data/llm.json attention has {len(data['attention'])} weights for {len(tokens[lang]['prompt'])} question tokens")
        first = tokens[lang]["answer"][0]["t"].strip()
        if not data["next"] or data["next"][0][0] != first:
            problems.append(f"{lang}: data/llm.json next must start with the first answer token {first!r}")
    if problems:
        raise BuildError("the About chat data is out of date (re-encode the question and answer into data/tokens.json "
                         "with tools/tokenize.py):\n  - " + "\n  - ".join(problems))


def validate(strings, projects, langs):
    problems = []
    reference = strings["en"]
    for lang in langs:
        if lang != "en":
            problems += compare_keys(reference, strings[lang], lang)
    for project in projects:
        pid = project.get("id", "?")
        for field in ("id", "title", "course", "description", "repo"):
            if field not in project:
                problems.append(f"projects.json: '{pid}' has no '{field}'")
        localized = [("title", project.get("title")), ("course", project.get("course")),
                     ("description", project.get("description"))]
        for index, metric in enumerate(project.get("metrics", [])):
            localized += [(f"metrics[{index}].value", metric.get("value")), (f"metrics[{index}].label", metric.get("label"))]
        if project.get("image"):
            localized.append(("image.alt", project["image"].get("alt")))
        for name, values in localized:
            for lang in langs:
                if not isinstance(values, dict) or not values.get(lang):
                    problems.append(f"projects.json: '{pid}' has no {name}.{lang}")
    if problems:
        raise BuildError("translations are incomplete:\n  - " + "\n  - ".join(problems))


# Rendering helpers --------------------------------------------------------

def esc(value):
    return html.escape(str(value), quote=True)


def text(value):
    """Escaped text; a leading TODO becomes the visible marker."""
    value = str(value)
    if TODO.match(value):
        rest = TODO.sub("", value)
        return f'<span class="todo">TODO</span> <span class="todo-text">{esc(rest)}</span>'
    return esc(value)


def lookup(strings, path, lang):
    node = strings
    for key in path.split("."):
        if not isinstance(node, dict) or key not in node:
            raise BuildError(f"{lang}: template uses '{path}', which is not in i18n/{lang}.json")
        node = node[key]
    if isinstance(node, (dict, list)):
        raise BuildError(f"{lang}: '{path}' is not a string")
    return node


def external(href, label, context, s):
    hidden = f": {context} ({s['a11y']['newTab']})" if context else f" ({s['a11y']['newTab']})"
    return (f'<a href="{esc(href)}" target="_blank" rel="noopener">{text(label)}{ARROW}'
            f'<span class="visually-hidden">{esc(hidden)}</span></a>')


def page_url(site, language):
    return site["url"] + language["path"]


def relative_href(root, language):
    return (root + language["path"]) or "./"


# Fragments ----------------------------------------------------------------

def render_alternates(site):
    lines = [f'  <link rel="alternate" hreflang="{lang["code"]}" href="{page_url(site, lang)}">' for lang in site["languages"]]
    default = next(lang for lang in site["languages"] if lang.get("default"))
    lines.append(f'  <link rel="alternate" hreflang="x-default" href="{page_url(site, default)}">')
    return "\n".join(lines)


def render_og_alternates(site, strings, current):
    return "\n".join(
        f'  <meta property="og:locale:alternate" content="{esc(strings[lang["code"]]["meta"]["ogLocale"])}">'
        for lang in site["languages"] if lang["code"] != current)


def render_jsonld(site, s):
    person = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": site["person"]["name"],
        "url": site["url"],
        "jobTitle": s["meta"]["jobTitle"],
        "sameAs": [site["person"]["github"], site["person"]["linkedin"]],
    }
    return json.dumps(person, ensure_ascii=False).replace("</", "<\\/")


def render_lang_menu(site, strings, current, root):
    items = []
    for lang in site["languages"]:
        code = lang["code"]
        current_attr = ' aria-current="page"' if code == current else ""
        items.append(
            f'              <li role="none"><a role="menuitem" href="{relative_href(root, lang)}" hreflang="{code}" lang="{code}"'
            f' data-lang-link{current_attr}><span class="lang__name">{esc(strings[code]["meta"]["langName"])}</span>'
            f'<span class="lang__item-code" aria-hidden="true">{code.upper()}</span></a></li>')
    return "\n".join(items)


def render_lang_suggest(site, strings, current, root):
    blocks = []
    for lang in site["languages"]:
        code = lang["code"]
        if code == current:
            continue
        s = strings[code]["langSuggest"]
        blocks.append(
            f'  <div class="lang-suggest" data-suggest="{code}" lang="{code}" hidden>\n'
            f'    <p>{esc(s["text"])}</p>\n'
            f'    <a class="lang-suggest__action" href="{relative_href(root, lang)}" hreflang="{code}">{esc(s["action"])}</a>\n'
            f'    <button class="lang-suggest__close" type="button" data-suggest-dismiss aria-label="{esc(s["dismiss"])}">'
            f'<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 4l8 8M12 4l-8 8"/></svg></button>\n'
            f'  </div>')
    return "\n".join(blocks)


# The About chat -----------------------------------------------------------
# The question and the answer are written into the HTML, so the finished chat is what
# readers without JavaScript and search engines get. js/chat.js animates it: the
# token ids (real, data/tokens.json) and the illustrative attention weights and
# candidates (data/llm.json) travel as a small JSON block for it.

SEND = '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 15.5v-11M5 9l5-5 5 5"/></svg>'
SKIP = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 4l4 4-4 4M9 4l4 4-4 4"/></svg>'
REPLAY = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 8a4.5 4.5 0 1 0 1.4-3.3"/><path d="M3.5 2.5v2.6h2.6"/></svg>'


def render_chat(s, tokens, model, lang):
    chat = s["chat"]
    answer = "".join(f'<span class="t">{esc(token["t"])}</span>' for token in tokens[lang]["answer"])
    data = {
        "prompt": tokens[lang]["prompt"],
        "attention": model[lang]["attention"],
        "next": [{"t": word, "p": p} for word, p in model[lang]["next"]],
        "stages": chat["stages"],
    }
    # "</" cannot close the script block early: every "<" is escaped.
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    return f'''        <div class="chat" data-chat>
          <p class="visually-hidden">{esc(chat["description"])}</p>
          <div class="chat__panel">
            <div class="chat__scene">
              <div class="chat__log" aria-hidden="true">
                <p class="chat__bubble"><span>{esc(chat["prompt"])}</span></p>
                <p class="chat__answer">{answer}</p>
              </div>
              <div class="chat__composer">
                <span class="chat__input" aria-hidden="true"><span class="chat__typed">{esc(chat["prompt"])}</span><span class="chat__placeholder">{esc(chat["placeholder"])}</span></span>
                <button class="chat__send" type="button" aria-label="{esc(chat["send"])}: {esc(chat["prompt"])}"><span class="chat__ring"></span>{SEND}</button>
              </div>
            </div>
            <div class="chat__stage" aria-hidden="true"></div>
            <span class="chat__clock" aria-hidden="true"></span>
            <button class="chat__ctl" type="button" data-chat-skip hidden>{esc(chat["skip"])}{SKIP}</button>
            <button class="chat__ctl" type="button" data-chat-replay hidden>{REPLAY}{esc(chat["replay"])}</button>
          </div>
          <p class="visually-hidden" aria-live="polite" data-chat-live></p>
          <script type="application/json" data-chat-model>{payload}</script>
        </div>'''


def render_about(s):
    # The chat introduces the owner; any further About text follows it.
    paragraphs = "\n".join(f"            <p>{text(p)}</p>" for p in s["about"]["paragraphs"])
    return f'          <div class="prose">\n{paragraphs}\n          </div>' if paragraphs else ""


def project_text(project, lang, s):
    pending = f"description.{lang}" in project.get("todo", [])
    attr = ' lang="en"' if pending and lang != "en" else ""
    note = f'\n                <p class="card__pending">{text(s["projects"]["translationPending"])}</p>' if pending else ""
    return f'<p class="card__text"{attr}>{text(project["description"][lang])}</p>{note}'


def project_links(project, lang, s):
    title = project["title"][lang]
    links = [external(project["repo"], s["projects"]["code"], title, s)]
    demo = project.get("demo")
    if demo and demo.get("url"):
        label = s["projects"]["colab"] if demo.get("type") == "colab" else s["projects"]["demo"]
        links.insert(0, external(demo["url"], label, title, s))
    # The repository keeps its own name in every language.
    repo = "/".join(project["repo"].rstrip("/").split("/")[-2:])
    return "".join(links) + f'<span class="card__repo" translate="no">{esc(repo)}</span>'


def course_line(project, lang, s):
    return f'{esc(project["course"][lang])} · <span class="nowrap">{esc(s["projects"]["university"])}</span>'


def tags(project, s):
    items = "".join(f"<li>{esc(t)}</li>" for t in project.get("tech", []))
    return f'<p class="visually-hidden">{esc(s["projects"]["stack"])}</p><ul class="tags" role="list">{items}</ul>'


def render_featured(projects, lang, s, root, warnings):
    cards = []
    for project in projects:
        if not project.get("featured"):
            continue
        image = project.get("image")
        if image and (ROOT / image["src"]).exists():
            media = (f'<img src="{root}{esc(image["src"])}" alt="{esc(image["alt"][lang])}" width="{image["width"]}" '
                     f'height="{image["height"]}" loading="lazy" decoding="async">')
        else:
            warnings.add(f"no screenshot for {project['id']} (expected {image['src'] if image else 'image'}), using a placeholder")
            media = (f'<div class="feature__placeholder" role="img" aria-label="{esc(project["title"][lang])}">'
                     f'<img src="{root}img/sd-navy.svg" alt="" width="290" height="208"></div>')
        metrics = "".join(
            f'<div class="metric"><dt>{esc(m["label"][lang])}</dt><dd>{esc(m["value"][lang])}</dd></div>'
            for m in project.get("metrics", []))
        cards.append(f'''            <li class="feature">
              <article class="feature__card" aria-labelledby="p-{project["id"]}">{FRAME}
                <div class="feature__media">{media}</div>
                <div class="feature__body">
                  <h4 class="feature__title" id="p-{project["id"]}">{esc(project["title"][lang])}</h4>
                  <p class="card__course">{course_line(project, lang, s)}</p>
                  {project_text(project, lang, s)}
                  <dl class="metrics" aria-label="{esc(s["projects"]["metrics"])}">{metrics}</dl>
                  {tags(project, s)}
                  <div class="card__links">{project_links(project, lang, s)}</div>
                </div>
              </article>
            </li>''')
    return "\n".join(cards)


def render_projects(projects, lang, s):
    cards = []
    for project in projects:
        if project.get("featured"):
            continue
        cards.append(f'''            <li class="card">{FRAME}
              <h4 class="card__title">{esc(project["title"][lang])}</h4>
              <p class="card__course">{course_line(project, lang, s)}</p>
              {project_text(project, lang, s)}
              {tags(project, s)}
              <div class="card__links">{project_links(project, lang, s)}</div>
            </li>''')
    return "\n".join(cards)


def render_entries(s, name):
    items = s[name]["items"]
    if not items:
        return f'          <p class="status">{text(s[name]["empty"])}</p>'
    rows = []
    for item in items:
        parts = [f'<p class="entry__period">{text(item["period"])}</p><div class="entry__body">',
                 f'<h3 class="entry__title">{text(item["title"])}</h3>']
        if item.get("org"):
            parts.append(f'<p class="entry__org">{text(item["org"])}</p>')
        if item.get("text"):
            parts.append(f'<p class="entry__text">{text(item["text"])}</p>')
        rows.append("            <li class=\"entry\">" + "".join(parts) + "</div></li>")
    return '          <ol class="entries" role="list">\n' + "\n".join(rows) + "\n          </ol>"


def render_skills(s):
    groups = [g for g in s["skills"]["groups"] if g.get("items")]
    if not groups:
        return f'          <p class="status">{text(s["skills"]["empty"])}</p>'
    blocks = []
    for group in groups:
        items = "".join(f"<li>{text(item)}</li>" for item in group["items"])
        blocks.append(f'            <div class="skills__group"><h3 class="skills__name">{text(group["name"])}</h3>'
                      f'<ul class="skills__items" role="list">{items}</ul></div>')
    return '          <div class="skills">\n' + "\n".join(blocks) + "\n          </div>"


def render_cv(s, root):
    contact = s["contact"]
    if contact["cvFile"]:
        name = contact["cvFile"].split("/")[-1]
        return (f'              <a class="contact__link" href="{root}{esc(contact["cvFile"])}" target="_blank" rel="noopener">'
                f'<span class="contact__label">{text(contact["cv"])}</span><span class="contact__value">{esc(name)}</span>{ARROW}'
                f'<span class="visually-hidden">({esc(s["a11y"]["newTab"])})</span></a>')
    return (f'              <div class="contact__row"><span class="contact__label">{text(contact["cv"])}</span>'
            f'<span class="contact__value">{text(contact["cvPending"])}</span></div>')


# Page ---------------------------------------------------------------------

PLACEHOLDER = re.compile(r"\{\{\s*([=@!]?)\s*([\w.]+)\s*\}\}")


def render_page(template, site, strings, projects, tokens, model, language, warnings):
    lang = language["code"]
    s = strings[lang]
    root = "../" * language["path"].count("/")
    values = {
        "lang": lang, "langCode": lang.upper(), "root": root, "year": date.today().year,
        "langs": ",".join(l["code"] for l in site["languages"]),
        "canonical": page_url(site, language), "siteUrl": site["url"],
        # Each language has its own link preview, English as fallback.
        "ogImage": site["url"] + (f"og-image-{lang}.png" if (ROOT / f"og-image-{lang}.png").exists() else "og-image.png"),
        "github": site["person"]["github"], "linkedin": site["person"]["linkedin"],
    }
    fragments = {
        "alternates": lambda: render_alternates(site),
        "ogAlternates": lambda: render_og_alternates(site, strings, lang),
        "jsonld": lambda: render_jsonld(site, s),
        "langMenu": lambda: render_lang_menu(site, strings, lang, root),
        "langSuggest": lambda: render_lang_suggest(site, strings, lang, root),
        "chat": lambda: render_chat(s, tokens, model, lang),
        "about": lambda: render_about(s),
        "featured": lambda: render_featured(projects, lang, s, root, warnings),
        "projects": lambda: render_projects(projects, lang, s),
        "experience": lambda: render_entries(s, "experience"),
        "education": lambda: render_entries(s, "education"),
        "skills": lambda: render_skills(s),
        "cv": lambda: render_cv(s, root),
    }

    def replace(match):
        kind, name = match.groups()
        if kind == "@":
            if name not in values:
                raise BuildError(f"template uses unknown build value '@{name}'")
            return esc(values[name])
        if kind == "!":
            if name not in fragments:
                raise BuildError(f"template uses unknown fragment '!{name}'")
            return fragments[name]()
        value = lookup(strings[lang], name, lang)
        return esc(value) if kind == "=" else text(value)

    return PLACEHOLDER.sub(replace, template)


def render_sitemap(site):
    entries = []
    for language in site["languages"]:
        links = "".join(
            f'\n    <xhtml:link rel="alternate" hreflang="{lang["code"]}" href="{page_url(site, lang)}"/>'
            for lang in site["languages"])
        default = next(lang for lang in site["languages"] if lang.get("default"))
        links += f'\n    <xhtml:link rel="alternate" hreflang="x-default" href="{page_url(site, default)}"/>'
        entries.append(f"  <url>\n    <loc>{page_url(site, language)}</loc>\n    <lastmod>{date.today().isoformat()}</lastmod>{links}\n  </url>")
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            + "\n".join(entries) + "\n</urlset>\n")


def build():
    site = load_json("data/site.json")
    langs = [language["code"] for language in site["languages"]]
    strings = {lang: load_json(f"i18n/{lang}.json") for lang in langs}
    projects = load_json("data/projects.json")["projects"]
    tokens = load_json("data/tokens.json")
    model = load_json("data/llm.json")
    validate(strings, projects, langs)
    validate_model(strings, tokens, model, langs)
    template = (ROOT / "src" / "index.html").read_text(encoding="utf-8")

    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    warnings = set()
    for language in site["languages"]:
        out = DIST / language["path"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(render_page(template, site, strings, projects, tokens, model, language, warnings), encoding="utf-8", newline="\n")

    for name in STATIC:
        source = ROOT / name
        if source.is_dir():
            shutil.copytree(source, DIST / name)
        elif source.exists():
            shutil.copy2(source, DIST / name)
    (DIST / "sitemap.xml").write_text(render_sitemap(site), encoding="utf-8", newline="\n")
    (DIST / "robots.txt").write_text(f"User-agent: *\nAllow: /\n\nSitemap: {site['url']}sitemap.xml\n", encoding="utf-8", newline="\n")
    (DIST / ".nojekyll").write_text("", encoding="utf-8")

    for warning in sorted(warnings):
        print(f"warning: {warning}", file=sys.stderr)
    print(f"built {len(langs)} pages into {DIST.relative_to(ROOT)}/ ({', '.join(langs)})")


def serve(port):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(DIST))
    with http.server.ThreadingHTTPServer(("127.0.0.1", port), handler) as server:
        print(f"serving dist/ on http://localhost:{port}/  (Ctrl+C to stop)")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--serve", action="store_true", help="serve dist/ after building")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    try:
        build()
    except BuildError as error:
        print(f"build failed: {error}", file=sys.stderr)
        sys.exit(1)
    if args.serve:
        serve(args.port)


if __name__ == "__main__":
    main()
