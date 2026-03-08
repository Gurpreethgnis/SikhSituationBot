# 🧪 SikhSituationBot - PoC Testing Guide

Welcome to the SikhSituationBot Proof of Concept (PoC) testing phase! This document outlines the features currently active in our `main` branch deployed to production. 

Use this guide during class to test the UI/UX and understand the baseline functionality before we embark on the MVP (Stage 2) database and AI integration.

## 🎯 Test Objective
Familiarize yourself with the frontend interaction patterns, the premium UI, and how the frontend communicates with the backend's current "mock" endpoint.

## ⚙️ Features to Test

### 1. Premium UI & Responsive Design
- **Action:** Open the deployed app on both a desktop browser and a mobile device (`https://sikhsituationbot.sage-school.com`).
- **Verify:**
  - The Deep Blue & Gold color palette and glassmorphism (frosted glass) effects render correctly.
  - The new official Wikipedia Khanda SVG logo displays clearly with a glowing chat-bubble effect.
  - The layout adjusts gracefully to smaller screens without breaking.

### 2. Persona Toggles
- **Action:** Click through the **Child (👳🏽)**, **Teen (👳🏽)**, and **Adult (👳🏽‍♂️)** perspective pills.
- **Verify:**
  - The active pill highlights with a golden gradient.
  - The placeholder text in the chat input smoothly changes to reflect the selected persona (e.g., "Share how you're feeling as a child...").

### 3. Keyword Triggers (Mock Backend)
The current backend (`server/app.py`) uses a mock hardcoded endpoint to demonstrate the planned UX. It is **not** querying the full SGGS database yet.
- **Action:** Type messages containing specific keywords and press Enter or the send icon.
- **Test Cases:**
  - Type a sentence containing **"peace"** (e.g., "I want to find peace"). 
    - *Expected:* A Shabad about coolness/peace (e.g., "Tati Vao Na Lagai").
  - Type a sentence containing stress words: **"stress"**, **"overwhelmed"**, **"anxious"**, or **"scared"**.
    - *Expected:* A Shabad about finding sanctuary and Waheguru's protection.
- **Verify Persona Logic:** Send the same keyword (e.g., "peace") but change the Persona before sending. Verify that the "AI insight" paragraph changes its tone depending on whether Child, Teen, or Adult was selected.

### 4. Shabad Response Structure
- **Action:** Trigger a successful keyword match.
- **Verify:** The response card cleanly formats the following elements:
  - **Gurmukhi:** Proper font rendering for the original text.
  - **Transliteration:** Clean, uppercase spacing for pronunciation.
  - **Translation:** The English meaning presented in an elegant, italicized typography.
  - **AI Insight:** Contextual guidance placed at the bottom with a proper divider.

### 5. Fallback Responses
- **Action:** Type a query that does *not* contain the keywords mentioned above (e.g., "What is the weather?" or "Hello").
- **Verify:** The bot should return a graceful default response, explaining that it is doing its best as a PoC and offering a universal Gurbani verse.

---
**💡 Takeaway:** By understanding how the current frontend components operate with mock data, you will be fully prepared to connect them to the real PostgreSQL vector database and Gemini API in your assigned MVP branches.
