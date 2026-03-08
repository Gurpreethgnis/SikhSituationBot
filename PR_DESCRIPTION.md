# feat(ux): Add premium chat input / search bar component

## Summary
Implements **Task 1** from TASK_ASSIGNMENTS.md for @siddharthchopra (UX): *Build chat input / search bar component* with a premium feel.

## Changes
- **Client scaffold**: Vite + React app in `/client` (port 5173)
- **ChatInput component** (`client/src/components/ChatInput.jsx`):
  - Text input with placeholder: "Share how you're feeling or ask for guidance..."
  - Submit on **Enter** or via **Send** button (gold accent)
  - Loading state (spinner), disabled state
  - Props: `onSend`, `placeholder`, `disabled`, `loading`
- **Theme**: Deep blue & gold (Sikh-inspired) CSS variables in `index.css`
- **App**: Renders ChatInput; `onSend` logs query to console (ready to wire to backend in Task 3)

## How to test
```bash
cd client
npm install
npm run dev
```
Open http://localhost:5173, type a message, press Enter or click Send — query appears in browser console.

## Checklist
- [x] Chat input / search bar with premium feel
- [x] Themed (deep blue, gold) per project design direction
- [x] No linter errors

## Related
- TASK_ASSIGNMENTS.md — Assigned to @siddharthchopra (UX)
- Next: Task 2 — Implement persona toggle (Child/Teen/Adult) UI
