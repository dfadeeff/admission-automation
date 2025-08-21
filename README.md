# IU Admissions RAG System

A minimal RAG (Retrieval-Augmented Generation) system that queries the 245-page IU admission handbook to automate admission decisions.

## Structure

```
├── backend/
│   ├── main.py              # FastAPI application
│   ├── rag/                 # RAG system components
│   │   ├── handbook_loader.py    # PDF processing
│   │   ├── vector_store.py       # ChromaDB integration
│   │   └── retriever.py          # Query engine
│   └── config/              # Configuration
├── data/
│   └── Leitfaden.pdf        # 245-page admission handbook
├── requirements.txt
└── .env.example
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure OpenAI API:
```bash
cp .env.example .env
# Add your OPENAI_API_KEY to .env
```

3. Start the server:
```bash
cd backend
python main.py
```

## Usage

### 1. Initialize RAG System
```bash
curl -X POST http://localhost:8000/initialize \
  -H "Content-Type: application/json" \
  -d '{"force_reload": true}'
```

### 2. Query Admission Rules
```bash
curl -X POST http://localhost:8000/query-rules \
  -H "Content-Type: application/json" \
  -d '{"question": "What are the requirements for Finanzmanagement program?"}'
```

### 3. Check Applicant Admission
```bash
curl -X POST http://localhost:8000/check-admission \
  -H "Content-Type: application/json" \
  -d '{
    "target_program": "Finanzmanagement",
    "previous_qualification": "Abitur",
    "has_exmatrikulation": false,
    "work_experience_years": 2
  }'
```

## How It Works

1. **PDF Processing**: Loads the 245-page handbook and chunks it into processable segments
2. **Embedding**: Creates vector embeddings of chunks using OpenAI embeddings
3. **Storage**: Stores embeddings in ChromaDB for fast retrieval
4. **Query**: When queried, retrieves relevant chunks and uses GPT-4 to answer based on the handbook content
5. **Citations**: Returns answers with page references for transparency

## API Endpoints

- `POST /initialize` - Initialize or reload the RAG system
- `POST /query-rules` - Query specific admission rules
- `POST /check-admission` - Check if an applicant meets criteria
- `GET /health` - Health check

## Key Features

- ✅ Processes 245-page German admission handbook
- ✅ RAG-based accurate rule retrieval
- ✅ Page-level citations for transparency
- ✅ Simple REST API
- ✅ Minimal dependencies