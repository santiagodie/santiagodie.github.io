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
        for field in ("id", "title", "subject", "description", "repo"):
            if field not in project:
                problems.append(f"projects.json: '{pid}' has no '{field}'")
        localized = [("title", project.get("title")), ("subject", project.get("subject")),
                     ("description", project.get("description"))]
        for index, metric in enumerate(project.get("metrics", [])):
            localized += [(f"metrics[{index}].value", metric.get("value")), (f"metrics[{index}].label", metric.get("label"))]
        for index, part in enumerate(project.get("parts", [])):
            if not part.get("repo"):
                problems.append(f"projects.json: '{pid}' has no parts[{index}].repo")
            localized.append((f"parts[{index}].label", part.get("label")))
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


def published(value):
    """Paragraphs and entries still marked TODO stay in i18n but are not published."""
    return bool(value) and not TODO.match(str(value))


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


def obfuscate(value):
    """Every character as an HTML entity: the browser shows and follows the same
    address, with or without JavaScript, while naive scrapers that grep the source
    for addresses do not find one."""
    return "".join(f"&#{ord(char)};" for char in value)


def thing(item):
    node = {"@type": item["type"], "name": item["name"]}
    if item.get("url"):
        node["url"] = item["url"]
    return node


def render_jsonld(site, strings, lang):
    person = site["person"]
    address = person["address"]
    data = {
        "@context": "https://schema.org",
        "@type": "Person",
        "name": person["name"],
        "alternateName": person.get("alternateName", []),
        "url": site["url"],
        "jobTitle": strings[lang]["meta"]["jobTitle"],
        "description": strings[lang]["meta"]["description"],
        "image": site["url"] + person["image"],
        "email": person["email"],
        "address": {"@type": "PostalAddress", "addressLocality": address["locality"],
                    "addressRegion": address["region"], "addressCountry": address["country"]},
        "alumniOf": [thing(school) for school in person["alumniOf"]],
        # An internship is not employment: `affiliation` says he is linked to the
        # organisation without claiming, as `worksFor` would, that he is on its staff.
        "affiliation": thing(person["affiliation"]),
        "knowsLanguage": [language["code"] for language in site["languages"]],
        "sameAs": [person["github"], person["linkedin"]] + person.get("otherProfiles", []),
    }
    # "@" and "." escaped as JSON unicode escapes (same value for any JSON parser),
    # so the address is not in the page source as plain text either.
    return (json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
            .replace(person["email"], person["email"].replace("@", "\\u0040").replace(".", "\\u002e")))


# Flags for the language links, drawn once as symbols. National flags in their own
# colours, the one exception to the palette (owner's request, v2.5); Spain's is the
# civil flag, without the coat of arms, which would be a smudge at this size.
FLAGS = {
    "en": ("gb", "0 0 60 30",
           '<clipPath id="flag-gb-clip"><path d="M30 15h30v15zv15H0zH0V0zV0h30z"/></clipPath>'
           '<path fill="#012169" d="M0 0h60v30H0z"/>'
           '<path stroke="#fff" stroke-width="6" d="M0 0l60 30m0-30L0 30"/>'
           '<path stroke="#C8102E" stroke-width="4" clip-path="url(#flag-gb-clip)" d="M0 0l60 30m0-30L0 30"/>'
           '<path stroke="#fff" stroke-width="10" d="M30 0v30M0 15h60"/>'
           '<path stroke="#C8102E" stroke-width="6" d="M30 0v30M0 15h60"/>'),
    "es": ("es", "0 0 750 500",
           '<path fill="#AA151B" d="M0 0h750v500H0z"/><path fill="#F1BF00" d="M0 125h750v250H0z"/>'),
    "fr": ("fr", "0 0 3 2",
           '<path fill="#000091" d="M0 0h1v2H0z"/><path fill="#fff" d="M1 0h1v2H1z"/><path fill="#E1000F" d="M2 0h1v2H2z"/>'),
}


def render_flag_sprite(site):
    symbols = "".join(f'<symbol id="flag-{name}" viewBox="{box}">{body}</symbol>'
                      for name, box, body in (FLAGS[lang["code"]] for lang in site["languages"]))
    return f'  <svg class="flag-sprite" aria-hidden="true" focusable="false">{symbols}</svg>'


def flag(code):
    """A decorative flag: the link or button around it carries the language's name."""
    name, box, _ = FLAGS[code]
    return (f'<svg class="flag flag--{name}" viewBox="{box}" aria-hidden="true" focusable="false">'
            f'<use href="#flag-{name}"/></svg>')


def render_lang_menu(site, strings, current, root):
    items = []
    for lang in site["languages"]:
        code = lang["code"]
        current_attr = ' aria-current="page"' if code == current else ""
        items.append(
            f'              <li role="none"><a role="menuitem" href="{relative_href(root, lang)}" hreflang="{code}" lang="{code}"'
            f' data-lang-link{current_attr}>{flag(code)}<span class="lang__name">{esc(strings[code]["meta"]["langName"])}</span></a></li>')
    return "\n".join(items)


def render_lang_list(site, strings, current, root):
    items = []
    for lang in site["languages"]:
        code = lang["code"]
        current_attr = ' aria-current="page"' if code == current else ""
        items.append(
            f'              <li><a href="{relative_href(root, lang)}" hreflang="{code}" lang="{code}" data-lang-link{current_attr}>'
            f'{flag(code)}<span>{esc(strings[code]["meta"]["langName"])}</span></a></li>')
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
# The question, the answer and the message-limit notice are written into the HTML, so
# the finished chat is what readers without JavaScript and search engines get.
# js/chat.js animates it: the token ids (real, data/tokens.json), the illustrative
# attention weights and candidates (data/llm.json) and the notice's reset-time
# sentences travel as a small JSON block for it.

SEND = '<svg viewBox="0 0 20 20" aria-hidden="true"><path d="M10 15.5v-11M5 9l5-5 5 5"/></svg>'
SKIP = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M4 4l4 4-4 4M9 4l4 4-4 4"/></svg>'
FORWARD = '<svg class="icon" aria-hidden="true" viewBox="0 0 16 16"><path d="M3 8h10M9 4l4 4-4 4"/></svg>'
CLOCK = '<svg class="chat__limit-icon" viewBox="0 0 20 20" aria-hidden="true"><circle cx="10" cy="10" r="7.5"/><path d="M10 5.5V10h3.5"/></svg>'
REPLAY = '<svg viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 8a4.5 4.5 0 1 0 1.4-3.3"/><path d="M3.5 2.5v2.6h2.6"/></svg>'


def render_chat(s, tokens, model, lang):
    chat = s["chat"]
    answer = "".join(f'<span class="t">{esc(token["t"])}</span>' for token in tokens[lang]["answer"])
    data = {
        "prompt": tokens[lang]["prompt"],
        "attention": model[lang]["attention"],
        "next": [{"t": word, "p": p} for word, p in model[lang]["next"]],
        "stages": chat["stages"],
        "reset": [chat["limit"]["reset"], chat["limit"]["resetOne"]],
    }
    # The arrow stays with the last word when the link wraps.
    *words, last = chat["limit"]["cta"].split(" ")
    cta = esc(" ".join(words + [""])) + f'<span class="nowrap">{esc(last)}&nbsp;{FORWARD}</span>'
    # "</" cannot close the script block early: every "<" is escaped.
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c")
    # Readers get the answer as paragraphs; the token spans are only drawn.
    paragraphs = "".join(f"<p>{esc(p)}</p>" for p in chat["answer"].split("\n\n"))
    # On narrow screens the conversation scrolls inside the panel, so it is a
    # focusable region (js/chat.js drops the tab stop where it does not scroll).
    # data-nosnippet: the chat is still indexed, but search engines do not quote it
    # as the page's summary (meta.description is the summary).
    return f'''        <div class="chat" data-chat data-nosnippet>
          <p class="visually-hidden">{esc(chat["description"])}</p>
          <div class="chat__panel">
            <div class="chat__scene">
              <div class="chat__log" role="region" aria-label="{esc(chat["log"])}" tabindex="0">
                <div class="visually-hidden"><p>{esc(chat["prompt"])}</p>{paragraphs}</div>
                <p class="chat__bubble" aria-hidden="true"><span>{esc(chat["prompt"])}</span></p>
                <p class="chat__answer" aria-hidden="true">{answer}</p>
              </div>
              <div class="chat__limit" data-chat-limit>
                <p class="chat__limit-body">{CLOCK}<span class="chat__limit-text">{esc(chat["limit"]["text"])}<span data-chat-reset></span></span><a class="chat__limit-link" href="#contact">{cta}</a></p>
              </div>
              <div class="chat__composer" role="group" aria-label="{esc(chat["placeholder"])}" aria-disabled="true">
                <span class="chat__input" aria-hidden="true"><span class="chat__typed">{esc(chat["prompt"])}</span><span class="chat__placeholder">{esc(chat["placeholder"])}</span></span>
                <button class="chat__send" type="button" disabled aria-label="{esc(chat["send"])}: {esc(chat["prompt"])}"><span class="chat__ring"></span>{SEND}</button>
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
    paragraphs = "\n".join(f"            <p>{text(p)}</p>" for p in s["about"]["paragraphs"] if published(p))
    return f'          <div class="prose">\n{paragraphs}\n          </div>' if paragraphs else ""


def lead(value):
    return f'          <p class="section__lead">{text(value)}</p>' if published(value) else ""


def project_text(project, lang, s):
    pending = f"description.{lang}" in project.get("todo", [])
    attr = ' lang="en"' if pending and lang != "en" else ""
    note = s["projects"]["translationPending"]
    note = f'\n                <p class="card__pending">{text(note)}</p>' if pending and published(note) else ""
    return f'<p class="card__text"{attr}>{text(project["description"][lang])}</p>{note}'


def repo_name(url):
    # The repository keeps its own name in every language.
    return url.rstrip("/").split("/")[-1]


def demo_label(demo, s, short=False):
    if demo.get("type") == "colab":
        return s["projects"]["colabShort" if short else "colab"]
    return s["projects"]["demoShort" if short else "demo"]


def project_links(project, lang, s):
    title = project["title"][lang]
    links = [external(project["repo"], s["projects"]["code"], title, s)]
    demo = project.get("demo")
    if demo and demo.get("url"):
        links.insert(0, external(demo["url"], demo_label(demo, s), title, s))
    return "".join(links) + f'<span class="card__repo" translate="no">{esc(repo_name(project["repo"]))}</span>'


def project_parts(project, lang, s):
    """A project made of several repositories: one labelled group per part, each with its
    demo and its code. The links keep the usual "Live demo" and "Code" text; the part and
    the project are added for screen readers, so no two links have the same name."""
    title = project["title"][lang]
    groups = []
    for index, part in enumerate(project["parts"]):
        label = part["label"][lang]
        context = f"{label}, {title}"
        links = external(part["repo"], s["projects"]["code"], context, s)
        demo = part.get("demo")
        if demo and demo.get("url"):
            links = external(demo["url"], demo_label(demo, s), context, s) + links
        heading = f'{project["id"]}-part-{index}'
        groups.append(
            f'<div class="card__part" role="group" aria-labelledby="{heading}">'
            f'<p class="card__part-label" id="{heading}">{esc(label)} '
            f'<span class="card__repo" translate="no">{esc(repo_name(part["repo"]))}</span></p>'
            f'{links}</div>')
    return "".join(groups)


def tags(project, s):
    items = "".join(f"<li>{esc(t)}</li>" for t in project.get("tech", []))
    return f'<p class="visually-hidden">{esc(s["projects"]["stack"])}</p><ul class="tags" role="list">{items}</ul>'


def render_featured(projects, lang, s):
    """The three featured projects: one row of cards, each with its README metrics."""
    cards = []
    for project in projects:
        if not project.get("featured"):
            continue
        metrics = "".join(
            f'<div><dt>{esc(m["label"][lang])}</dt><dd>{esc(m["value"][lang])}</dd></div>'
            for m in project.get("metrics", []))
        if metrics:
            metrics = f'\n              <dl class="card__metrics" aria-label="{esc(s["projects"]["metrics"])}">{metrics}</dl>'
        if project.get("parts"):
            links = f'<div class="card__links card__links--parts">{project_parts(project, lang, s)}</div>'
        else:
            links = f'<div class="card__links">{project_links(project, lang, s)}</div>'
        cards.append(f'''            <li class="card card--feature">{FRAME}
              <h4 class="card__title">{esc(project["title"][lang])}</h4>
              <p class="card__subject">{esc(project["subject"][lang])}</p>
              {project_text(project, lang, s)}{metrics}
              {tags(project, s)}
              {links}
            </li>''')
    return "\n".join(cards)


def render_projects(projects, lang, s):
    """The other projects: small cards that are one link to the repository (the link's
    ::after covers the card), with a separate, smaller Demo link where there is one."""
    cards = []
    new_tab = s["a11y"]["newTab"]
    for project in projects:
        if project.get("featured"):
            continue
        title = project["title"][lang]
        repo = repo_name(project["repo"])
        demo = project.get("demo")
        extra = ""
        if demo and demo.get("url"):
            extra = (f'<a class="card__demo" href="{esc(demo["url"])}" target="_blank" rel="noopener">{esc(demo_label(demo, s, short=True))}{ARROW}'
                     f'<span class="visually-hidden">: {esc(title)} ({esc(new_tab)})</span></a>')
        foot = "card__foot"
        if project.get("parts"):
            # One demo link per part, named after it; the repository name gets its own line
            extra = "".join(
                f'<a class="card__demo" href="{esc(part["demo"]["url"])}" target="_blank" rel="noopener">{esc(part["label"][lang])}{ARROW}'
                f'<span class="visually-hidden">: {esc(demo_label(part["demo"], s))}, {esc(title)} ({esc(new_tab)})</span></a>'
                for part in project["parts"] if part.get("demo", {}).get("url"))
            foot += " card__foot--stacked"
            extra = f'<span class="card__more">{extra}</span>'
        cards.append(f'''            <li class="card card--mini">{FRAME}
              <h4 class="card__title"><a class="card__link" href="{esc(project["repo"])}" target="_blank" rel="noopener">{esc(title)}<span class="visually-hidden">: {esc(s["projects"]["code"])} ({esc(new_tab)})</span></a></h4>
              <p class="card__subject">{esc(project["subject"][lang])}</p>
              {tags(project, s)}
              <p class="{foot}"><span class="card__repo" translate="no" aria-hidden="true"><span class="card__repo-name">{esc(repo)}</span>{ARROW}</span>{extra}</p>
            </li>''')
    if not cards:
        return ""  # no heading over an empty list
    return (f'          <h3 class="subhead">{text(s["projects"]["more"])}</h3>\n'
            f'          <ul class="projects" role="list">\n' + "\n".join(cards) + "\n          </ul>")


def entries(s, name):
    """The published entries: an entry whose title is still TODO is left out."""
    return [item for item in s[name]["items"] if published(item["title"])]


def stack(value, s):
    """A "A · B · C" line as a list in mono with gold dots, like a project's technologies."""
    items = "".join(f"<li>{esc(t)}</li>" for t in value.split(" · "))
    return f'<p class="visually-hidden">{esc(s["projects"]["stack"])}</p><ul class="tags" role="list">{items}</ul>'


def render_entries(s, name):
    rows = []
    for item in entries(s, name):
        period = item["period"] if published(item.get("period")) else ""
        parts = [f'<p class="entry__period">{text(period)}</p><div class="entry__body">',
                 f'<h3 class="entry__title">{text(item["title"])}</h3>']
        if published(item.get("org")):
            place = f'<span class="entry__place"> · {esc(item["place"])}</span>' if published(item.get("place")) else ""
            parts.append(f'<p class="entry__org">{text(item["org"])}{place}</p>')
        if published(item.get("text")):
            parts.append(f'<p class="entry__text">{text(item["text"])}</p>')
        if published(item.get("details")):
            parts.append(f'<p class="entry__details">{esc(item["details"])}</p>')
        if published(item.get("stack")):
            parts.append(stack(item["stack"], s))
        rows.append("            <li class=\"entry\">" + "".join(parts) + "</div></li>")
    if not rows:
        return ""
    out = '          <ol class="entries" role="list">\n' + "\n".join(rows) + "\n          </ol>"
    # Certifications sit under Education, as a short list of their own.
    certs = s[name].get("certifications")
    if certs and [c for c in certs["items"] if published(c)]:
        items = "".join(f"<li>{esc(c)}</li>" for c in certs["items"] if published(c))
        out += (f'\n          <h3 class="minor">{esc(certs["title"])}</h3>'
                f'\n          <ul class="certs" role="list">{items}</ul>')
    return out


def skill_groups(s):
    """The published skill groups, each with its published items; empty ones are left out."""
    groups = []
    for group in s["skills"]["groups"]:
        items = [item for item in group.get("items", []) if published(item)]
        if published(group["name"]) and items:
            groups.append((group["name"], items))
    return groups


def render_skills(s):
    """Each group as a row: its name, then its items in mono; then the spoken languages."""
    rows = []
    for name, items in skill_groups(s):
        items = "".join(f"<li>{esc(item)}</li>" for item in items)
        rows.append(f'            <div class="skills__group"><dt class="skills__name">{text(name)}</dt>'
                    f'<dd><ul class="skills__items" role="list">{items}</ul></dd></div>')
    if not rows:
        return ""
    out = '          <dl class="skills">\n' + "\n".join(rows) + "\n          </dl>"
    languages = s["skills"]["languages"]
    if languages["items"]:
        items = "".join(f'<div class="langs__item"><dt>{esc(item["name"])}</dt><dd>{esc(item["level"])}</dd></div>'
                        for item in languages["items"])
        out += (f'\n          <h3 class="minor">{esc(languages["title"])}</h3>'
                f'\n          <dl class="langs">{items}</dl>')
    return out


def render_email(site, s):
    """The address, entity-encoded (see obfuscate); a plain mailto link for the visitor."""
    address = obfuscate(site["person"]["email"])
    return (f'            <li>\n              <a class="contact__link" href="{obfuscate("mailto:")}{address}">'
            f'<span class="contact__label">{text(s["contact"]["emailLabel"])}</span><span class="contact__value">{address}</span>{ARROW}</a>\n'
            f'            </li>')


def render_location(s):
    contact = s["contact"]
    return (f'            <li>\n              <p class="contact__row">'
            f'<span class="contact__label">{esc(contact["locationLabel"])}</span><span class="contact__value">{esc(contact["location"])}</span></p>\n'
            f'            </li>')


def render_cv(s, root, warnings):
    """The CV button only exists when the PDF does."""
    contact = s["contact"]
    if not contact["cvFile"]:
        return ""
    if not (ROOT / contact["cvFile"]).exists():
        warnings.add(f"contact.cvFile is {contact['cvFile']!r}, which does not exist: the CV is not published")
        return ""
    name = contact["cvFile"].split("/")[-1]
    return (f'            <li>\n              <a class="contact__link" href="{root}{esc(contact["cvFile"])}" target="_blank" rel="noopener">'
            f'<span class="contact__label">{text(contact["cv"])}</span><span class="contact__value">{esc(name)}</span>{ARROW}'
            f'<span class="visually-hidden">({esc(s["a11y"]["newTab"])})</span></a>\n'
            f'            </li>')


# Page ---------------------------------------------------------------------

PLACEHOLDER = re.compile(r"\{\{\s*([=@!]?)\s*([\w.]+)\s*\}\}")
FRAGMENT_LINE = re.compile(r"^[ \t]*\{\{\s*(!)\s*(\w+)\s*\}\}\n", re.M)
# The page's sections, in order (ids in src/index.html).
SECTIONS = ["about", "projects", "experience", "education", "skills", "contact"]


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
    # A section without published content is left out, with its menu link (and so its
    # point on the progress line); the rest are numbered 01, 02... without gaps and
    # alternate white and bone. Contact is always navy, and always has the profiles.
    content = {
        "about": True,  # the chat
        "projects": bool(projects),
        "experience": bool(entries(s, "experience")),
        "education": bool(entries(s, "education")),
        "skills": bool(skill_groups(s)),
        "contact": True,
    }
    shown = [section for section in SECTIONS if content[section]]
    for number, section in enumerate(shown, 1):
        values[f"num_{section}"] = f"{number:02d} /"
        values[f"navnum_{section}"] = f"{number:02d}"  # the same number in the mobile menu
        values[f"bg_{section}"] = "white" if number % 2 else "bone"
    for section in SECTIONS:
        for key in ("num", "navnum", "bg"):
            values.setdefault(f"{key}_{section}", "")
    fragments = {
        "alternates": lambda: render_alternates(site),
        "ogAlternates": lambda: render_og_alternates(site, strings, lang),
        "jsonld": lambda: render_jsonld(site, strings, lang),
        "langMenu": lambda: render_lang_menu(site, strings, lang, root),
        "langList": lambda: render_lang_list(site, strings, lang, root),
        "langFlag": lambda: flag(lang),
        "flagSprite": lambda: render_flag_sprite(site),
        "langSuggest": lambda: render_lang_suggest(site, strings, lang, root),
        "chat": lambda: render_chat(s, tokens, model, lang),
        "about": lambda: render_about(s),
        "featured": lambda: render_featured(projects, lang, s),
        "projects": lambda: render_projects(projects, lang, s),
        "experience": lambda: render_entries(s, "experience"),
        "education": lambda: render_entries(s, "education"),
        "skills": lambda: render_skills(s),
        "projectsLead": lambda: lead(s["projects"]["intro"]),
        "contactLead": lambda: lead(s["contact"]["text"]),
        "email": lambda: render_email(site, s),
        "location": lambda: render_location(s),
        "cv": lambda: render_cv(s, root, warnings),
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

    def line(match):
        # A fragment alone on its line that renders nothing takes its line with it.
        rendered = replace(match)
        return rendered + "\n" if rendered else ""

    page = FRAGMENT_LINE.sub(line, template)
    page = PLACEHOLDER.sub(replace, page)
    for section in SECTIONS:
        if section not in shown:
            page, removed = re.subn(rf'\n\n *<section class="section[^"]*" id="{section}".*?</section>\n', "\n", page, flags=re.S)
            page, unlinked = re.subn(rf'\n *<li[^>]*><a href="#{section}".*?</a></li>', "", page)
            if not (removed and unlinked):
                raise BuildError(f"src/index.html: could not leave out the empty '{section}' section")
    return page


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
