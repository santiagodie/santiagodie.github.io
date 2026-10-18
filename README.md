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
- **The hero** shows how a language model turns a prompt ("Who is Santiago Die?", translated per page) into an answer, in eight stages: prompt, tokens, embeddings, attention, softmax, sampling, output and the autoregressive loop. Token ids are real (`cl100k_base`, the tokenizer of the LinkedIn banner); probabilities, embeddings and attention weights are illustrative (screen readers are told so). It plays once when it scrolls into view, with pause, replay and stage controls; on phones it becomes a fixed-height card with one stage at a time. Without JavaScript or with reduced motion it is a complete static diagram.
- **Scroll**: sections assemble once as they arrive, and a thin gold line drawn with the scroll links the section numbers (CSS scroll timeline where supported, `requestAnimationFrame` elsewhere). Content is always visible in the HTML; nothing holds or redirects the scroll.

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
data/site.json             # Site URL, profiles, languages
data/tokens.json           # Real cl100k_base token ids of the hero prompt and answer
data/llm.json              # Illustrative values of the hero diagram: candidates, probabilities, attention
css/styles.css             # All styles: tokens, layout, components, motion
js/main.js                 # Behaviour only: header, menus, language suggestion
js/hero-model.js           # Plays the hero diagram (classes and attributes only, no text)
js/scroll.js               # Progress line, current section, sections assembling on scroll
img/                       # SD logos (unmodified) and project screenshots (img/projects/*.webp)
favicon.svg, favicon.ico, apple-touch-icon.png, CNAME
og-image.png, og-image-es.png, og-image-fr.png   # Link previews, one per language
tools/build.py             # Generator: renders dist/, sitemap.xml and robots.txt
.github/workflows/pages.yml  # Builds and deploys dist/ on every push to main

assets/banner.svg          # README banner (not published)
```

## Adding a Project

Add an object to `data/projects.json`. Cards appear in the order of the list.

```json
{
  "id": "my-project",
  "title": { "en": "My Project", "es": "Mi proyecto", "fr": "Mon projet" },
  "course": { "en": "Artificial Intelligence", "es": "Inteligencia Artificial", "fr": "Intelligence artificielle" },
  "featured": false,
  "description": { "en": "One or two sentences.", "es": "…", "fr": "…" },
  "todo": [],
  "tech": ["Python", "PyTorch"],
  "repo": "https://github.com/santiagodie/my-project",
  "demo": { "url": "https://santiagodie.com/my-project/", "type": "web" }
}
```

- `title`, `description`, `course`, the image `alt` and the metric labels are required in every language; the build stops if one is missing. The repository name is not translated: it is shown as `santiagodie/<repo>` in mono next to the links.
- `demo` is optional; use `"type": "colab"` for a notebook.
- `todo` lists what is still pending. While it contains `description.es` or `description.fr`, that page shows a "translate description" marker and marks the English text with `lang="en"`.
- **Featured projects** (`"featured": true`) get a large card and also need:
  - `metrics`: one or two `{ "value": {en, es, fr}, "label": {en, es, fr} }` taken from the README (format numbers per language: `4,122` / `4.122` / `4 122`);
  - `image`: `{ "src": "img/projects/my-project.webp", "width": 1200, "height": 750, "alt": {en, es, fr} }`. Capture the live demo at 1440×900 and save it as WebP at 1200×750. Without the file, the build warns and shows a placeholder.

## Editing or Adding a Translation

- Edit the same key in the three files in `i18n/`. Lists (`experience.items`, `education.items`, `skills.groups`) must have the same entries in every language; an empty list shows a short "nothing yet" message, and an empty `about.paragraphs` removes the About section and its menu link.
- The hero diagram's prompt and answer are `llm.prompt` and `llm.answer`. After editing them, re-encode both with the `cl100k_base` tokenizer (for example with `tiktoken`) and update `data/tokens.json`; the build refuses ids that no longer spell the text. If the answer's length changes, give `data/llm.json` one step per answer token plus the end token (the candidate words and probabilities there are illustrative).
- To add the CV, put the PDF in a `cv/` folder (it is copied into `dist/`) and set `contact.cvFile`, for example `"cv/santiago-die-morejon-cv.pdf"`, in each language file.
- To add a language: copy `i18n/en.json` to `i18n/<code>.json` and translate it, add every project's `<code>` texts, add `{ "code": "<code>", "path": "<code>/" }` to `languages` in `data/site.json`, add its tokens to `data/tokens.json` and its steps to `data/llm.json`. The menu, hreflang links and sitemap appear automatically; for the language suggestion bar add the `html[data-suggest="<code>"]` line in `css/styles.css`, and for its link preview add an `og-image-<code>.png` (1200×630).

## Deployment

Every push to `main` (or a manual run) triggers `.github/workflows/pages.yml`: it runs `python tools/build.py` and deploys only `dist/` to GitHub Pages. In the repository settings, **Pages → Build and deployment → Source** must be **GitHub Actions**; the custom domain stays configured through `CNAME`.

## Contact

Santiago Die · [GitHub](https://github.com/santiagodie) · [LinkedIn](https://www.linkedin.com/in/santiago-die-morejon)
