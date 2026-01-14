# 🗓️ 4-Week PoC Weekly Plan

This plan outlines the focus for a student team to reach a demo-ready product in 4 weeks.

## Week 1: Foundation & Scaffold
- **Tech Setup**: Initialize React (Vite) and Flask projects.
- **UI Design**: Create a basic chat layout with a "Persona Toggle" (Child/Teen/Adult).
- **Hello AI**: Connect a simple backend route to the LLM API to confirm connectivity.

## Week 2: Data & Search
- **Curated Dataset**: Create the `data/shabads.json` file with 50 common situational Shabads.
- **Search Logic**: Implement basic keyword search and simple semantic retrieval in the backend.
- **Display**: Ensure the frontend can render Gurmukhi fonts beautifully.

## Week 3: The AI Voice (RAG)
- **Prompt Engineering**: Develop specific system prompts for the Child, Teen, and Adult personas.
- **Integration**: Connect the Retrieval logic to the LLM so the bot uses real verses to answer questions.
- **Safety**: Implement basic filters to ensure the bot doesn't provide medical or legal advice.

## Week 4: Polish & Demo
- **UI/UX**: Add loading animations (sparkles/shimmer) and smooth transitions.
- **Testing**: Run internal "demo trials" with common user queries (Anxiety, Bravery, Grief).
- **Deployment**: Deploy the frontend to Vercel and the backend to a platform like Render/Railway.

---
*Success Metric: A user can get a relevant Shabad and a customized explanation in under 5 seconds.*
