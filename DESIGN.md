---
name: Media Trust Framework
colors:
  surface: '#f8f9ff'
  surface-dim: '#cbdbf5'
  surface-bright: '#f8f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#eff4ff'
  surface-container: '#e5eeff'
  surface-container-high: '#dce9ff'
  surface-container-highest: '#d3e4fe'
  on-surface: '#0b1c30'
  on-surface-variant: '#424656'
  inverse-surface: '#213145'
  inverse-on-surface: '#eaf1ff'
  outline: '#727687'
  outline-variant: '#c2c6d8'
  surface-tint: '#0054d6'
  primary: '#0050cb'
  on-primary: '#ffffff'
  primary-container: '#0066ff'
  on-primary-container: '#f8f7ff'
  inverse-primary: '#b3c5ff'
  secondary: '#006c49'
  on-secondary: '#ffffff'
  secondary-container: '#6cf8bb'
  on-secondary-container: '#00714d'
  tertiary: '#a33200'
  on-tertiary: '#ffffff'
  tertiary-container: '#cc4204'
  on-tertiary-container: '#fff6f4'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#dae1ff'
  primary-fixed-dim: '#b3c5ff'
  on-primary-fixed: '#001849'
  on-primary-fixed-variant: '#003fa4'
  secondary-fixed: '#6ffbbe'
  secondary-fixed-dim: '#4edea3'
  on-secondary-fixed: '#002113'
  on-secondary-fixed-variant: '#005236'
  tertiary-fixed: '#ffdbd0'
  tertiary-fixed-dim: '#ffb59d'
  on-tertiary-fixed: '#390c00'
  on-tertiary-fixed-variant: '#832600'
  background: '#f8f9ff'
  on-background: '#0b1c30'
  surface-variant: '#d3e4fe'
typography:
  headline-lg:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: -0.02em
  headline-md:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: '1.3'
    letterSpacing: -0.01em
  headline-sm:
    fontFamily: Inter
    fontSize: 18px
    fontWeight: '600'
    lineHeight: '1.4'
    letterSpacing: '0'
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: '1.6'
    letterSpacing: '0'
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: '1.5'
    letterSpacing: '0'
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: '1.4'
    letterSpacing: 0.02em
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: '1.2'
    letterSpacing: 0.05em
rounded:
  sm: 0.125rem
  DEFAULT: 0.25rem
  md: 0.375rem
  lg: 0.5rem
  xl: 0.75rem
  full: 9999px
spacing:
  unit: 8px
  container-max: 1280px
  gutter: 24px
  margin-page: 40px
  stack-sm: 8px
  stack-md: 16px
  stack-lg: 32px
---

## Brand & Style

The brand personality is rooted in journalistic integrity and digital security. The target audience includes media professionals, fact-checkers, and discerning consumers who require immediate clarity regarding the origin of digital assets. The UI evokes a sense of "quiet authority"—it is unobtrusive, allowing the media content to remain the focus while providing a rigorous layer of verification.

The design style is **Corporate Modern with Minimalist influences**. It prioritizes heavy whitespace and a restricted color palette to minimize cognitive load. Every element serves a functional purpose, avoiding unnecessary decoration to maintain a high level of perceived reliability and "trustworthy" precision.

## Colors

The palette is designed to communicate stability and verification status through high-contrast functional colors against a sterile, professional backdrop.

- **Primary (Blue):** Used exclusively for primary actions, navigation anchors, and active states. It represents the "engine" of the authentication process.
- **Success (Emerald Green):** Reserved strictly for "Authenticated" or "Verified" statuses. It provides a high-signal confirmation of trust.
- **Neutrals:** A range of cool greys (Slate) is used to establish hierarchy without introducing visual noise. 
- **Backgrounds:** Pure white is used for the primary canvas to maximize legibility, while light grey surfaces differentiate secondary content areas or metadata panels.

## Typography

This design system utilizes **Inter** for its exceptional legibility and systematic, utilitarian feel. The typographic scale is tightly controlled to ensure information density remains manageable.

- **Headlines:** Use a semi-bold weight with slight negative letter-spacing to create a compact, authoritative appearance.
- **Body Text:** Standardized on 16px for long-form reading and 14px for metadata and descriptions to ensure accessibility.
- **Labels:** Small caps or increased letter-spacing should be used for labels (e.g., "TIMESTAMP" or "ORIGIN") to distinguish data headers from the data itself.

## Layout & Spacing

The layout follows a **Fixed Grid** model for desktop views to maintain a centered, editorial focus, transitioning to a fluid model for mobile. 

- **Grid:** A 12-column system is used for content organization.
- **Rhythm:** An 8px base unit governs all spatial relationships. 
- **Density:** High whitespace is encouraged around media assets to signify "room to breathe," while data-heavy sidebars utilize tighter spacing (8px or 16px) to keep information visible without scrolling.

## Elevation & Depth

To maintain a "trustworthy" and grounded feel, the design system avoids heavy shadows or distracting blurs.

- **Low-Contrast Outlines:** Surfaces are primarily defined by 1px borders in `Slate-200` (#E2E8F0). This creates a flat, architectural structure.
- **Tonal Layering:** Depth is achieved by placing white cards on top of light grey (`Slate-50`) backgrounds.
- **Interaction Shadows:** Very soft, high-diffusion shadows (0px 4px 12px rgba(0,0,0,0.05)) are permitted only on floating elements like dropdowns or active modals to indicate temporary elevation.

## Shapes

The shape language is disciplined and consistent. A **moderate 8px (0.5rem) radius** is applied to almost all UI components, including buttons, input fields, and cards. This curvature softens the technical nature of the product without making it appear overly casual or "playful." Larger containers like main media viewing areas may use the same 8px radius to maintain a unified visual language.

## Components

- **Buttons:** Primary buttons use the solid action blue with white text. Secondary buttons use a white fill with a 1px border. There is no "ghost" button for primary actions; every action must feel deliberate.
- **Status Chips:** The "Authenticated" chip features a light emerald background with dark emerald text and a leading checkmark icon. It is the most distinct element in the UI.
- **Input Fields:** Use a white background with a subtle grey border. On focus, the border transitions to the primary blue with a 2px offset "halo" effect.
- **Cards:** Used to wrap media assets and their associated metadata. Cards should have no shadow, utilizing a 1px border for definition.
- **Authentication Timeline:** A vertical list component using "stepper" logic to show the chain of custody. Verified nodes use the emerald green theme.
- **Data Tables:** Clean, header-less or subtle-header tables for displaying technical metadata (hash values, camera EXIF data), using the `label-sm` typographic style for keys.