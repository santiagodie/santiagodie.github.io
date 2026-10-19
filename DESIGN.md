# Design

Visual system of santiagodie.com (v2, 2026-10-17; v2.1 additions 2026-10-18; v2.3, the chat as the About section and hidden empty sections, 2026-10-18; v2.4, the real content, the full About answer and compact project cards, 2026-10-19). Product context lives in PRODUCT.md.

## Non-negotiable rules

Set by the owner; they win over any recommendation from any design skill. Copied verbatim from the v2 brief (Spanish original). They replace the v1 rules (navy page background).

> - Fondo principal blanco #FFFFFF. Bone #F5F0E1 como fondo secundario para alternar secciones. Navy #0B1F3A para textos, titulares y bloques destacados.
> - Gold #C9A227: solo sobre azul marino, o como detalle decorativo fino (líneas, marcos, iconos) sobre claro. Nunca como color de texto sobre blanco o hueso, porque no tiene contraste suficiente.
> - No se pueden añadir colores nuevos. Logo sin modificar: sd-navy.svg sobre fondos claros y sd-gold.svg sobre azul marino (las versiones de sd-logo\).
> - Prohibido: glassmorphism, neones, degradados de colores, partículas, redes neuronales de fondo, cursores personalizados, scroll-jacking. Respeta prefers-reduced-motion en todo.

Still binding from v1: derived tints (lighter, darker, transparent) of the four colours are allowed, new hues are not; content about the owner is never invented; motion is short, purposeful and respects `prefers-reduced-motion`. Missing content is no longer shown with a TODO marker on the published page (owner's choice, 2026-10-18, replacing the v1 rule):

> Hidden sections (owner's rule, 2026-10-18): paragraphs and entries that still start with `TODO` stay in `i18n/*.json` but are never published. A section left without published content is not published either: not the section, not its link in the navigation (desktop and mobile menu), not its point on the progress line; the visible sections are numbered 01, 02, 03... without gaps and keep alternating left/right and white/bone. A section comes back by itself once it has content. Contact is never empty, because the chat's notice links to it: it always has the real GitHub and LinkedIn profiles and a short translated sentence; the email stays TODO (unpublished) until the owner decides, and the CV button only exists when the PDF does.

Since v2.4 (2026-10-19) every section has the owner's real content, and Contact also publishes the email (santiagodimo@gmail.com, owner's decision) and the location. Content texts are used exactly as supplied in EN/ES/FR; corrections are proposed to the owner, never applied silently.

v2.1 additions (2026-10-18), also binding. The first one is verbatim from the v2.1 brief:

> - La punta de la línea de progreso: un punto luminoso con un halo dorado suave (drop-shadow o blur del mismo gold con opacidad baja), y detrás una estela que se desvanece en unas decenas de px. Es una excepción a la regla de "sin neones" solo para este elemento: brillo contenido, un solo color, nada de tonos fluorescentes ni degradados multicolor (solo opacidades del gold).

- The About chat animation is presented as "a language model" in general, never as the internals of Claude or of any specific model, and its interface and texts copy no real product. Token ids are real (`cl100k_base`); probabilities, embeddings and attention weights are illustrative. No note says so on the page (removed at the owner's request, v2.3).
- Every animated thing has a complete static form: without JavaScript or with `prefers-reduced-motion: reduce`, the About chat is shown answered with its message-limit notice (reduced motion: a short fade, no zoom), sections are simply there, and the progress line is complete and still.
- Scroll motion animates `transform`, `opacity` and `stroke-dashoffset` only, plays once per element, never leaves content half-visible, and never holds or hijacks the scroll. Content is visible in the HTML by default; the hidden starting state only exists under `html.js` with motion allowed.

Design direction: a professional 2026 portfolio people remember, still sober. Character comes from the owner's own material (the SD stroke, the tokenizer banner, real project evidence), typography and rhythm, never from generic effects.

## Color

Light page. All tokens live in `css/styles.css` `:root`.

| Token | Value | Use |
| --- | --- | --- |
| `--white` | `#FFFFFF` | Page background |
| `--bone` | `#F5F0E1` | Alternating section background, text on navy |
| `--navy` | `#0B1F3A` | Text, headings, buttons, featured blocks, scrolled header, footer |
| `--gold` | `#C9A227` | On navy: accents, active states, text. On white/bone: only thin lines, frames, icons, bars (never text) |
| `--navy-2`, `--navy-3` | navy 72 % / 58 % | Secondary and tertiary text on light (both ≥ 4.5:1 on white and bone) |
| `--bone-2` | bone 76 % | Secondary text on navy |
| `--line` | navy 12 % | Hairlines on light |

## Typography

- **Hubot Sans** (display: name, section titles, card titles), GitHub's display typeface, used wide and heavy for an editorial voice.
- **Mona Sans** (text), its companion text face, for reading.
- **JetBrains Mono** for data only: token ids, section numbers, metrics, technologies and skills, course names, periods, language codes, repository names.

## Signature elements

1. **Drawn monogram**: the hero SD (`sd-navy.svg` path, unchanged) draws itself once as one continuous stroke (`stroke-dashoffset`). Reduced motion: shown drawn.
2. **The About chat**: section 01 introduces the owner as a chat. Someone asks an AI "Who is Santiago Die?" (translated per page) and the answer is the owner's own About text, three paragraphs starting "Based on my analysis…". Press send and the camera zooms into the message: tokens with their real ids, six-cell embedding vectors, attention arcs and a pulse through four blocks, softmax bars over five candidates, the winner flying into the answer, a flash of the cycle for the next eight tokens, then the rest streamed word by word (about 18 s in all, with small mono stage labels). Then the chat has hit its message limit: a notice with the reset time links to Contact to ask Santiago directly, and the box switches off. All text is in the generated HTML.
3. **Progress line with a trail**: one gold line (1.5px, rounded turns like the monogram) that is drawn as you scroll and retracts when you scroll back. It connects the section numbers, alternating sides on wide screens (01 left, 02 right, ...) and crossing between sections with a rounded monoline turn through the empty band above each heading. Its tip is a small gold point with a soft gold halo and a short fading trail (the one sanctioned glow, see above). When the tip reaches a section number, the number lights up and stays lit; the navigation's current section follows the tip. Decorative: `aria-hidden`, `pointer-events: none`. Below 48em it runs straight down the left margin.
4. **Evidence-first projects**: three featured cards in one row with their README metrics in mono; the rest as small cards that each lead straight to the repository (owner's choice in v2.4: no screenshots on the page).

## Type scale

| Token | Value | Use |
| --- | --- | --- |
| `--step-4` | `clamp(3.25rem, 1.2rem + 8vw, 8.75rem)` | Name (Hubot Sans 750, width 112 %, line-height 0.9) |
| `--step-3` | `clamp(2.25rem, 1.4rem + 3.6vw, 4.5rem)` | Section titles (Hubot Sans 700, width 108 %) |
| `--step-2` | `clamp(1.375rem, 1.2rem + 0.8vw, 1.875rem)` | Sub-heads, entry titles, contact labels |
| `--step-1` | `clamp(1.125rem, 1.05rem + 0.35vw, 1.3125rem)` | Lead text |
| `--step-0` | `1.0625rem` | Body (Mona Sans, line-height 1.65) |
| `--step--1` | `0.8125rem` | Mono labels: section numbers, course, ids, periods |

Optional About text under the chat is set as display copy (Hubot Sans 500, up to 2.5rem). Display headings keep tight leading (0.9–1.2) on purpose.

## Layout and spacing

- Content max width 76rem; side margins `clamp(1.25rem, 5vw, 4rem)` plus safe-area insets; gutter `clamp(1.25rem, 2.5vw, 2rem)`.
- Section padding `clamp(5rem, 11vw, 9rem)`. Sections alternate white / bone in the order they are shown (the build assigns it, so a hidden section never leaves two of the same in a row); Contact and the footer are navy.
- From 64em: 12-column section grid; titles span the full width, text bodies start at column 3, Projects uses the full width.
- Breakpoints: 22.5em (icon-only menu button), 36em (small project cards two across), 48em (entries, skills and contact in columns), 64em (desktop navigation, hero name beside the monogram, featured cards three across, small cards four across). Project grids use fixed column counts, so a last card alone keeps its width and sits on the left. The chat's notice switches from one row to two below a 34rem-wide panel (container query).
- Radii: 6px (chips), 8px (buttons), 10–16px (menus, cards).

## Components

- **Header**: sticky, transparent over the hero (navy logo and links); after 16px of scroll it fades to navy (gold logo, bone links, gold active link with a 1.5px gold rule). Below 64em a "Menu" button opens a navy panel with the links, the social buttons and the language menu.
- **Social buttons**: 40px square, 1px border, 8px radius; on hover or focus they round to a circle, lift 2px, fill (navy on light, bone on navy) and show a mono label below. Inspired by Uiverse.io components by akshat-patel28 and EcheverriaJesus (credited in the CSS).
- **Language menu**: menu button showing the current code; white popover with the three languages as links (`hreflang`, `lang`), the current one marked. Arrows, Home/End, Enter, Escape, click outside. Switching keeps the current section. Without JavaScript there is no button: the three languages are a plain row of links.
- **Language suggestion**: a slim bone bar in the page flow above the header, shown only when the browser prefers another available language; decided by the inline head script before the first paint (no layout shift); dismissal remembered.
- **Hero**: drawn monogram, name, plain role line, primary navy button and quiet underlined link; nothing below them.
- **About chat**: under the section title, in the text column (from 64em columns 3–12, like every other section body, about 1008px at 1440); the conversation keeps a centred 46rem column inside. Navy panel, 22px radius, as tall as the finished chat from the first paint (everything is laid out, only invisible, and the notice keeps its place), so nothing around it moves in any language or width. The conversation is capped at `max(15rem, min(36rem, 100svh − 22rem))`: past that (phones, short windows) it scrolls inside the panel, is followed by the stream as the answer is written, fades at the edges that have more to read, and once finished takes keyboard focus to be scrolled; the notice and the box stay in view below it. At rest a pill box in bone 7 % with the typed question and a 40px gold send button with a navy arrow (48px target), mid-panel. Question bubble in bone with navy text; answer in Mona Sans on navy. Skip and Replay: mono, top-right, 44px. Finished: the **message-limit notice** sits above the box, a thin bar in bone 6 % with a 1px gold edge (60 %) and 14px radius, a monoline gold clock drawn like the monogram (square ends, round joins), the sentence in `--bone-2` and the link in gold, underlined, with an SVG arrow (44px target, gold focus ring); the box dims to 72 % with the placeholder in bone 42 % and the send button turned to a slate disk (bone 22 % over navy). Without JavaScript the chat is shown in that finished state, the notice without a time.
- **Progress line**: see Signature elements. Nodes: a 9px ring on the line at each number (section background fill, gold 1.5px stroke) that fills gold when lit; the number turns from navy 66 % to navy (gold on navy) over 200 ms.
- **Section header sides**: from 48em, even visible sections (02, 04...) set the number and title right-aligned so they meet the line on the right; body text always stays left-aligned for reading. Numbers are assigned by the build to the visible sections only.
- **Featured card**: white, 1px gold border (30 %; the traced frame is full gold), 12px radius; title (translated), course in mono, description, README metrics (value in mono over its label, two across where they fit on one line, otherwise stacked; a value never wraps), technologies (gold dot separators), underlined "Live demo" and "Code" links and the repository name in mono. Three across from 64em, one column below. Hover: lifts 2px, soft shadow, border to full gold.
- **Small project card**: white, hairline border, 12px radius; title, course in mono, technologies, and at the foot the repository name in mono with an arrow (ellipsis if long). The whole card is one link to the repository (the title link's `::after` covers it; no nested links), and its focus ring goes round the card; a project with a demo adds a small underlined "Demo" (or "Colab") link that sits above that layer as a separate target. Four across from 64em, two from 36em, one below. Hover: lifts 2px, gold border, arrow nudges; press scales to 0.985.
- **Entries**: hairline-ruled rows; period in mono in a 12rem column from 48em; title in display type; organisation with the place in tertiary navy; text; Education's line of subjects or track in tertiary navy; Experience's technologies in mono with gold dots. **Certifications** follow Education as a short ruled list under a small mono heading.
- **Skills**: one ruled row per group, the name (display type) in the 12rem column and the items in mono with gold dots; no levels, bars or percentages. **Languages** follow as ruled rows of language and level under a small mono heading.
- **Contact, footer**: hairline-ruled rows with labels in display type and values in mono: Email, GitHub, LinkedIn (gold arrow) and Location (no arrow, not a link); footer with the gold monogram.
- **TODO marker**: dashed gold frame; navy text on light, gold on navy. Kept for any TODO string outside paragraphs and entries; paragraphs and entries marked TODO are not published at all.

## Motion

- Easing: `--ease-out: cubic-bezier(0.23, 1, 0.32, 1)` for UI, `--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1)` for the drawn stroke. Durations: 150 ms (colour), 220 ms (UI), 260 ms (header state, card lift).
- Once per visit: monogram draw (1.6 s), then name, role and actions settle in (10px, 500–700 ms).
- About chat: the section assembles first (number, title, then the panel); the question types itself (34 ms per character) only once the panel has finished appearing and is at least 35 % on screen, then the send button pulses once. The run (about 18 s) uses Web Animations on `transform`, `opacity` and `stroke-dashoffset` only, pauses in a hidden tab and finishes itself if scrolled away; Skip and Escape go to the end. After the camera pulls out, eight tokens flash through the cycle (300 ms, each 20 % faster), then the rest streams in word by word (each word fades in over 220 ms, the pace quickening slightly, a 200 ms breath before each paragraph); its length is fixed, so the whole answer is written 5 s after the pull-out in every language. The notice enters just after the answer (opacity and 6px up, 320 ms, `--ease-out`; reduced motion: opacity only). Focus after a keyboard run or Skip goes to the notice's link, then Replay.
- Section assembly, once per element, triggered as it enters: number and node first, title (+80 ms), text (+160 ms), then cards or entries (+70 ms each, at most 6 staggered). Each moves 12px and fades in over 520 ms with `--ease-out`; card frames trace in 600 ms (`stroke-dashoffset`) before their content. Time-based rather than scroll-scrubbed, so nothing can stop half-visible.
- The progress line never competes with the chat: while the chat animation plays, the line holds its length and hides its tip and trail, then catches up.
- Progress line: drawn with `stroke-dashoffset` from the scroll position, through a CSS scroll timeline where supported, otherwise one `requestAnimationFrame` update per scroll frame; geometry recalculated only on resize (ResizeObserver).
- Menus open slower than they close (220/150 ms; language menu 150–220/120 ms) and grow from their trigger.
- Hover motion only under `(hover: hover) and (pointer: fine)`; presses scale to 0.97.
- `prefers-reduced-motion: reduce`: no movement at all; the logo is shown drawn, the chat's answer and notice fade in without zoom or stages, sections are visible at once, the progress line is complete and still with every number in its normal state.
