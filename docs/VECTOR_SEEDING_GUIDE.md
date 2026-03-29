# Vector Database Seeding Guide

**Last Updated**: March 23, 2026
**Purpose**: Step-by-step instructions for seeding the PostgreSQL database with Gurbani verses and their vector embeddings.

---

## 📋 Prerequisites

### 1. Database Setup
You must have a PostgreSQL database with pgvector extension enabled.

**Local Development Setup:**
```bash
# Install PostgreSQL and pgvector
# On macOS with Homebrew:
brew install postgresql
brew install pgvector

# Create database
createdb sikhsituationbot

# Enable pgvector extension
psql sikhsituationbot -c "CREATE EXTENSION vector;"
```

**Cloud Database (Railway/Supabase):**
- Provision PostgreSQL database
- Ensure pgvector extension is enabled
- Get the `DATABASE_URL` connection string

### 2. Environment Variables
Copy `.env.example` to `.env` and fill in the required values:

```bash
cp .env.example .env
```

Required variables:
- `DATABASE_URL`: PostgreSQL connection string
- `GEMINI_API_KEY`: Your Google Gemini API key

### 3. Python Dependencies
Install the required packages:

```bash
cd server
pip install -r requirements.txt
```

---

## 🚀 Seeding Process

### Step 1: Verify Data File
Ensure your Gurbani data is in the correct format:

```bash
# Check the data file exists and is valid JSON
python -c "import json; print('Data file valid:', bool(json.load(open('../data/shabads_cleaned.json'))))"
```

Expected output: `Data file valid: True`

### Step 2: Test Database Connection
Verify your database connection works:

```bash
cd server
python -c "from app import app, db; app.app_context().push(); print('DB connected:', db.engine.url.database)"
```

### Step 3: Run the Seeder
Execute the seeding script:

```bash
cd server
python seed_db.py
```

**Alternative: Use custom data file**
```bash
python seed_db.py ../data/your_custom_data.json
```

### Step 4: Monitor Progress
The seeder will output progress information:

```
[12:34:56] INFO - Found 3 shabads in data file. Beginning ingestion...
[12:34:56] INFO - Setting up pgvector extension and indexes...
[12:34:57] INFO - Generating embedding for shabad 1/3: unknown
[12:34:58] INFO - Generating embedding for shabad 2/3: unknown
[12:34:59] INFO - Committed batch of 2 shabads
[12:35:00] INFO - Generating embedding for shabad 3/3: unknown
[12:35:01] INFO - Committed final batch of 1 shabads
==================================================
DATABASE SEEDING COMPLETE
==================================================
Total processed: 3
Successfully embedded: 3
Failed embeddings: 0
Duplicates skipped: 0
Elapsed time: 5.23 seconds
Success rate: 100.0%
==================================================
```

---

## 🔍 Troubleshooting

### Common Issues

#### 1. Database Connection Failed
**Error**: `sqlalchemy.exc.OperationalError: (psycopg2.OperationalError) connection failed`

**Solutions**:
- Check `DATABASE_URL` format in `.env`
- Ensure PostgreSQL is running (local) or accessible (cloud)
- Verify username/password in connection string
- For cloud databases, check firewall rules and SSL requirements

#### 2. pgvector Extension Not Available
**Error**: `sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedFunction) function vector_cosine_distance(vector, vector) does not exist`

**Solutions**:
- Install pgvector extension: `CREATE EXTENSION vector;`
- For cloud providers, ensure pgvector is supported/enabled
- Check PostgreSQL version compatibility (pgvector requires PostgreSQL 11+)

#### 3. Gemini API Key Issues
**Error**: `google.api_core.exceptions.Unauthenticated: Request had invalid authentication credentials`

**Solutions**:
- Verify `GEMINI_API_KEY` in `.env` is correct
- Check API key has proper permissions
- Ensure billing is enabled on Google Cloud project
- Check API quota/limits

#### 4. Embedding Generation Failed
**Error**: `Failed to generate embedding for shabad: shabad-1`

**Solutions**:
- Check internet connection for Gemini API
- Verify API key is valid and has quota
- The script will automatically fall back to local sentence-transformers model
- Check logs for specific error details

#### 5. Duplicate Shabads
**Info**: `Duplicates skipped: 2`

**Solutions**:
- This is normal behavior - the script prevents duplicate entries
- If you want to re-seed, you can drop and recreate the table
- Or modify the script to allow updates instead of skipping

---

## 📊 Expected Results

### Success Metrics
After successful seeding, you should see:
- **Total processed**: Number of shabads in your JSON file
- **Successfully embedded**: Should match total processed (or close with fallbacks)
- **Failed embeddings**: 0 (or minimal)
- **Success rate**: > 95%

### Database Verification
Check your database contains the data:

```sql
-- Count total shabads
SELECT COUNT(*) FROM shabads;

-- Check embedding vectors exist
SELECT shabad_id, LENGTH(embedding) as vector_length
FROM shabads
LIMIT 5;

-- Test similarity search
SELECT shabad_id, english_translation,
       embedding <=> '[0.1, 0.2, ...]' as similarity_score
FROM shabads
ORDER BY embedding <=> '[0.1, 0.2, ...]'
LIMIT 3;
```

---

## ⚙️ Configuration Options

### Batch Size
Control memory usage and commit frequency:

```python
# In seed_db.py, modify the call:
stats = seed_database(data_path, batch_size=5)  # Smaller batches for testing
stats = seed_database(data_path, batch_size=50)  # Larger batches for production
```

### Duplicate Handling
Control whether to skip or update existing records:

```python
# Skip duplicates (default)
stats = seed_database(data_path, skip_duplicates=True)

# Allow updates (slower, more complex)
stats = seed_database(data_path, skip_duplicates=False)
```

---

## 🔄 Re-seeding the Database

If you need to re-seed with updated data:

```bash
# Option 1: Clear and re-seed (development only)
cd server
python -c "from app import app, db; app.app_context().push(); db.drop_all(); db.create_all()"

# Option 2: Manual cleanup
# Connect to your database and run:
# DELETE FROM shabads;
# Or drop and recreate the table

# Then re-run the seeder
python seed_db.py
```

---

## 📈 Performance Notes

### Expected Timing
- **3 test shabads**: ~5-10 seconds
- **50 shabads**: ~2-3 minutes
- **500 shabads**: ~20-30 minutes

### Optimization Tips
- Use larger batch sizes for better performance
- Gemini API has rate limits - the script includes automatic retries
- Local embeddings are faster but less accurate than Gemini
- Consider using a GPU for local embeddings with larger datasets

---

## 🧪 Testing the Seeded Data

After seeding, test the retrieval system:

```bash
cd server
python test_query.py  # If you have a test script
```

Or manually test via the API:

```bash
curl -X POST http://localhost:5000/ask \
  -H "Content-Type: application/json" \
  -d '{"query": "feeling anxious", "persona": "adult"}'
```

---

## 📞 Support

If you encounter issues:
1. Check the logs for detailed error messages
2. Verify all prerequisites are met
3. Test database connection independently
4. Ensure API keys are valid and have proper permissions

For team-specific issues, contact the AI/Data team lead (@sbindra-ai).