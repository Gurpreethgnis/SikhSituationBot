# Design Tokens Specification 🪯

This document serves as the single source of truth for the **SikhSituationBot** design language. These tokens are implemented as CSS variables in `client/src/index.css`.

## 🎨 Color Tokens

### Core Palette (Deep Blues)
Deep, contemplative blues inspired by the night sky and the spiritual depth of the Ocean of Gurbani.

| Token | HSL | Hex Equivalent | Usage |
| :--- | :--- | :--- | :--- |
| `midnight` | `hsl(230, 60%, 8%)` | `#080c1d` | App background, primary depth |
| `navy-deep` | `hsl(230, 50%, 12%)` | `#10162f` | Card backgrounds, elevated surfaces |
| `navy` | `hsl(230, 45%, 18%)` | `#19244a` | Secondary surfaces, borders |
| `royal` | `hsl(225, 60%, 28%)` | `#1c2e73` | Primary brand color, headers |

### Accent Palette (Gold)
Vibrant golds representing the Divine Light (`Joti`), wisdom, and spiritual value.

| Token | HSL | Hex Equivalent | Usage |
| :--- | :--- | :--- | :--- |
| `gold` | `hsl(48, 100%, 55%)` | `#ffcc1a` | Primary actions, icons, highlights |
| `gold-light` | `hsl(48, 100%, 70%)` | `#ffdd66` | Hover states, gradients |
| `gold-muted` | `hsl(48, 40%, 45%)` | `#a18c45` | Decorative borders, secondary text |

---

## 🔠 Typography Tokens

We use a dual-font system to balance modern readability with spiritual elegance.

| Attribute | Token | Value |
| :--- | :--- | :--- |
| **Primary Font** | `font-body` | `'Inter', system-ui, sans-serif` |
| **Heading Font** | `font-display` | `'Outfit', sans-serif` |
| **Size: XS** | `size-xs` | `0.75rem` (12px) |
| **Size: SM** | `size-sm` | `0.875rem` (14px) |
| **Size: Base** | `size-base` | `1rem` (16px) |
| **Size: LG** | `size-lg` | `1.125rem` (18px) |
| **Size: XL** | `size-xl` | `1.25rem` (20px) |
| **Size: 2XL** | `size-2xl` | `1.5rem` (24px) |

---

## 📐 Layout & Spacing

Based on a 4px / 8px grid system.

| Token | Value | Visual Equivalent |
| :--- | :--- | :--- |
| `space-1` | `0.25rem` | 4px |
| `space-2` | `0.5rem` | 8px |
| `space-4` | `1rem` | 16px |
| `space-6` | `1.5rem` | 24px |
| `space-8` | `2rem` | 32px |

---

## ✨ Effects & Surfaces

### Glassmorphism
Used for chat bubbles and floating panels to maintain depth over the radial background.

| Token | Value |
| :--- | :--- |
| `glass-bg` | `hsla(0, 0%, 100%, 0.03)` |
| `glass-blur` | `blur(12px)` |
| `glass-border` | `1px solid hsla(0, 0%, 100%, 0.08)` |

### Radii
| Token | Value |
| :--- | :--- |
| `radius-sm` | `4px` |
| `radius-md` | `8px` |
| `radius-lg` | `16px` |
| `radius-full` | `9999px` |

### Shadows & Glows
| Token | Value |
| :--- | :--- |
| `shadow-gold` | `0 0 20px hsla(48, 100%, 55%, 0.4)` |
| `shadow-navy` | `0 10px 30px hsla(230, 60%, 5%, 0.5)` |

---

## 🏗️ UI Components (Preview Specs)

### Perspective Pills (Child, Teen, Adult)
The persona switching system uses a pill-based toggle bar.

**Visual Specs:**
- **Container**: `borderRadius: 99px`, `bg: hsla(230, 50%, 5%, 0.3)`, `border: var(--border-glass)`
- **Inactive Pill**: `color: var(--text-secondary)`, `bg: transparent`, `font: var(--font-display) 600`
- **Active Pill**: `bg: var(--gold-gradient)`, `color: var(--midnight)`, `boxShadow: var(--gold-glow)`
- **Interaction**: Smooth scale and color transition on hover/active.

**Implementation Class**: `.perspective-pill`

---

## ⌨️ Developer Implementation

These tokens are exposed in `:root` inside `client/src/index.css`. Use them like so:

```css
.card {
  background: var(--navy-deep);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  color: var(--text-primary);
}

.button-gold {
  background: var(--gold-gradient);
  box-shadow: var(--shadow-gold);
}
```
