# Google Cloud Platform (GCP) Scalability Plan (1000+ Users)

## 🎯 Objective
To build a data layer for SikhSituationBot on **Google Cloud Platform (GCP)** capable of handling 1,000+ concurrent requests with semantic search capabilities.

## 🏛️ GCP Architecture Recommendation

### 1. Primary Database: Cloud SQL for PostgreSQL
- **Concurrency**: Cloud SQL provides highly available, managed PostgreSQL instances. We will enable the **pgvector** extension.
- **Why?**: It handles thousands of concurrent connections and allows us to store and query embeddings (vectors) directly alongside our text data.
- **Scaling**: We can scale the instance size (CPU/RAM) vertically or use read replicas for massive read-scaling.

### 2. Backend Hosting: Google Cloud Run
- **Scaling**: This is a "Serverless" container platform. It will automatically scale from 0 to hundreds of instances based on incoming traffic.
- **Concurrency**: Each Cloud Run instance can handle up to 250 concurrent requests, making it perfect for your 1,000+ user requirement.

### 3. AI & Embeddings: Vertex AI
- **Text Embeddings**: We will use the `textembedding-gecko` model via Google Vertex AI to convert user queries and Shabads into vectors.
- **Vector Search**: While we'll start with `pgvector` in Cloud SQL, we can graduate to **Vertex AI Vector Search** if we reach millions of records.

### 4. Storage & Secret Management
- **Cloud Storage**: To store raw JSON data backups and logs.
- **Secret Manager**: To securely store API keys (Gemini, DB credentials).

## 🛠️ Data Pipeline (GCP Focused)
1. **Extraction**: Cleaned data via `scripts/clean_data.py`.
2. **Vectorization**: A Python script using `google-cloud-aiplatform` to generate embeddings.
3. **Seeding**: Push data to Cloud SQL.

## 📅 Roadmap Update
- [x] Select Google Cloud as the provider.
- [x] Create `scripts/vectorize_data.py`.
- [x] Define SQLAlchemy models for Cloud SQL (`server/models.py`).
- [x] Create database seeding script (`scripts/seed_cloud_db.py`).
