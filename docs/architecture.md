# Architecture & Data Flow

## 🏛️ System Overview
The SikhSituationBot uses a **RAG (Retrieval-Augmented Generation)** architecture to ensure that the AI's responses are grounded in actual scripture rather than hallucinated text.

### Tech Stack Choice: Python/Flask + PostgreSQL + pgvector
We have selected **Python/Flask** for the backend because Python is the native language of AI and LLM development. It provides the best libraries for semantic search and prompt orchestration. The system uses **PostgreSQL with pgvector extension** for efficient vector similarity search and **Google Gemini API** for intelligent response synthesis.

## 🔄 Core Data Flow

### Complete RAG Pipeline

1. **User Request**: User selects a persona (Child/Teen/Adult) and types: "I'm feeling afraid of the dark."

2. **Query Processing**: The Flask backend receives the query and validates input parameters.

3. **Embedding Generation**: Query is converted into a 768-dimensional vector using:
   - **Primary**: Google Gemini `text-embedding-004` model (cloud-based, high quality)
   - **Fallback**: Local `sentence-transformers` `all-MiniLM-L6-v2` model (offline, fast)

4. **Vector Similarity Search**: System searches PostgreSQL database with pgvector for verses semantically closest to the query vector using cosine similarity:
   ```sql
   SELECT * FROM shabads
   ORDER BY embedding <=> query_embedding
   LIMIT 3;
   ```

5. **Persona-Aware Retrieval**: Results are filtered/refined based on persona compatibility and relevance scoring.

6. **Prompt Engineering**: Backend constructs a sophisticated prompt combining:
   - User's emotional query
   - Retrieved Gurbani verses with full context
   - Persona-specific guidance tones (Child: simple/metaphors, Teen: relatable/modern, Adult: philosophical/spiritual)
   - Sikh wisdom framework and response guidelines

7. **AI Synthesis**: Google Gemini 1.5 Flash generates a compassionate, personalized response that:
   - Acknowledges the user's feelings
   - Connects their situation to Gurbani wisdom
   - Provides practical spiritual guidance
   - Maintains appropriate tone for selected persona

8. **Response Delivery**: Frontend displays:
   - AI-generated guidance (persona-tailored)
   - Most relevant Shabad with Gurmukhi, Romanization, and English translation
   - Related Shabads (if available)
   - Error handling with graceful fallbacks

## 🗄️ Database Architecture

### PostgreSQL with pgvector
- **Engine**: PostgreSQL 11+ with pgvector extension
- **Vector Dimensions**: 768 (matching Gemini embedding model)
- **Index**: IVFFlat with cosine distance for fast similarity search
- **Schema**: Structured Shabad model with metadata

### Data Model
```sql
CREATE TABLE shabads (
    id SERIAL PRIMARY KEY,
    shabad_id VARCHAR(50) UNIQUE NOT NULL,
    gurmukhi TEXT NOT NULL,
    romanization TEXT,
    english_translation TEXT NOT NULL,
    source VARCHAR(100),
    recommended_persona VARCHAR(20) DEFAULT 'any',
    context_tags TEXT[], -- Array of emotional/context tags
    embedding vector(768), -- pgvector embedding column
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance index for similarity search
CREATE INDEX shabads_embedding_idx
ON shabads USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

## 🧠 AI/ML Components

### Embedding Strategy
- **Dual Model Approach**: Cloud (Gemini) + Local (sentence-transformers) for reliability
- **Retry Logic**: Exponential backoff for API rate limits
- **Fallback Chain**: Gemini → Local model → Error handling
- **Caching**: Local model instances cached for performance

### Prompt Engineering
- **Persona-Specific**: Different tones for Child/Teen/Adult
- **Context-Rich**: Full Shabad details + emotional context
- **Instruction-Guided**: Clear guidelines for compassionate, scripture-based responses
- **Safety-Aligned**: Respectful of Sikh teachings and cultural sensitivity

### Response Synthesis
- **Model**: Google Gemini 1.5 Flash
- **Parameters**: temperature=0.7, max_tokens=500, top_p=0.8
- **Safety**: Configured for helpful, harmless content
- **Fallbacks**: Graceful degradation when API unavailable

## 🏗️ Component Breakdown

### Frontend (Next.js React)
- **State Management**: Persona selection, loading states, error handling
- **UI Components**: Chat input, perspectives selector, Shabad display
- **API Integration**: RESTful calls to `/ask` endpoint
- **Typography**: High-quality Gurmukhi rendering with proper spacing

### Backend (Flask Python)
- **API Layer**: REST endpoints with CORS support
- **Embedding Service**: Dual-model embedding generation with retry logic
- **Vector Search**: pgvector-based similarity queries
- **AI Orchestration**: Gemini API integration with prompt engineering
- **Data Pipeline**: Robust seeding with batch processing and error handling

### Data Layer (PostgreSQL + pgvector)
- **Storage**: Structured Gurbani verses with vector embeddings
- **Search**: Fast semantic similarity using cosine distance
- **Indexing**: Optimized for vector operations
- **Migration**: Support for data updates and re-embedding

### External Services
- **Google Gemini API**: Embedding generation and response synthesis
- **PostgreSQL Cloud**: Railway/Supabase for production database
- **Local Fallbacks**: sentence-transformers for offline operation

## 🔒 Security & Reliability

### API Security
- **Key Management**: Environment variables for API keys
- **Rate Limiting**: Built-in retry logic with exponential backoff
- **Error Handling**: Graceful degradation and user-friendly messages

### Data Integrity
- **Validation**: Input sanitization and schema validation
- **Atomic Operations**: Database transactions for data consistency
- **Backup Strategy**: JSON exports for data recovery

### Performance Optimization
- **Batch Processing**: Efficient data seeding with configurable batch sizes
- **Connection Pooling**: Database connection management
- **Caching**: Model instances and frequent queries
- **Async Processing**: Non-blocking API calls where possible

## 📊 Monitoring & Observability

### Logging
- **Structured Logs**: Request/response tracking with timestamps
- **Error Tracking**: Detailed error messages with context
- **Performance Metrics**: Embedding generation times, API response times

### Health Checks
- **Database Connectivity**: Connection validation
- **API Availability**: Gemini service health checks
- **Data Integrity**: Shabad count and embedding validation

## 🚀 Deployment Architecture

### Development
- **Local PostgreSQL**: pgvector-enabled database
- **Environment Variables**: Local .env configuration
- **Hot Reload**: Flask development server with auto-restart

### Production
- **Cloud Database**: Railway PostgreSQL with pgvector
- **Environment Secrets**: Secure API key management
- **Container Ready**: Docker support for consistent deployment
- **Health Monitoring**: Application performance tracking
