# System Architecture - SikhSituationBot

This document outlines the technical components and data flow for the SikhSituationBot PoC.

## 🧱 Component Breakdown

### 1. User Interface (Frontend)
- **Tech Stack**: Next.js (React) + Vanilla CSS.
- **Responsibilities**: 
    - Handle user input and demographic selection.
    - Display Gurbani verses in Gurmukhi, Romanization, and English.
    - Responsive mobile-first design for "on-the-go" spiritual help.

### 2. Backend Logic (API)
- **Tech Stack**: Next.js API Routes (Node.js).
- **Responsibilities**:
    - Orchestrating the flow between the UI and the AI services.
    - Managing prompt templates for different age groups.

### 3. Retrieval Engine (RAG)
- **Tech Stack**: Supabase Vector or Pinecone.
- **Responsibilities**:
    - **Vector Store**: Storage of Gurmukhi verses and their English embeddings.
    - **Semantic Search**: Mapping user queries (e.g., "fear") to relevant verses (e.g., "Nirbhau").

### 4. Data Layer
- **Source**: JSON/CSV exports from BaniDB or Shabad OS.
- **Processing**: A Python or Node script to chunk and embed the data into the Vector Store.

### 5. AI Reasoning (LLM)
- **Model**: Gemini 1.5 Flash (via Google AI Studio).
- **Responsibilities**:
    - Synthesizing retrieved context into a coherent explanation.
    - Enforcing "Safety Rails" to ensure the AI doesn't give medical or legal advice.

## 🔄 Core Workflow (The "Loop")

1. **Query**: "I'm scared of failing my exam."
2. **Embedding**: Convert query to a numerical vector using an embedding model ($e.g., text-embedding-004$).
3. **Search**: Find the top 3 most relevant Shabads in the Vector DB based on cosine similarity.
4. **Augment**: Create a prompt: 
   > "Using these Shabads: [Verse 1, Verse 2], explain to a [Teenager] how to handle the fear of failure."
5. **Generate**: LLM returns the final response.
6. **Render**: UI displays the Shabad + The "Situation Guide".

## 🛠️ Dev Tools for Students
- **Cursor/Antigravity**: Used for rapid scaffolding and fixing RAG logic.
- **Vercel**: For instant deployment and sharing the PoC link.
- **Postman**: For testing API routes.
