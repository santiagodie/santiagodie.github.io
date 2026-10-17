---
version: 1
slug: "index-html"
primary_target: "index.html"
related_targets: []
---

Scope: index.html, the whole one-page portfolio. Visitor mode: Experience (the work leads; the interface recedes).

Audience and job: technical recruiters and engineering teams (Spain + English-speaking countries) screening Santiago in minutes, often from LinkedIn on a phone. Action: open a repo or demo, then reach out via GitHub, LinkedIn or CV.

Constraints: brief-pinned world (DESIGN.md non-negotiables: navy/gold/bone/white only, gold only on navy, unmodified SD logo, GitHub-profile frame language, no flashy effects). Static HTML/CSS/JS, no deps. EN/ES/FR from i18n JSON.

## Direction contract

THESIS: The portfolio is the GitHub profile banner made habitable: one framed navy plate per idea, quiet typography, evidence first. It refuses the dark-mode developer template (neon accent, terminal costume, gradient hero, icon-tile cards).
OWN-WORLD: Navy ground everywhere; bone text in three opacities; gold only as 1px frames, short 44px rules, focus, active states and "·" separators. Double thin gold frame with 6px corners (from header.svg / make_banner.py). Mona Sans for voice, JetBrains Mono only for data (stack, course, years, language codes, TODO).
STORY: Visitor learns name and focus in the first screen, sees eight real projects with course context and links, then finds how to get in touch.
FIRST VIEWPORT: Fixed 64px header (logo left, links, EN ES FR right). Below, the hero plate fills the viewport: double gold frame; inside, left: name at display scale, 44px gold rule, gold role line, two actions (Projects bordered gold, Contact underlined bone); right of a vertical gold hairline: the SD monogram, as in the banner. Mobile: monogram hidden, plate full-bleed minus gutter.
FORM: Editorial two-column section rhythm (title 3/12, content 9/12), brief-pinned; seed: none (unavailable). Signature interaction: the gold rule under the name draws in once on load; sections settle 8px on first view; language switch crossfades text.
FINISH: unreviewed and undocumented is unfinished; this build ends with the finish review, the verdict, DESIGN.md, and every shipping raster carrying its provenance
