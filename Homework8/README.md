# Pinecone + Airflow: Medium Article Semantic Search Engine

## 📋 Overview

This project implements a semantic search engine for Medium articles using Apache Airflow for orchestration, Pinecone for vector storage, and Sentence Transformers for embeddings. The system downloads articles, generates embeddings, stores them in Pinecone, and enables similarity-based search.

---

## 🛠️ Tech Stack

- **Orchestration**: Apache Airflow 2.x
- **Vector Database**: Pinecone Serverless (AWS us-east-1)
- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Data Processing**: Pandas
- **Containerization**: Docker & Docker Compose


### Setup

**Configure Pinecone API Key**
   - Get API key from [pinecone.io](https://www.pinecone.io/)
   - In Airflow UI (http://localhost:8080): Admin → Variables
   - Add: `pinecone_api_key` = your-api-key

**Run the DAG**
   - Enable `Medium_to_Pinecone` DAG
   - Click trigger button

---

## 📊 Pipeline Overview

The DAG consists of 5 sequential tasks:

### 1️⃣ download_data
Downloads Medium articles dataset from S3
- **Source**: https://s3-geospatial.s3.us-west-2.amazonaws.com/medium_data.csv
- **Output**: `/tmp/medium_data/medium_data.csv`

### 2️⃣ preprocess_data
Cleans and prepares data
- Combines title + subtitle into metadata field
- Adds unique IDs
- **Output**: `/tmp/medium_data/medium_preprocessed.csv`

### 3️⃣ create_pinecone_index
Creates Pinecone index
- **Name**: semantic-search-fast
- **Dimension**: 384
- **Metric**: dotproduct
- **Type**: Serverless (AWS us-east-1)

### 4️⃣ generate_embeddings_and_upsert
Generates embeddings and uploads to Pinecone
- Uses all-MiniLM-L6-v2 model
- Processes in batches of 100
- Converts article titles to 384-dimensional vectors

### 5️⃣ test_search_query
Tests search with query: "what is ethics in AI"
- Returns top 5 similar articles
- Includes similarity scores and metadata

---

## 🔍 How It Works
```
Medium Articles → Download → Preprocess → Create Index
                                             ↓
                      Search ← Upsert ← Generate Embeddings
```

**Semantic Search Process:**
1. Convert search query to embedding vector
2. Find similar vectors in Pinecone (cosine similarity)
3. Return top-k most similar articles with metadata

---


## ⚙️ Configuration

### docker-compose.yaml
Includes required packages:
```yaml
_PIP_ADDITIONAL_REQUIREMENTS: sentence-transformers pinecone
```

### Airflow Variables
- `pinecone_api_key`: Your Pinecone API key

### DAG Configuration
- Schedule: Weekly (`timedelta(days=7)`)
- Start Date: April 1, 2025
- Catchup: False

