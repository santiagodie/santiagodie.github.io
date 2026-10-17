<p align="center"><img src="assets/banner.svg" width="100%" alt="santiagodie.com · Personal portfolio website" /></p>

<p align="center">The source of <a href="https://santiagodie.com">santiagodie.com</a>: a one-page portfolio in English, Spanish and French, generated as static HTML (one page per language) from JSON content by a small Python script. No framework, no runtime dependencies.</p>

<p align="center">
  <img src="https://img.shields.io/badge/language-HTML%20%C2%B7%20CSS%20%C2%B7%20JS%20%C2%B7%20Python-C9A227?style=flat-square&labelColor=0B1F3A" alt="Language: HTML, CSS, JavaScript, Python" />
  <a href="https://santiagodie.com"><img src="https://img.shields.io/badge/live-santiagodie.com-C9A227?style=flat-square&labelColor=0B1F3A" alt="Live site" /></a>
</p>

## Table of Contents

- [About the Project](#about-the-project)
- [Built With](#built-with)
- [Getting Started](#getting-started)
- [Project Structure](#project-structure)
- [Adding a Project](#adding-a-project)
- [Editing or Adding a Translation](#editing-or-adding-a-translation)
- [Deployment](#deployment)
- [Contact](#contact)

## About the Project

- **One static page per language**, for search engines: English at `/`, Spanish at `/es/`, French at `/fr/`. Every word is in the generated HTML; JavaScript only adds behaviour (header state, menus, a dismissible language suggestion) and never injects content.
- **SEO per language**: translated `title`, description and Open Graph, `<link rel="canonical">`, `hreflang` alternates (with `x-default` to English), a Person JSON-LD block, `sitemap.xml` and `robots.txt`. There is no automatic redirect by browser language.
- **Content lives in JSON**: interface text in `i18n/<lang>.json`, projects (with their three languages) in `data/projects.json`, shared data in `data/site.json`. The build fails with a clear message if any language misses a key, so a page with gaps is never published.
- **Visible placeholders**: any string that starts with `TODO:` is rendered with a dashed `TODO` marker.
- **The hero** reuses the LinkedIn banner idea: the headline split into tokens with their real `cl100k_base` ids, and a `predict_next()` panel.

The visual rules (palette, logo, typography, motion) are in [DESIGN.md](DESIGN.md); product context is in [PRODUCT.md](PRODUCT.md).

## Built With

- HTML, CSS and vanilla JavaScript
- Python 3 (standard library only) for the generator
- [Hubot Sans](https://fonts.google.com/specimen/Hubot+Sans), [Mona Sans](https://fonts.google.com/specimen/Mona+Sans) and [JetBrains Mono](https://fonts.google.com/specimen/JetBrains+Mono) from Google Fonts
- GitHub Actions and GitHub Pages

## Getting Started

Build the three pages into `dist/` and serve them locally:

```bash
python tools/build.py --serve
```

Then open <http://localhost:8000> (and `/es/`, `/fr/`). Use `python tools/build.py` to build without serving, or `--port 8080` to change the port. `dist/` is generated, ignored by git and rebuilt by the deployment workflow.

## Project Structure

```
src/index.html             # Page template ({{ key }} placeholders, see tools/build.py)
i18n/en.json, es.json, fr.json   # All copy, per language
data/projects.json         # Projects: titles, courses, descriptions, metrics, links (3 languages)
data/site.json             # Site URL, profiles, languages, hero prediction
css/styles.css             # All styles: tokens, layout, components, motion
js/main.js                 # Behaviour only: header, menus, language suggestion
img/                       # SD logos (unmodified) and project screenshots (img/projects/*.webp)
favicon.svg, favicon.ico, apple-touch-icon.png, og-image.png, CNAME
tools/build.py             # Generator: renders dist/, sitemap.xml and robots.txt
tools/og-image.html        # Source of og-image.png
.github/workflows/pages.yml  # Builds and deploys dist/ on every push to main

assets/banner.svg          # README banner (not published)
PRODUCT.md, DESIGN.md      # Product and design context (not published)
```

## Adding a Project

Add an object to `data/projects.json`. Cards appear in the order of the list.

```json
{
  "id": "my-project",
  "title": "My Project",
  "course": { "en": "Artificial Intelligence", "es": "Inteligencia Artificial", "fr": "Intelligence artificielle" },
  "featured": false,
  "description": { "en": "One or two sentences.", "es": "…", "fr": "…" },
  "todo": [],
  "tech": ["Python", "PyTorch"],
  "repo": "https://github.com/santiagodie/my-project",
  "demo": { "url": "https://santiagodie.com/my-project/", "type": "web" }
}
```

- `demo` is optional; use `"type": "colab"` for a notebook.
- `todo` lists what is still pending. While it contains `description.es` or `description.fr`, that page shows a "translate description" marker and marks the English text with `lang="en"`.
- **Featured projects** (`"featured": true`) get a large card and also need:
  - `metrics`: one or two `{ "value": {en, es, fr}, "label": {en, es, fr} }` taken from the README (format numbers per language: `4,122` / `4.122` / `4 122`);
  - `image`: `{ "src": "img/projects/my-project.webp", "width": 1200, "height": 750, "alt": {en, es, fr} }`. Capture the live demo at 1440×900 and save it as WebP at 1200×750. Without the file, the build warns and shows a placeholder.

## Editing or Adding a Translation

- Edit the same key in the three files in `i18n/`. Lists (`experience.items`, `education.items`, `skills.groups`) must have the same entries in every language; an empty list shows a short "nothing yet" message, and an empty `about.paragraphs` removes the About section and its menu link.
- The hero tokens (`hero.tokens`) are the headline encoded with the `cl100k_base` tokenizer. If you change a headline, re-encode it, for example with `tiktoken`: `[{"t": enc.decode([i]), "id": i} for i in enc.encode(text)]`.
- To add the CV, put the PDF in a `cv/` folder (it is copied into `dist/`) and set `contact.cvFile`, for example `"cv/santiago-die-morejon-cv.pdf"`, in each language file.
- To add a language: copy `i18n/en.json` to `i18n/<code>.json` and translate it, add every project's `<code>` texts, and add `{ "code": "<code>", "path": "<code>/" }` to `languages` in `data/site.json`. The menu, hreflang links, sitemap and suggestion appear automatically.

To regenerate `og-image.png` after editing `tools/og-image.html`:

```bash
chrome --headless=new --hide-scrollbars --window-size=1200,630 --virtual-time-budget=8000 \
  --allow-file-access-from-files --screenshot=og-image.png "file:///$PWD/tools/og-image.html"
```

## Deployment

Every push to `main` (or a manual run) triggers `.github/workflows/pages.yml`: it runs `python tools/build.py` and deploys only `dist/` to GitHub Pages. In the repository settings, **Pages → Build and deployment → Source** must be **GitHub Actions**; the custom domain stays configured through `CNAME`.

## Contact

Santiago Die · [GitHub](https://github.com/santiagodie) · [LinkedIn](https://www.linkedin.com/in/santiago-die-morejon)
