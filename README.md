<p align="center"><img src="assets/banner.svg" width="100%" alt="santiagodie.com · Personal portfolio website" /></p>

<p align="center">The source of <a href="https://santiagodie.com">santiagodie.com</a>: a one-page, trilingual (English, Spanish, French) portfolio written in plain HTML, CSS and JavaScript, with no framework, no dependencies and no build step.</p>

<p align="center">
  <img src="https://img.shields.io/badge/language-HTML%20%C2%B7%20CSS%20%C2%B7%20JS-C9A227?style=flat-square&labelColor=0B1F3A" alt="Language: HTML, CSS, JavaScript" />
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

A single page with a fixed header and the sections About, Projects, Experience, Education, Skills and Contact.

- **Content lives in JSON.** Interface text is in `i18n/<lang>.json`; projects are in `data/projects.json`. The HTML holds structure only.
- **Three languages.** English by default. On the first visit the site follows the browser language when it is Spanish or French; after that it remembers the visitor's choice (`localStorage`). `?lang=es` or `?lang=fr` in the URL forces a language, which is useful for sharing a link.
- **Visible placeholders.** Any string that starts with `TODO:` is shown with a dashed `TODO` marker, so missing content is easy to spot before publishing.
- **Accessible and light.** Semantic HTML, keyboard navigation, visible focus, AA contrast, `prefers-reduced-motion` support, and one small script.

The visual rules (palette, logo use, typography, motion) are in [DESIGN.md](DESIGN.md); product context is in [PRODUCT.md](PRODUCT.md).

## Built With

- HTML, CSS and vanilla JavaScript
- [Mona Sans](https://fonts.google.com/specimen/Mona+Sans) and [JetBrains Mono](https://fonts.google.com/specimen/JetBrains+Mono) from Google Fonts
- GitHub Actions and GitHub Pages

## Getting Started

The page loads its JSON with `fetch`, so it needs a local web server (opening `index.html` from the file system will not work):

```bash
python -m http.server 8000
```

Then open <http://localhost:8000>.

## Project Structure

```
index.html                 # Page structure; text comes from i18n/
css/styles.css             # All styles: tokens, layout, components, motion
js/main.js                 # i18n, project cards, mobile menu, section reveals
data/projects.json         # Project cards
i18n/en.json, es.json, fr.json
img/sd-gold.svg            # SD logo (unmodified)
favicon.svg, favicon.ico, apple-touch-icon.png
og-image.png               # Link preview image (1200x630)
CNAME                      # Custom domain
.github/workflows/pages.yml  # Deploys only the files above

assets/banner.svg          # README banner (not published)
tools/og-image.html        # Source of og-image.png (not published)
PRODUCT.md, DESIGN.md      # Product and design context for the design skills (not published)
```

## Adding a Project

Add an object to `data/projects.json`. Cards appear in the order of the list.

```json
{
  "id": "my-project",
  "title": "My Project",
  "course": "Artificial Intelligence",
  "description": {
    "en": "One or two sentences, ideally the same as the repository's About.",
    "es": "…",
    "fr": "…"
  },
  "todo": [],
  "tech": ["Python", "PyTorch"],
  "repo": "https://github.com/santiagodie/my-project",
  "demo": { "url": "https://santiagodie.com/my-project/", "type": "web" }
}
```

- `course` is optional; when present the card reads "Course · University of La Rioja" (translated).
- `demo` is optional. Use `"type": "web"` for a live site and `"type": "colab"` for a notebook.
- `"featured": true` (optional) makes the card span the full row with the double gold frame of the hero. Use it for one or two projects at most.
- `todo` lists fields still to be done. While `description.es` or `description.fr` is in it, the card shows a "translate description" marker in that language. Remove the entry once the translation is in.

## Editing or Adding a Translation

- To change text, edit the same key in `i18n/en.json`, `i18n/es.json` and `i18n/fr.json`.
- Experience, Education and Skills are lists inside each language file (`experience.items`, `education.items`, `skills.groups`). An empty list shows a short "nothing yet" message; an empty `about.paragraphs` hides the About section.
- To add the CV, put the PDF in a `cv/` folder and set `contact.cvFile` (for example `"cv/santiago-die-morejon-cv.pdf"`) in each language file. A different PDF per language works too.
- To add a language, copy `i18n/en.json` to `i18n/<code>.json`, translate it, add the code to `LANGS` in `js/main.js` and add a button with `data-lang="<code>"` to the language switcher in `index.html`.

The title and description in the `<head>` of `index.html` stay in English on purpose: link previews (LinkedIn, Slack) read the HTML without running JavaScript.

To regenerate `og-image.png` after a change to `tools/og-image.html`, serve the repository locally and run:

```bash
chrome --headless=new --hide-scrollbars --window-size=1200,630 --virtual-time-budget=8000 \
  --screenshot=og-image.png http://localhost:8000/tools/og-image.html
```

## Deployment

Every push to `main` (or a manual run) triggers `.github/workflows/pages.yml`, which copies only the website files into an artifact and deploys it to GitHub Pages. In the repository settings, **Pages → Build and deployment → Source** must be set to **GitHub Actions**; the custom domain stays configured through `CNAME`.

## Contact

Santiago Die · [GitHub](https://github.com/santiagodie) · [LinkedIn](https://www.linkedin.com/in/santiago-die-morejon)
