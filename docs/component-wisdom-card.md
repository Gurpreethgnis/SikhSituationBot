# Component Specification: Gurbani Wisdom Card 📜

This document defines the technical and visual requirements for the `ShabadCard` component, the primary way Gurbani is presented to the user.

---

## 🏗️ Structure (The Markup)

The component should be structured to handle multiple layers of information while maintaining a clean, sacred hierarchy.

```html
<article class="shabad-card [persona-class]">
  <!-- 1. Spiritual Anchor -->
  <header class="card-header">
    <div class="ik-onkar-icon">ੴ</div>
  </header>

  <!-- 2. Scripture Section -->
  <section class="scripture-content">
    <h2 class="gurmukhi-text">ਸਤਿਨਾਮੁ ਕਰਤਾ ਪੁਰਖੁ ਨਿਰਭਉ ਨਿਰਵੈਰੁ...</h2>
    <p class="transliteration">Satinaamu karataa purakhu nirabhau niravairu...</p>
    <blockquote class="translation">True is His Name, Creative Being, Without Fear, Without Hatred...</blockquote>
  </section>

  <!-- 3. AI Insights (Guided by Persona) -->
  <footer class="ai-insight">
    <div class="insight-label">AI Perspective: 🧘 Adult</div>
    <p class="insight-text">
      This verse reminds us that the core of our being is connected to a source that is naturally fearless...
    </p>
  </footer>
</article>
```

---

## 🎨 Visual Styles (The Pattern)

### 1. Base Container (`.shabad-card`)
- **Background**: `var(--surface-glass)` (0.03 opacity) with a strong `backdrop-filter: blur(20px)`.
- **Border**: `1px solid var(--border-gold)` with a subtle inner glow.
- **Shadow**: `var(--shadow-navy)` for depth.
- **Micro-interaction**: A soft fade-in and slide-up animation when it appears.

### 2. Typography Specs
| Element | Font | Color | Detail |
| :--- | :--- | :--- | :--- |
| **Gurmukhi** | `Raaj` / `GurbaniAkhar` | `var(--text-primary)` | Size: `2.5rem`, centered, high line-height |
| **Translit** | `Inter` | `var(--text-muted)` | Size: `0.9rem`, italic, uppercase tracking |
| **Translation** | `Outfit` | `var(--gold-light)` | Size: `1.25rem`, weight: 600, serif-style quotes |
| **AI Insight** | `Inter` | `var(--text-secondary)`| Border-top in `var(--border-glass)` |

---

## ✨ Persona-Specific Variations

The card should adapt its "tone" based on the selected persona:

### 👶 Child Persona
- **Corners**: `radius-2xl` (32px) for a softer look.
- **Icons**: Add a soft yellow "Protection" glow around the text.
- **Language**: Use simpler words and spacing between Gurbani lines.

### 🎒 Teen Persona
- **Style**: More "Digital/Tech" feel. Use sharper `var(--gold-gradient)` on borders.
- **Typography**: Slightly larger English headings for better scanning.

### 🧘 Adult Persona
- **Style**: Minimalist and Zen. Focus on the Gurmukhi, reducing the size of the transliteration.
- **Color**: Use more `var(--gold-muted)` instead of vibrant gold for a sophisticated feel.

---

## 🌊 Transitions & Motion

- **Entrance**: `opacity: 0` to `1` and `translateY(20px)` to `0`.
- **Timing**: `0.6s` with `cubic-bezier(0.16, 1, 0.3, 1)` (The "Ease-Out-Power" curve).
- **persona-change**: If the user toggles persona while a card is visible, the AI Insight section should "shimmer" and cross-fade to the new explanation.

---

## 🛠️ Implementation To-Do List (UX & Engineering)
- [ ] Install `GurbaniAkhar` webfont in `/public/fonts`.
- [ ] Create `ShabadCard.jsx` following this markup.
- [ ] Add the responsive class logic: `<article class={`shabad-card ${persona.toLowerCase()}`}>`.
- [ ] Wire up the API response to map to `gurmukhi_raw`, `english_translation`, and `ai_explanation`.
