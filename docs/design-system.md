# Design System: SikhSituationBot 🪯

This document defines the visual language for the SikhSituationBot, focusing on a premium, spiritual, and modern aesthetic.

## 🎨 Color Palette

The palette uses **Deep Blues** for depth and serenity, with **Gold Accents** to represent the divine light and wisdom of Gurbani.

### Deep Blues (Backgrounds & Primary)
| Color | HSL | Variable | Preview |
| :--- | :--- | :--- | :--- |
| **Midnight** | `hsl(230, 60%, 8%)` | `--midnight` | ![#080c1d](https://via.placeholder.com/15/080c1d/080c1d.png) |
| **Deep Navy** | `hsl(230, 50%, 12%)` | `--navy-deep` | ![#10162f](https://via.placeholder.com/15/10162f/10162f.png) |
| **Navy** | `hsl(230, 45%, 18%)` | `--navy` | ![#19244a](https://via.placeholder.com/15/19244a/19244a.png) |
| **Royal Blue** | `hsl(225, 60%, 28%)` | `--royal` | ![#1c2e73](https://via.placeholder.com/15/1c2e73/1c2e73.png) |

### Gold Accents (Highlights & Spiritual)
| Color | HSL | Variable | Preview |
| :--- | :--- | :--- | :--- |
| **Vibrant Gold** | `hsl(48, 100%, 55%)` | `--gold` | ![#ffcc1a](https://via.placeholder.com/15/ffcc1a/ffcc1a.png) |
| **Bright Gold** | `hsl(48, 100%, 70%)` | `--gold-light` | ![#ffdd66](https://via.placeholder.com/15/ffdd66/ffdd66.png) |
| **Muted Gold** | `hsl(48, 40%, 45%)` | `--gold-muted` | ![#a18c45](https://via.placeholder.com/15/a18c45/a18c45.png) |

## 🧪 CSS implementation (`index.css`)

```css
:root {
  /* Deep Blues */
  --midnight: hsl(230, 60%, 8%);
  --navy-deep: hsl(230, 50%, 12%);
  --navy: hsl(230, 45%, 18%);
  --royal: hsl(225, 60%, 28%);

  /* Gold Accents */
  --gold: hsl(48, 100%, 55%);
  --gold-light: hsl(48, 100%, 70%);
  --gold-muted: hsl(48, 40%, 45%);
  --gold-gradient: linear-gradient(135deg, var(--gold-light), var(--gold));

  /* Text & Surface */
  --text-primary: hsl(0, 0%, 98%);
  --text-secondary: hsl(230, 20%, 75%);
  --surface-glass: hsla(0, 0%, 100%, 0.05);
  --border-glass: hsla(0, 0%, 100%, 0.1);
  
  /* Shadows */
  --shadow-gold: 0 4px 14px 0 hsla(48, 100%, 55%, 0.3);
}
```
