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

The personal portfolio of Santiago Die Morejón, a final-year computer engineering student focused on applied AI: language models and computer vision (lot 22, 2026-11-20; until then "AI, machine learning and MLOps", and MLOps is now one skill among others). It gathers the projects, background and contact points in one place so that a reader can decide quickly whether to get in touch.

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

- One page per language with sticky navigation: Header, Hero, Projects, About (the chat), Experience, Education, Skills, Contact, Footer. Sections without published content are left out (see below).
- No automatic redirect by browser language. At most a discreet, dismissible suggestion of the matching language version; the dismissal is remembered.
- All ten current projects are coursework from the University of La Rioja (confirmed again 2026-11-16 for the two added later); each card shows its course (`subject` in `data/projects.json`, taken from the "Built for the … course" line of each README). Official Spanish course names: "Sistemas Distribuidos", "Programación de Aplicaciones Web", "Inteligencia Artificial", "Profesión de Ingeniero Informático", "Tecnología Orientada a Objetos", "Taller Transversal I: Programación y Proceso de Información"; English and French use natural translations.
- Featured projects (one row of cards with their README metrics; no screenshots since v2.4, owner's choice): since lot 22 (2026-11-20, option B), face-similarity-search-pipeline, satellite-image-classifier and prompt-topic-classifier, one language project and two vision projects, all the owner's own work; graduate-salary-predictor and the life simulation moved to More projects. Satellite links its public model on the Hugging Face Hub ("Model"); prompts will once its DistilBERT is published. The rest are small cards (title, course, technologies) that each link to their repository, with a separate Demo link where there is one.
- One project can span several repositories: the life simulation is one card with two parts (`parts` in `data/projects.json`), life-simulation-service and life-simulation-web-client, each with its own repository and demo, grouped by repository.
- Demo links have a type: `web` (live site), `colab` (notebook) or `download` (a release to download, e.g. library-management-system's latest GitHub release).
- No analytics (owner's decision, 2026-11-16, after Google Analytics was added and removed on 2026-10-21): no tracking scripts, no cookies, so no consent banner. The only client storage is the language-suggestion dismissal in `localStorage`.
- Project titles, descriptions, image alt texts and metric labels exist in all three languages (natural translations, 2026-10-18); repository names are never translated.
- Real content (supplied by Santiago in santiago-die-portfolio.md, 2026-10-19, in EN/ES/FR, used verbatim; corrections are proposed to him, never applied silently): the About text is the chat's answer; Experience (internship at Encore Lab, from Sep 2026; freelance full-stack developer for Islamontana Travel, remote, from Apr 2026, added by the owner on 2026-10-21), Education (Bachelor's Degree in Computer Engineering, 4 years and 240 ECTS, at the University of La Rioja, 2021–2027; since lot 23 never "BSc" or "Licence", which are 3-year degrees, and in French never "génie informatique" or "ingénieur", which read as a Bac+5 diplôme d'ingénieur; French Baccalauréat and Ecuadorian Bachillerato at the Lycée franco-équatorien La Condamine, 2020) with Certifications, Skills with spoken Languages, and Contact with the email contact@santiagodie.com and the location (Logroño, La Rioja, Spain), plus the owner's photo (`img/portrait-*`, AVIF/WebP/JPEG at 160 and 320 px). The CV PDF exists since lot 4 (2026-11-17): one per language, printed from the page itself (`tools/make_cv.py`), downloaded from the hero's first button.
- Hidden sections (owner's rule, 2026-10-18): paragraphs and entries that still start with `TODO` stay in `i18n/*.json` but are never published. A section left without published content is not published either: not the section, not its link in the navigation (desktop and mobile menu), not its point on the progress line; the visible sections are numbered 01, 02, 03... without gaps and keep alternating left/right and white/bone. A section comes back by itself once it has content. Contact is never empty, because the chat's notice links to it: it always has the real GitHub and LinkedIn profiles and a short translated sentence; the email stays TODO (unpublished) until the owner decides, and the CV button only exists when the PDF does. (2026-10-19: the owner decided; the email is published, entity-encoded against simple scrapers.)

## Brand Commitments

- Name: **Santiago Die Morejón**. Headline since lot 22: the page title "Applied AI: language and computer vision" (ES «IA aplicada: lenguaje y visión por computador», FR « IA appliquée : langage et vision par ordinateur »); the hero's role line and the link previews (`hero.role`, `tools/make_og.py`) say the same, at most two lines at 360px. Earlier: "Computer Engineer · AI & ML · MLOps"; French "Ingénieur informatique" (owner's choice, 2026-10-18, not "Ingénieur informaticien").
- SD monogram (`assets/logo/sd-gold.svg`, copied unmodified from `sd-logo/`), used in header and footer. The favicons redraw the same geometry: `favicon.svg` without a background, navy in light mode and white in dark mode, with a stroke of 28 instead of 20 so it holds at 16 px; `favicon.ico` (16, 32, 48 px) navy on a rounded bone square for browsers without SVG favicons; `apple-touch-icon.png` gold on navy with a safe margin.
- Logo versions from `sd-logo/`, unmodified: `sd-navy.svg` on light grounds, `sd-gold.svg` on navy.
- LinkedIn banner concept (`linkedin-banner.png`): a phrase shown as `tokenize()` chips with token ids (cl100k_base) and a `predict_next()` panel, "Computer → engineer 0.86, science 0.09, vision 0.03, programmer 0.02". Since v2.1 the hero expands it into a diagram of how a language model turns the prompt "Who is Santiago Die?" into "A computer engineer focused on AI and MLOps." (translated per page): token ids are real, the other values illustrative, and the static diagram shows the banner's own step, "computer → engineer 0.86". It is described as "a language model" in general, never as any specific model.
- Visual coherence with the GitHub profile and banners: navy, bone, gold, white; thin gold lines and frames; sobriety. Full rules in DESIGN.md.

## Evidence on Hand

- Eleven public repositories with READMEs behind ten projects (descriptions and "Built With" lists are the source for `data/projects.json`).
- Metrics stated in the READMEs, usable on cards: Graduate Salary Predictor R² = 0.919 and MAE ≈ 4,122 on a 200-row test set (indicative, small training sample); Face Similarity Search 38,299 indexed face embeddings, F1 0.911 at the calibrated threshold, 94.4% self-retrieval; Life Simulation 108 tests passing across 3 Maven modules, 220 requests sent over 30 s to 5 workers, the queue empty at 83 s (never "processed in 30 s"); Satellite classifier 99.82% test accuracy (ResNet18, 4 classes; shown as a percentage since lot 23) and five CNN architectures compared; Prompt classifier 67.35% test accuracy and weighted F1 0.667 on 1,550 test prompts (DistilBERT, 10 classes); WordHive TCP (7777) and HTTP (7070) modes from one entry point, 31 daily puzzles.
- Live demos: wordhive-socket-server, electrosa-fullstack-ecommerce, face-similarity-search-pipeline, graduate-salary-predictor, life-simulation-service, life-simulation-web-client (GitHub Pages); sudoku-vision-solver (Colab notebook). Download: library-management-system (latest GitHub release).
- GitHub: https://github.com/santiagodie · LinkedIn: https://www.linkedin.com/in/santiago-die-morejon · Hugging Face: https://huggingface.co/santiagodie (lot 22: in Contact and the JSON-LD `sameAs`; Instagram removed from `sameAs`). The CV's head keeps the site and LinkedIn only (plus the phone and the email); GitHub and Hugging Face reach the CV through the projects' links.
- Every figure on the site and in the CV is in `.audit/l5/claims.json` with its source (repository, file and line, or notebook cell; Encore Lab: the owner's diagnosis of 2026-11-20).
- Absent, must not be fabricated: work history beyond the two Experience entries, dates, grades, skills levels, testimonials, metrics beyond what the READMEs state.

## Product Principles

1. Evidence over claims: link to code and demos; never invent facts about Santiago.
2. Fast to scan: a recruiter should get name, focus and best work in seconds.
3. Equal in three languages: no language is a second-class translation of the layout.
4. Easy to maintain: adding a project or a translation is editing one JSON file.

## Accessibility & Inclusion

WCAG 2.2 AA: semantic HTML, alt text, visible focus, full keyboard navigation, AA contrast, and `prefers-reduced-motion` respected.
