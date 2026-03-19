# GRC-LLM: RAG-Grounded Compliance Assessment Tool

A multi-framework security maturity assessment tool that ingests organizational policy documents (PDF), uses Retrieval-Augmented Generation to ground LLM responses in actual policy text, and evaluates compliance against 9 security frameworks — producing weighted maturity scores (0–5) with structured, auditable outputs.

Built to address three gaps identified in the literature:
1. No unified multi-framework assessment tool exists
2. Existing tools rely on keyword matching, not semantic understanding
3. No open-source RAG-grounded maturity scorer produces auditable outputs

## Features

- **PDF Ingestion** — Upload policy documents; text is extracted, chunked, embedded, and indexed in a local vector store
- **9 Security Frameworks** — Assess against NIST CSF, NIST 800-53, ISO 27001, CIS CSC, CMMC, HIPAA, PCI-DSS, CSA CCM, and FTC Safeguards Rule
- **RAG-Grounded Assessment** — Each control is evaluated by retrieving the most relevant policy excerpts and prompting Claude for a structured assessment
- **Weighted Maturity Scoring** — Control-level scores (0–5) aggregate into family and framework scores using configurable weights
- **Auditable JSON Output** — Every score includes evidence quotes, gap analysis, and recommendations
- **Single-Page Frontend** — Upload, assess, and explore results with an interactive dashboard

## Architecture

```
PDF Upload → PyMuPDF text extraction → 400-token chunks with 50-token overlap
           → sentence-transformers (all-mpnet-base-v2) embedding
           → ChromaDB vector store (one collection per document)

Assessment → For each control in selected framework(s):
               1. Embed control description → query ChromaDB → top-5 chunks
               2. Build prompt with control requirement + retrieved excerpts
               3. Claude (claude-opus-4-6) returns structured JSON assessment
               4. Parse → ControlAssessmentResult {score, evidence, gaps, recommendations}
           → Weighted aggregation → family scores → framework score → overall posture
           → Save to JSON store
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.11+, FastAPI |
| LLM | Anthropic Claude (claude-opus-4-6) |
| Vector Store | ChromaDB (local, persistent) |
| Embeddings | sentence-transformers (all-mpnet-base-v2) |
| PDF Parsing | PyMuPDF (fitz) |
| Validation | Pydantic v2 |
| Frontend | Plain HTML / CSS / JS |

## Quick Start

```bash
# Clone
git clone https://github.com/revo23/GRC-LLM.git
cd GRC-LLM

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# Run
uvicorn app.main:app --reload

# Open http://localhost:8000
```

## Usage

1. **Upload** — Drag and drop a PDF policy document. The tool extracts text, chunks it, and indexes embeddings in ChromaDB.
2. **Assess** — Select the uploaded document and one or more frameworks. Click "Run Assessment" — the tool evaluates each control asynchronously.
3. **Results** — View the overall posture score (0–5 gauge), per-framework score cards, control family heatmap, and an expandable gap table with evidence, gaps, and recommendations per control.
4. **Download** — Export the full assessment as a structured JSON report.

## Frameworks

| Framework | Controls | Description |
|-----------|----------|-------------|
| NIST CSF | 26 | Cybersecurity Framework v1.1 — Identify, Protect, Detect, Respond, Recover |
| NIST 800-53 | 26 | Security and Privacy Controls Rev 5 — AC, AT, AU, CA, CM, IA, IR, RA, SC, SI |
| ISO 27001 | 22 | Information Security Management 2022 — Annex A controls |
| CIS CSC | 18 | Critical Security Controls v8 — Basic, Foundational, Organizational |
| CMMC | 20 | Cybersecurity Maturity Model Certification 2.0 — Level 1–3 practices |
| HIPAA | 19 | Security Rule — Administrative, Physical, Technical safeguards |
| PCI-DSS | 22 | Payment Card Industry Data Security Standard 4.0 — Requirements 1–12 |
| CSA CCM | 23 | Cloud Controls Matrix 4.0 — AIS, BCR, CCC, CEK, GRC, IAM, LOG, SEF, TVM |
| FTC Safeguards | 15 | FTC Safeguards Rule 2023 — 9 required elements |

## Maturity Scale

| Score | Level | Description |
|-------|-------|-------------|
| 0 | Not Implemented | No evidence of the control in the policy |
| 1 | Initial | Ad hoc mention, no formal process defined |
| 2 | Developing | Some elements present but incomplete or inconsistent |
| 3 | Defined | Formal, documented process covering most requirements |
| 4 | Managed | Measured, monitored with defined metrics and accountability |
| 5 | Optimized | Continuously improved, integrated with risk management |

## Project Structure

```
├── app/
│   ├── main.py               # FastAPI app, CORS, static files
│   ├── config.py             # Pydantic settings (.env)
│   ├── api/                  # Route handlers
│   │   ├── documents.py      # Upload, list, delete documents
│   │   ├── assessments.py    # Run and retrieve assessments
│   │   ├── frameworks.py     # List frameworks and controls
│   │   └── reports.py        # Download JSON reports
│   ├── frameworks/           # 9 framework definitions
│   ├── models/               # Domain dataclasses
│   ├── schemas/              # Pydantic API contracts
│   ├── services/             # Core logic
│   │   ├── ingestion.py      # PDF → chunks → embeddings → ChromaDB
│   │   ├── retrieval.py      # Semantic search over document chunks
│   │   ├── assessor.py       # Claude-powered control assessment
│   │   ├── scorer.py         # Weighted score aggregation
│   │   └── report_builder.py # Assessment orchestration
│   └── storage/              # JSON file-based persistence
├── frontend/                 # Single-page app (HTML/CSS/JS)
├── requirements.txt
└── .env.example
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/documents/upload` | Upload PDF, trigger ingestion |
| `GET` | `/api/documents` | List uploaded documents |
| `DELETE` | `/api/documents/{id}` | Delete document and index |
| `GET` | `/api/frameworks` | List all frameworks |
| `GET` | `/api/frameworks/{id}/controls` | List controls for a framework |
| `POST` | `/api/assessments/run` | Start async assessment |
| `GET` | `/api/assessments/{id}` | Get assessment result |
| `GET` | `/api/assessments` | List all assessments |
| `GET` | `/api/reports/{id}/download` | Download JSON report |

## License

MIT
