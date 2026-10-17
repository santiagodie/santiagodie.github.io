# Design

Visual system of santiagodie.com. Product context lives in PRODUCT.md.

## Non-negotiable rules

These rules were set by the owner and win over any recommendation from any design skill. They are copied verbatim from the brief (Spanish original).

> 1. Paleta, exactamente estos colores:
>    - Navy #0B1F3A: fondo principal.
>    - Gold #C9A227: acentos. Regla: el dorado solo va sobre el azul marino.
>    - Bone #F5F0E1: texto principal.
>    - White #FFFFFF.
>    Puedes derivar matices (más claros u oscuros, con transparencia) de estos cuatro, pero no añadas colores nuevos.
> 2. Logo: sd-logo\sd-gold.svg, sin modificarlo (ni proporciones, ni trazo, ni color salvo las versiones existentes en sd-logo\). Va en la cabecera, en el footer y como favicon.
> 3. Coherencia con mi perfil de GitHub: revisa assets/ del repo de perfil (santiagodie\santiagodie): header.svg, footer.svg y tools/make_banner.py (marco fino dorado, esquinas redondeadas, sobriedad).
> 4. Nada de efectos llamativos: sin glassmorphism, sin neones, sin degradados de colores, sin partículas, sin redes neuronales de fondo, sin cursores personalizados, sin scroll-jacking.
> 5. Animaciones discretas, cortas y con propósito (aparición de secciones, hover, cambio de idioma), respetando prefers-reduced-motion.
> 6. Contenido: no inventes nada sobre mí. Donde falte información, pon un marcador claro (TODO).

Design direction from the same brief: minimal, sober and editorial; quality comes from typography, spacing, hierarchy and detail, not effects. Plenty of white space, a clear grid, few elements per screen, each with a reason.

## Color

Dark only, by brand: the navy is the page. All tokens are in `css/styles.css` `:root`.

| Token | Value | Use |
| --- | --- | --- |
| `--navy` | `#0B1F3A` | Page and header background |
| `--gold` | `#C9A227` | Hero role line, short rules, frames, focus ring, active language and nav state, "·" separators, link hover, TODO markers |
| `--bone` / `--text` | `#F5F0E1` | Primary text |
| `--white` | `#FFFFFF` | Hover text on links and the primary button; text selection |
| `--text-2` | bone 76 % | Secondary text (descriptions, values) |
| `--text-3` | bone 60 % | Tertiary text (mono labels, periods); ~5:1 on navy |
| `--line` / `--line-strong` | bone 12 % / 22 % | Hairlines, card borders |
| `--gold-frame` / `--gold-frame-inner` | gold 90 % / 38 % | Double hero frame (outer / inner) |
| `--gold-line`, `--gold-hover`, `--gold-soft` | gold 35 % / 55 % / 12 % | Header hairline on scroll, card hover border, primary button hover fill |
| `--surface` | bone 2.5 % | Card fill |

Gold never sits on anything but navy (or a navy-derived surface). Text on gold is never used.

## Typography

- **Mona Sans** (Google Fonts, variable weight and width): all reading and display text. It is GitHub's own typeface, which ties the site to the GitHub profile. The name uses width 108 % for a slightly expanded display voice.
- **JetBrains Mono**: data only: technologies, course labels, periods, language codes, URLs in Contact, TODO markers, footer.
- Scale (fluid, ratio ≈ 1.25): `--step-4` name `clamp(2.75rem → 5.5rem)`, `--step-3` section titles `clamp(1.75rem → 2.5rem)`, `--step-2` card and contact labels, `--step-1` lead text, `--step-0` body 17px, `--step--1` mono 13px.
- Body line-height 1.6, reading measure ≤ 62ch, `text-wrap: balance` on headings and `pretty` on paragraphs.

## Layout

- Content max width 72rem; side margins `clamp(1.25rem, 5vw, 4rem)` plus safe-area insets.
- From 60em: 12-column section grid. Section title spans 3 columns and stays sticky; content spans 9.
- Section spacing `clamp(4.5rem, 14vw, 10rem)`; 4-pt spacing scale `--space-1` … `--space-10`.
- Breakpoints: 22.5em (very narrow phones: icon-only menu button), 48em (two-column cards, two-column entries, hero monogram), 60em (inline navigation, section grid).

## Components

- **Header**: fixed, solid navy; logo, section links, `EN ES FR` in mono. A gold hairline appears once the page scrolls. Below 60em, a "Menu" button opens a panel under the header (not a modal; Escape and outside click close it).
- **Hero plate**: the GitHub-banner frame made into a page: 1px gold outer frame with 6px corners, a second frame 6px inside at lower opacity and 3px corners. Name, 44px gold rule, gold role line, two actions (bordered gold primary, underlined quiet secondary). From 48em a vertical gold hairline and the monogram on the right, as in `make_banner.py`.
- **Project card**: hairline border, 6px corners, faint bone fill; title, course line in mono, description, technologies in mono separated by gold "·", links row (Code, Live demo / Open in Colab) with a drawn arrow icon. Hover and focus-within turn the border gold.
- **Entry rows** (Experience, Education): period in mono on the left, title, organisation and text on the right, separated by hairlines.
- **Contact rows**: large label, mono value, gold arrow; the CV row shows a TODO until `contact.cvFile` is set.
- **TODO marker**: strings starting with `TODO:` render a dashed gold `TODO` chip and dim the rest.
- **Buttons and targets**: ≥ 44px tall; focus ring 2px gold, 3px offset.

## Motion

- One authored moment on load: the gold rule under the name draws in (scaleX, 700 ms) while name, role and actions settle 10px upward with a short stagger. Runs once per visit.
- Sections settle 10px with opacity (500 ms) the first time they enter the viewport; project cards stagger 50 ms.
- Language change: text fades and blurs 2px out and back (120 ms).
- Hover: colour changes 150 ms; arrow icons nudge 2px. Gated behind `(hover: hover) and (pointer: fine)`.
- Easing `cubic-bezier(0.23, 1, 0.32, 1)`. Menu opens in 220 ms and closes in 150 ms.
- `prefers-reduced-motion: reduce`: no movement at all (no entrance, reveal, nudge, press scale or menu slide); opacity fades remain because they explain changes.

## Assets

- `img/sd-gold.svg` and `favicon.svg`: byte-identical copies of `sd-logo/sd-gold.svg`.
- `favicon.ico` (16/32/48) and `apple-touch-icon.png` (180): from the existing `sd-avatar-gold-on-navy-1024.png`.
- `og-image.png` (1200×630): rendered from `tools/og-image.html` with headless Chrome.
- `assets/banner.svg`: README banner from `santiagodie/tools/make_banner.py`.
