# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Static HTML, CSS and vanilla JavaScript, no framework and no runtime dependencies. Since v2 (2026-10-17) a small generator, `tools/build.py` (Python standard library only), renders one complete HTML page per language from `src/` templates plus `i18n/*.json` and `data/projects.json` into `dist/`. JavaScript only enhances (navigation state, menus, language suggestion); it never injects content. GitHub Actions runs the generator and deploys `dist/`; generated pages are not committed. Asset paths stay relative so the output works at https://santiagodie.com and on a local static server.

## Users

- **Technical recruiters** in Spain and in English-speaking countries, screening a candidate in a few minutes, often from a LinkedIn link, often on a phone.
- **Engineering teams and hiring managers** who want evidence: what was built, with which tools, and whether the code and demos are real.

## Product Purpose

The personal portfolio of Santiago Die Morejón, a computer engineer specialising in AI, machine learning and MLOps. It gathers the projects, background and contact points in one place so that a reader can decide quickly whether to get in touch.

Success: a visitor understands who Santiago is and what the work is about within the first screen, can open a real repository or demo in one click, and can get in touch through GitHub, LinkedIn or the CV.

## Positioning

The proof is the work itself: every project links to a public repository with a detailed README, and several have live demos at `https://santiagodie.com/<repo>/`. The site must let that evidence speak rather than adding claims around it.

Career moment (confirmed 2026-10-17): Santiago is doing the degree internship and graduates this year, with little professional experience so far. The copy should stay timeless rather than read as a "junior looking for a first job" page, so it does not need rewriting after the next career step.

## Operating Context

- Readers arrive from LinkedIn, GitHub, a CV or an email signature, so the shared link preview (Open Graph) matters.
- The site is trilingual, one static page per language for SEO: English at `/` (default and `x-default`), Spanish at `/es/`, French at `/fr/`. French and Spanish strings run longer than English.
- All copy lives in `i18n/*.json`; project data, with its three languages, lives in `data/projects.json`. The build fails if a key is missing in any language.
- Search engines and link previews read the static HTML, so every language page carries its own title, description, canonical, hreflang alternates, Open Graph and Person JSON-LD.

## Capabilities and Constraints

- One page per language with sticky navigation: Header, Hero, About, Projects, Experience, Education, Skills, Contact, Footer.
- No automatic redirect by browser language. At most a discreet, dismissible suggestion of the matching language version; the dismissal is remembered.
- All eight current projects are coursework from the University of La Rioja; each card shows its course. Official Spanish course names: "Sistemas Distribuidos", "Programación de Aplicaciones Web", "Inteligencia Artificial", "Profesión de Ingeniero Informático"; English and French use natural translations.
- Featured projects (large cards with a real demo screenshot and README metrics): graduate-salary-predictor, face-similarity-search-pipeline, wordhive-socket-server. The rest sit in a compact grid.
- Open (TODO, to be supplied by Santiago): About text, Experience entries, Education entries, Skills list, CV PDF, translated project descriptions.

## Brand Commitments

- Name: **Santiago Die Morejón**. Headline: "Computer Engineer · AI & ML · MLOps".
- SD monogram (`assets/logo/sd-gold.svg`, copied unmodified from `sd-logo/`), used in header, footer and favicon.
- Logo versions from `sd-logo/`, unmodified: `sd-navy.svg` on light grounds, `sd-gold.svg` on navy.
- LinkedIn banner concept (`linkedin-banner.png`): a phrase shown as `tokenize()` chips with token ids (cl100k_base) and a `predict_next()` panel, "Computer → engineer 0.86, science 0.09, vision 0.03, programmer 0.02". The hero reuses this concept; ids are computed with the real tokenizer and the probabilities are the banner's own figures.
- Visual coherence with the GitHub profile and banners: navy, bone, gold, white; thin gold lines and frames; sobriety. Full rules in DESIGN.md.

## Evidence on Hand

- Eight public repositories with READMEs (descriptions and "Built With" lists are the source for `data/projects.json`).
- Metrics stated in the READMEs, usable on cards: Graduate Salary Predictor R² = 0.919 and MAE ≈ 4,122 on a 200-row test set (indicative, small training sample); Face Similarity Search 38,299 indexed face embeddings, F1 0.911 at the calibrated threshold, 94.4% self-retrieval; WordHive TCP (7777) and HTTP (7070) modes from one entry point, 31 daily puzzles.
- Live demos: wordhive-socket-server, electrosa-fullstack-ecommerce, face-similarity-search-pipeline, graduate-salary-predictor (GitHub Pages); sudoku-vision-solver (Colab notebook).
- GitHub: https://github.com/santiagodie · LinkedIn: https://www.linkedin.com/in/santiago-die-morejon
- Absent, must not be fabricated: work history, dates, grades, skills levels, testimonials, metrics beyond what the READMEs state.

## Product Principles

1. Evidence over claims: link to code and demos; never invent facts about Santiago.
2. Fast to scan: a recruiter should get name, focus and best work in seconds.
3. Equal in three languages: no language is a second-class translation of the layout.
4. Easy to maintain: adding a project or a translation is editing one JSON file.

## Accessibility & Inclusion

WCAG 2.2 AA: semantic HTML, alt text, visible focus, full keyboard navigation, AA contrast, and `prefers-reduced-motion` respected.
