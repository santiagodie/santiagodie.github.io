# Design

Visual system of santiagodie.com (v2, 2026-10-17). Product context lives in PRODUCT.md.

## Non-negotiable rules

Set by the owner; they win over any recommendation from any design skill. Copied verbatim from the v2 brief (Spanish original). They replace the v1 rules (navy page background).

> - Fondo principal blanco #FFFFFF. Bone #F5F0E1 como fondo secundario para alternar secciones. Navy #0B1F3A para textos, titulares y bloques destacados.
> - Gold #C9A227: solo sobre azul marino, o como detalle decorativo fino (líneas, marcos, iconos) sobre claro. Nunca como color de texto sobre blanco o hueso, porque no tiene contraste suficiente.
> - No se pueden añadir colores nuevos. Logo sin modificar: sd-navy.svg sobre fondos claros y sd-gold.svg sobre azul marino (las versiones de sd-logo\).
> - Prohibido: glassmorphism, neones, degradados de colores, partículas, redes neuronales de fondo, cursores personalizados, scroll-jacking. Respeta prefers-reduced-motion en todo.

Still binding from v1: derived tints (lighter, darker, transparent) of the four colours are allowed, new hues are not; content about the owner is never invented, missing content shows a visible TODO marker; motion is short, purposeful and respects `prefers-reduced-motion`.

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
2. **Tokenized headline**: the role line rendered as `tokenize()` chips with thin borders and real cl100k_base ids, plus a `predict_next()` panel with the banner's probabilities. All of it is text in the generated HTML.
3. **Pipeline thread**: a thin gold line in the logo's stroke language that runs through the section numbers as you scroll (CSS scroll-driven animation where supported, static line elsewhere). Decorative, never blocks scrolling.
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
- **Language suggestion**: fixed toast, white with a thin border, shown only when the browser prefers another available language; dismissal remembered.
- **Hero**: drawn monogram, name, `tokenize()` chips (1px gold frames, sub-word tokens 2px apart, ids below in mono), `predict_next()` panel behind a gold hairline (top bar gold, others navy 22 %), primary navy button and quiet underlined link.
- **Pipeline thread**: 1.5px gold line at the left of the content, leaving the hero with a 14px rounded turn, with a 9px gold node at each section number.
- **Featured card**: white, 1px gold frame (30 %), 16px radius; real demo screenshot (WebP, 16:10) beside the body; title, course, description, two README metrics in mono, technologies (gold dot separators), Demo (navy) and Code (outlined) buttons. Hover: lifts 3px, soft shadow, frame to full gold.
- **Project card**: white, hairline border, 12px radius; title, course, description, technologies, underlined links. Hover: lifts 2px, gold border.
- **Entries, skills, contact, footer**: hairline-ruled rows; periods in mono; contact labels in display type with a gold arrow; footer with the gold monogram.
- **TODO marker**: dashed gold frame; navy text on light, gold on navy.

## Motion

- Easing: `--ease-out: cubic-bezier(0.23, 1, 0.32, 1)` for UI, `--ease-in-out: cubic-bezier(0.77, 0, 0.175, 1)` for the drawn stroke. Durations: 150 ms (colour), 220 ms (UI), 260 ms (header state, card lift).
- Once per visit: monogram draw (1.6 s), then name, tokens (45 ms stagger), prediction bars and actions settle in (10px, 500–800 ms); the caret blinks four times and stops.
- Scroll-driven (CSS `animation-timeline: view()`): the thread draws through each section and its node fills; static where unsupported.
- Menus open slower than they close (220/150 ms; language menu 150–220/120 ms) and grow from their trigger.
- Hover motion only under `(hover: hover) and (pointer: fine)`; presses scale to 0.97.
- `prefers-reduced-motion: reduce`: no movement at all; the logo is shown drawn, content is visible at once, opacity fades remain.
