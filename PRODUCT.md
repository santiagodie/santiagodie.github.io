# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Static HTML, CSS and vanilla JavaScript. No framework, no build step, no runtime dependencies. Relative paths only, so the same files work at https://santiagodie.com and on any local static server. Deployed to GitHub Pages with a GitHub Actions workflow that publishes only the site files.

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
- The site is trilingual: English (default), Spanish and French. French and Spanish strings run longer than English.
- All UI copy lives in `i18n/*.json`; project data lives in `data/projects.json`.

## Capabilities and Constraints

- One page with fixed navigation: Header, Hero, About, Projects, Experience, Education, Skills, Contact, Footer.
- Language chosen from the browser (es / fr) on first visit, then remembered.
- All eight current projects are coursework from the University of La Rioja; each card shows its course as a discreet label.
- Open (TODO, to be supplied by Santiago): About text, Experience entries, Education entries, Skills list, CV PDF, translated project descriptions.

## Brand Commitments

- Name: **Santiago Die Morejón**. Headline: "Computer Engineer · AI & ML · MLOps".
- SD monogram (`assets/logo/sd-gold.svg`, copied unmodified from `sd-logo/`), used in header, footer and favicon.
- Visual coherence with the GitHub profile (`santiagodie/santiagodie`): navy, bone and gold, thin gold frame, rounded corners, sobriety. Full rules in DESIGN.md.

## Evidence on Hand

- Eight public repositories with READMEs (descriptions and "Built With" lists are the source for `data/projects.json`).
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
