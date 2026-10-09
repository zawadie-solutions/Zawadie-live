---
name: Kinship & Memory
colors:
  surface: '#fcf9f4'
  surface-dim: '#dcdad5'
  surface-bright: '#fcf9f4'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f6f3ee'
  surface-container: '#f0ede9'
  surface-container-high: '#ebe8e3'
  surface-container-highest: '#e5e2dd'
  on-surface: '#1c1c19'
  on-surface-variant: '#54433e'
  inverse-surface: '#31302d'
  inverse-on-surface: '#f3f0eb'
  outline: '#87736d'
  outline-variant: '#dac1ba'
  surface-tint: '#944931'
  primary: '#91462f'
  on-primary: '#ffffff'
  primary-container: '#af5e45'
  on-primary-container: '#fffbff'
  inverse-primary: '#ffb59f'
  secondary: '#835400'
  on-secondary: '#ffffff'
  secondary-container: '#fcba5f'
  on-secondary-container: '#734900'
  tertiary: '#4b5f69'
  on-tertiary: '#ffffff'
  tertiary-container: '#637882'
  on-tertiary-container: '#fbfdff'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#ffdbd0'
  primary-fixed-dim: '#ffb59f'
  on-primary-fixed: '#3a0a00'
  on-primary-fixed-variant: '#76321d'
  secondary-fixed: '#ffddb5'
  secondary-fixed-dim: '#fcba5f'
  on-secondary-fixed: '#2a1800'
  on-secondary-fixed-variant: '#643f00'
  tertiary-fixed: '#d0e6f1'
  tertiary-fixed-dim: '#b5cad5'
  on-tertiary-fixed: '#091e26'
  on-tertiary-fixed-variant: '#364a53'
  background: '#fcf9f4'
  on-background: '#1c1c19'
  surface-variant: '#e5e2dd'
typography:
  display-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 40px
    fontWeight: '700'
    lineHeight: 48px
    letterSpacing: -0.02em
  display-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 30px
    fontWeight: '700'
    lineHeight: 38px
    letterSpacing: -0.015em
  headline-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
    letterSpacing: -0.015em
  headline-lg-mobile:
    fontFamily: Plus Jakarta Sans
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
    letterSpacing: -0.01em
  headline-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 30px
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '600'
    lineHeight: 26px
    letterSpacing: '0'
  body-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 18px
    fontWeight: '400'
    lineHeight: 28px
    letterSpacing: '0'
  body-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 15px
    fontWeight: '400'
    lineHeight: 24px
    letterSpacing: '0'
  body-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 13px
    fontWeight: '400'
    lineHeight: 20px
    letterSpacing: 0.005em
  label-lg:
    fontFamily: Plus Jakarta Sans
    fontSize: 14px
    fontWeight: '600'
    lineHeight: 20px
    letterSpacing: 0.01em
  label-md:
    fontFamily: Plus Jakarta Sans
    fontSize: 12px
    fontWeight: '600'
    lineHeight: 16px
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Plus Jakarta Sans
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
    letterSpacing: 0.03em
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1.5rem
  gutter-sm: 1rem
  gutter-lg: 2rem
  margin: 2rem
  margin-mobile: 1rem
  margin-tablet: 1.5rem
  margin-desktop: 3rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2.5rem
---

## Brand & Style

This design system frames biometric comparison through the respectful lens of family archives, ancestry discovery, and personal memory preservation. It deliberately avoids forensic, surveillance, or stark law-enforcement visual metaphors—dispensing with crosshairs, bounding-box reticles, glowing neon scans, and stark utilitarian telemetry. Instead, the UI evokes an archival workspace: physical linen folders, gentle natural lighting, and tactile mountboards.

The target audience includes genealogists, family historians, and everyday individuals exploring vintage family scrapbooks or rediscovering long-lost relatives across generations. The visual response must be deeply reassuring, confidential, warm, and humanistic.

The aesthetic blends **Modern Editorial Warmth** with **Tactile Archival Craft**:
- Generous cream and warm linen backdrops that alleviate eye fatigue and suggest archival-grade paper.
- Thoughtfully sculpted cards with soft organic perimeters, faint parchment-tone borders, and diffuse ambient dropshadows reminiscent of stacked photographic prints.
- Quiet, respectful privacy cues prioritizing user agency, explicit local processing notices, and clear, humanized certainty disclosures over clinical percentages.

## Colors

The palette draws directly from heritage darkrooms, natural cotton rag mats, and sun-warmed earth:

- **Canvas & Surfaces**: The foundation is anchored on `#FBF8F3` (Alabaster Linen), with secondary card elevations using `#FFFFFF` (Crisp Mountboard) and muted recessed containers resting on `#F3EEE6` (Warm Parchment).
- **Ink & Typography**: All primary copy renders in deep charcoal-umber `#1F2421` (Archive Charcoal), maintaining WCAG AAA contrast against the cream ground while eliminating the harsh clinical bite of pure black. Secondary and metadata text uses `#575B57` (Weathered Stone).
- **Primary Accent (`#C26D53`)**: A sunbaked terracotta clay used for primary actions, curated comparisons, and focus points. It radiates warmth, antiquity, and care.
- **Secondary Accent (`#D99B43`)**: A gentle antique amber that provides nuanced emphasis for in-progress states, multi-face resolution suggestions, and archival notes.
- **Tertiary Accent (`#5A6E78`)**: A calm, dusty slate-blue that stabilizes analytical framing, side-by-side inspection borders, and neutral informative banners.
- **Semantic Indicators**:
  - *Match / Confirmation*: Deep forest emerald (`#2C6E49`) set over pale herbal sage (`#EBF5EE`).
  - *Divergence / Non-Match*: Soft rose-madder (`#A64242`) set over muted vintage rose (`#FAECEC`).
  - *Guidance / Advisory*: Warm ochre (`#926017`) set over pale sunlight linen (`#FDF6E9`).

## Typography

The design system standardizes on **Plus Jakarta Sans** across all roles. Its geometric backbone combined with subtle, friendly humanist terminals conveys technical competence without clinical coldness.

- **Headlines & Display**: Set with tighter letter spacing and medium-bold weights to ground titles with the stability of printed museum labels.
- **Body Text**: Tuned with generous line heights (`1.5` to `1.6`) to ensure comfortable reading across archival descriptions, personal notes, and match narratives.
- **Labels & Badges**: Employs uppercase-accented micro-tracking (`+0.02em` to `+0.03em`) on smaller sizes to maintain rapid glanceability on confidence pills, file formats, and historical timeline indicators.

## Layout & Spacing

The layout philosophy mirrors an intentional archival collector's desk: organized, spacious, and unhurried. 

- **Grid Model**: A responsive 12-column fluid grid system bounded by a max container width of `1280px` for discovery and utility screens, expanding to `1440px` for side-by-side photo inspection canvases. Element pairs (such as Reference Photo vs. Comparison Subject) map naturally to a balanced 6/6 split on desktop screens.
- **Breakpoints**:
  - `Mobile` (< `640px`): Single-column presentation, stacked photo inspection, minimum outer margin (`1rem`), and tight component padding to prioritize photo viewport area.
  - `Tablet` (`640px` - `1024px`): 8-column layout, contextual side-by-side or tabs for inspection, `1.5rem` margins.
  - `Desktop` (> `1024px`): Full 12-column layout with pinned comparison modules, inspector side-panels, and generous `3rem` canvas breathing room.
- **Vertical Rhythm**: Generous vertical spacing (`space-lg` and `space-xl`) isolates core comparison modules, ensuring users never feel hurried or visually overwhelmed during emotionally meaningful evaluations.

## Elevation & Depth

Visual hierarchy relies on warm tactile layering rather than synthetic neon or dramatic drop shadows.

- **Tonal Layers**: The primary interface canvas lives on `#FBF8F3`. Interactive modules and photo wells elevate using `#FFFFFF` surfaces bounded by hairline borders (`#EADFD3`). Recessed preview docks and drag-and-drop landing areas descend into `#F3EEE6`.
- **Ambient Warm Shadows**: Shadows emulate soft daylight diffused through museum-grade glass:
  - *Base Cards*: `0 2px 8px -2px rgba(50, 40, 30, 0.05), 0 1px 3px 0 rgba(50, 40, 30, 0.03)`
  - *Active Photo Docks & Modals*: `0 12px 28px -6px rgba(50, 40, 30, 0.08), 0 4px 12px -2px rgba(50, 40, 30, 0.04)`
  - *Elevated Draggable Items*: `0 20px 32px -8px rgba(50, 40, 30, 0.12)`
- **Soft Outlines**: Crisp 1px borders colored in translucent warm sepia (`rgba(80, 60, 45, 0.08)`) frame all surfaces, delivering physical edge definition without harsh line work.

## Shapes

The design system incorporates **Level 2 (Rounded)** shape metrics to evoke smoothly trimmed photographic paper, vintage carte-de-visite corners, and approachable editorial cards:

- **Base Radius (`0.5rem` / `8px`)**: Input text fields, dropdown trigger buttons, tooltips, and secondary action chips.
- **Large Radius (`rounded-lg`, `1rem` / `16px`)**: Archival comparison cards, photograph presentation frames, contextual guidance drawers, and upload zones.
- **Extra Large Radius (`rounded-xl`, `1.5rem` / `24px`)**: Primary inspection panels, floating results summaries, and dialog windows.
- **Full Pill (`9999px`)**: Semantic verification chips, privacy status badges, and circular zoom/crop action anchors.

## Components

### Buttons & Interactive Triggers
- **Primary Action (Terracotta)**: Solid `#C26D53` fill with white text (`#FFFFFF`), subtle hover transition to `#B05C43`, active state scaling to `0.99`. No high-contrast glow; uses a gentle warm focus ring (`3px` solid `rgba(194, 109, 83, 0.25)`).
- **Secondary Action (Linen Outline)**: White background `#FFFFFF`, subtle `#E0D4C5` border, charcoal text `#1F2421`. On hover, background shifts to `#F8F3EC`.
- **Tertiary / Ghost**: Transparent fill with muted charcoal `#575B57`, transitioning to a warm parchment tint on hover.

### Photo Comparison Cards & Wells
- **Photo Display**: Wrapped in 16px rounded borders with an archival matting effect: `8px` of white padding around the image frame before encountering a `1px` inner sepia border (`rgba(80, 60, 45, 0.08)`).
- **Comparison Splitter**: A tactile centered handle with a soft amber-tinted thumb slider, devoid of medical or biometric calibration hash marks.

### Semantic Pill Badges
- **Match Pill**: Pill radius (`9999px`), `4px 12px` padding. Solid pale herbal ground (`#EBF5EE`), deep emerald label (`#2C6E49`), accompanied by a soft leaf or double-check glyph. Copy reads "Strong Likeness" or "Consistent Features" instead of cold probability percentages.
- **Non-Match Pill**: Pill radius, pale vintage rose (`#FAECEC`), deep rose-madder label (`#A64242`). Labeled gently as "Distinct Features" or "Different Subject".
- **Guidance Pill (Multiple Faces / Low Light)**: Warm daylight ground (`#FDF6E9`), dark ochre label (`#926017`). Signals multiple subjects available for selection or offers tips on portrait angles.

### Input Fields & Upload Drag-Drop Zones
- **Upload Drop Zone**: Dashed perimeter (`2px`) with a soft `#D6C7B6` tint, resting on `#FAF6F0`. Features friendly archival camera or album illustrations rather than sterile upload arrows.
- **Text & Meta Fields**: Cream-white base (`#FFFFFF`) with `#DBCFC2` default borders, expanding gently to a `#C26D53` focus ring. Text matches `#1F2421` with `#787570` placeholders.

### Checkboxes & Radios
- Soft square (`6px` radius for checkboxes) and true circular radios with `#C26D53` active fills, displaying a soft ivory inner indicator. 

### Privacy & Trust Reassurance Banners
- Dedicated subtle panels colored in `#EEF2F4` with `#5A6E78` icons and text. Explicitly certifies: "Photographs remain your private family memory. No biometric data is ever stored, sold, or shared."