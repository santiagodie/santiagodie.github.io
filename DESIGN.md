# Design

Visual system of santiagodie.com (v2, 2026-10-17; v2.1 additions 2026-10-18). Product context lives in PRODUCT.md.

## Non-negotiable rules

Set by the owner; they win over any recommendation from any design skill. Copied verbatim from the v2 brief (Spanish original). They replace the v1 rules (navy page background).

> - Fondo principal blanco #FFFFFF. Bone #F5F0E1 como fondo secundario para alternar secciones. Navy #0B1F3A para textos, titulares y bloques destacados.
> - Gold #C9A227: solo sobre azul marino, o como detalle decorativo fino (líneas, marcos, iconos) sobre claro. Nunca como color de texto sobre blanco o hueso, porque no tiene contraste suficiente.
> - No se pueden añadir colores nuevos. Logo sin modificar: sd-navy.svg sobre fondos claros y sd-gold.svg sobre azul marino (las versiones de sd-logo\).
> - Prohibido: glassmorphism, neones, degradados de colores, partículas, redes neuronales de fondo, cursores personalizados, scroll-jacking. Respeta prefers-reduced-motion en todo.

Still binding from v1: derived tints (lighter, darker, transparent) of the four colours are allowed, new hues are not; content about the owner is never invented, missing content shows a visible TODO marker; motion is short, purposeful and respects `prefers-reduced-motion`.

v2.1 additions (2026-10-18), also binding. The first one is verbatim from the v2.1 brief:

> - La punta de la línea de progreso: un punto luminoso con un halo dorado suave (drop-shadow o blur del mismo gold con opacidad baja), y detrás una estela que se desvanece en unas decenas de px. Es una excepción a la regla de "sin neones" solo para este elemento: brillo contenido, un solo color, nada de tonos fluorescentes ni degradados multicolor (solo opacidades del gold).

- The hero model animation is presented as "a language model" in general, never as the internals of Claude or of any specific model. Token ids are real (`cl100k_base`); probabilities, embeddings and attention weights are illustrative and the panel says so in a small translated note.
- Every animated thing has a complete static form: without JavaScript or with `prefers-reduced-motion: reduce`, the hero shows the whole pipeline as a static diagram with the final answer, sections are simply there, and the progress line is complete and still.
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
- **JetBrains Mono** for data only: token ids, section numbers, metrics, technologies, periods, language codes.

## Signature elements

1. **Drawn monogram**: the hero SD (`sd-navy.svg` path, unchanged) draws itself once as one continuous stroke (`stroke-dashoffset`). Reduced motion: shown drawn.
2. **Prompt to answer** (`generate()`): the hero explains how a language model turns a prompt ("Who is Santiago Die?", translated per page) into an answer, in eight stages, each a visible transformation of the data: prompt typed with a caret, token chips with real ids, embedding columns plus position, attention arcs and a pulse through a "Transformer × N" stack, logits normalised by softmax over five candidates, sampling at a stated temperature, detokenisation into a streaming answer, and the loop back to the input until `<|endoftext|>`. The first token is explained slowly; the rest run quickly. It plays once when it enters the screen (about 16 s), with pause, replay, previous/next and a clickable stage indicator. The banner's "computer → engineer 0.86" reappears as the step that predicts "engineer". All text is in the generated HTML.
3. **Progress line with a trail**: one gold line (1.5px, rounded turns like the monogram) that is drawn as you scroll and retracts when you scroll back. It connects the section numbers, alternating sides on wide screens (01 left, 02 right, ...) and crossing between sections with a rounded monoline turn through the empty band above each heading. Its tip is a small gold point with a soft gold halo and a short fading trail (the one sanctioned glow, see above). When the tip reaches a section number, the number lights up and stays lit; the navigation's current section follows the tip. Decorative: `aria-hidden`, `pointer-events: none`. Below 48em it runs straight down the left margin.
4. **Evidence-first projects**: three featured cards with a real demo screenshot and README metrics in mono; the rest in a compact grid.

## Type scale

| Token | Value | Use |
| --- | --- | --- |
| `--step-4` | `clamp(3.25rem, 1.2rem + 8vw, 8.75rem)` | Name (Hubot Sans 750, width 112 %, line-height 0.9) |
| `--step-3` | `clamp(2.25rem, 1.4rem + 3.6vw, 4.5rem)` | Section titles (Hubot Sans 700, width 108 %) |
| `--step-2` | `clamp(1.375rem, 1.2rem + 0.8vw, 1.875rem)` | Sub-heads, entry titles, contact labels |
| `--step-1` | `clamp(1.125rem, 1.05rem + 0.35vw, 1.3125rem)` | Lead text |
| `--step-0` | `1.0625rem` | Body (Mona Sans, line-height 1.65) |
| `--step--1` | `0.8125rem` | Mono labels: section numbers, course, ids, periods |

About text is set as display copy (Hubot Sans 500, up to 2.5rem). Display headings keep tight leading (0.9–1.2) on purpose.

## Layout and spacing

- Content max width 76rem; side margins `clamp(1.25rem, 5vw, 4rem)` plus safe-area insets; gutter `clamp(1.25rem, 2.5vw, 2rem)`.
- Section padding `clamp(5rem, 11vw, 9rem)`. Sections alternate white / bone; Contact and the footer are navy.
- From 64em: 12-column section grid; titles span the full width, text bodies start at column 3, Projects uses the full width.
- Breakpoints: 22.5em (icon-only menu button), 48em (hero model in two columns, entries and contact in columns), 64em (desktop navigation, hero name beside the monogram, featured cards side by side).
- Radii: 6px (chips), 8px (buttons), 10–16px (menus, cards).

## Components

- **Header**: sticky, transparent over the hero (navy logo and links); after 16px of scroll it fades to navy (gold logo, bone links, gold active link with a 1.5px gold rule). Below 64em a "Menu" button opens a navy panel with the links, the social buttons and the language menu.
- **Social buttons**: 40px square, 1px border, 8px radius; on hover or focus they round to a circle, lift 2px, fill (navy on light, bone on navy) and show a mono label below. Inspired by Uiverse.io components by akshat-patel28 and EcheverriaJesus (credited in the CSS).
- **Language menu**: menu button showing the current code; white popover with the three languages as links (`hreflang`, `lang`), the current one marked. Arrows, Home/End, Enter, Escape, click outside. Switching keeps the current section.
- **Language suggestion**: a slim bone bar in the page flow above the header, shown only when the browser prefers another available language; decided by the inline head script before the first paint (no layout shift); dismissal remembered.
- **Hero**: drawn monogram, name, plain role line, primary navy button and quiet underlined link, then the `generate()` panel.
- **`generate()` panel**: white, 1px gold frame (30 %), 16px radius. Head: mono label, short title, controls (previous, pause/resume, next, replay; 44px targets) and an eight-step stage indicator (mono numbers; current step navy with a gold rule). Stage caption: mono stage label plus one translated sentence. Canvas with a fixed height per breakpoint (no layout shift): token table (chips with 1px gold frames, ids in mono, six-cell embedding columns in navy opacities, position), attention arcs (gold, opacity and width by weight), `Transformer × N` stack (hairline blocks, a gold pulse), softmax bars (top candidate gold, others navy 22 %), `T = 0.7` in mono, the answer in display type with a caret, and a rounded loop connector back to the input. Footnote: "illustrative values" plus the tokenizer name. From 64em the tokens run left to right with the arcs above them, and the stack, the scores and the answer sit side by side below; from 48em to 64em the regions stack. Under 48em, when animated, the panel is a fixed-height card (about 470 px at 375 px wide, 490 px at 320 px) that shows one stage at a time with a 260 ms fade, a segmented progress bar as the clickable stage indicator, the controls in the header row and the answer always at the bottom; heights are minimums, so enlarged text grows the card instead of clipping it. Without JavaScript or with reduced motion, phones get the full static diagram with its legend.
- **Progress line**: see Signature elements. Nodes: a 9px ring on the line at each number (section background fill, gold 1.5px stroke) that fills gold when lit; the number turns from navy 66 % to navy (gold on navy) over 200 ms.
- **Section header sides**: from 48em, even sections (02, 04, 06) set the number and title right-aligned so they meet the line on the right; body text always stays left-aligned for reading.
- **Featured card**: white, 1px gold frame (30 %, an SVG rect so it can trace itself in), 16px radius; title translated per language, repository name (`santiagodie/<repo>`) in mono beside the buttons; real demo screenshot (WebP, 16:10) beside the body; title, course, description, two README metrics in mono, technologies (gold dot separators), Demo (navy) and Code (outlined) buttons. Hover: lifts 3px, soft shadow, frame to full gold.
- **Project card**: white, hairline border, 12px radius; title, course, description, technologies, underlined links. Hover: lifts 2px, gold border.
- **Entries, skills, contact, footer**: hairline-ruled rows; periods in mono; contact labels in display type with a gold arrow; footer with the gold monogram.
- **TODO marker**: dashed gold frame; navy text on light, gold on navy.

## Motion

- Easing: `--ease-out: cubic-bezier(0.23, 1, 0.32, 1)` for UI, `--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1)` for the drawn stroke. Durations: 150 ms (colour), 220 ms (UI), 260 ms (header state, card lift).
- Once per visit: monogram draw (1.6 s), then name, role and actions settle in (10px, 500–700 ms).
- `generate()` timeline: about 16 s, starts when the panel is mostly on screen, plays once, pauses off screen or in a hidden tab; stage changes fade in 220–320 ms with `--ease-out`, bars move with `scaleX` in 420 ms, the pulse travels with `--ease-in-out`.
- Section assembly, once per element, triggered as it enters: number and node first, title (+80 ms), text (+160 ms), then cards or entries (+70 ms each, at most 6 staggered). Each moves 12px and fades in over 520 ms with `--ease-out`; card frames trace in 600 ms (`stroke-dashoffset`) before their content. Time-based rather than scroll-scrubbed, so nothing can stop half-visible.
- The progress line never competes with the hero: while the `generate()` animation plays on screen, the line holds its length and hides its tip and trail, then catches up.
- Progress line: drawn with `stroke-dashoffset` from the scroll position, through a CSS scroll timeline where supported, otherwise one `requestAnimationFrame` update per scroll frame; geometry recalculated only on resize (ResizeObserver).
- Menus open slower than they close (220/150 ms; language menu 150–220/120 ms) and grow from their trigger.
- Hover motion only under `(hover: hover) and (pointer: fine)`; presses scale to 0.97.
- `prefers-reduced-motion: reduce`: no movement at all; the logo is shown drawn, the hero model is a complete static diagram, sections are visible at once, the progress line is complete and still with every number in its normal state.
