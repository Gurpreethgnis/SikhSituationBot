# 🧪 SikhSituationBot - MVP Testing Guide

Welcome to the **Stage 2 (MVP)** testing phase! This guide covers the context-aware features, semantic search, and the new mobile experience.

## ⚙️ Core Features to Test

### 1. Semantic Situational Search (RAG)
Unlike the PoC which used hardcoded keywords, the MVP understands *intent*.
- **Task:** Ask Giani Ji about complex emotions without using keywords like "peace" or "stress".
  - *Example:* "I'm feeling like everyone is moving faster than me and I'm left behind."
  - *Example:* "How do I deal with a friend who betrayed my trust?"
- **Verify:**
  - Does the bot retrieve a relevant Shabad?
  - Does the **AI Insight** section explain the Shabad in the context of your specific situation?
  - Change your **Persona** (Child/Teen/Adult) and ask the same thing. Verify the tone and vocabulary adjust.

### 2. Realtime Voice Interaction (Web & Mobile)
Experience hands-free conversation with Giani Ji.
- **Action:** Click the Microphone icon in the chat bar.
- **Verify:**
  - **Immersive Mode:** Does the screen transform into the immersive voice UI?
  - **Status:** Does it show "Listening...", "Thinking...", and "Speaking..."?
  - **Audio:** Does Giani Ji speak back to you with a natural voice?
  - **Transcript:** Is your speech transcribed accurately on screen?

### 3. Personalization & Memory
The bot remembers who you are and what you've discussed.
- **Task:** If you haven't yet, set your **Birth Year** in Onboarding/Settings.
- **Action:** Start a conversation, then ask "Based on what I just told you, what should I do?"
- **Verify:**
  - Does the bot remember your previous message?
  - Does the guidance feel appropriate for your age group?

### 4. Push Notifications (Mobile Only)
Stay connected with daily Gurbani reflections.
- **Verify:**
  - Run the admin test: Go to the **Admin Panel** on mobile and click **"Send Test Push"**.
  - Does your device receive a notification even when the app is closed?
  - Does tapping the notification open the app?

### 5. Gurbani Discovery (Parmaan Mode)
Advanced tools for deep Gurbani study.
- **Action:** Switch to **🔍 Parmaan** mode using the menu.
- **Search Types:**
  - **Ask:** Just talk normally; it will find 5 relevant shabads.
  - **Find Line:** Type a phrase to find specific verses from the corpus.
  - **By Theme:** Search by broad concepts (e.g. "Humility", "Grit").
- **Discovery Chips:** Try "Similar", "Topic", and "Contrasts" to see how the retrieval logic changes.

---

## 🐞 Reporting Issues
If you encounter a bug or the AI gives an irrelevant response:
1. Click the **Feedback (🚩)** button on the specific message.
2. Describe what was wrong.
3. Your feedback (including the shabad context) is sent directly to the Admin Panel for us to review.

## 🚀 Deployment Status
- **Web:** `https://sikhsituationbot.sage-school.com`
- **Mobile:** Open via Expo Go or the provided build link.
