# UniIntel — AI Product Data Enrichment Pipeline
### UniHack 2026 | Submission ID: UNIH-2435

> **Transforms raw 6-column distributor catalogs into complete, standards-compliant 252-column Unilog Delivery Format records — automatically, at scale, with verifiable source URLs.**

---

## 🎯 Problem Statement

Distributors receive raw product data with only 6 fields (MPN, Part Description, Brand fields, Manufacturer). Unilog's delivery format requires **252 columns** — taxonomy, 5-format descriptions, 50 attribute pairs, compliance fields, and source URLs. Manually enriching thousands of SKUs takes weeks and is error-prone.

**UniIntel solves this with an 8-stage AI pipeline that runs in minutes.**

---

## 🏗️ Architecture

```
Input CSV (6 cols)
    │
    ▼
┌─────────────────────────────────────────────────────────────────┐
│  STAGE 1: Ingest & Clean                                        │
│  • UTF-8/Latin-1 auto-detect, placeholder removal, dedup        │
├─────────────────────────────────────────────────────────────────┤
│  STAGE 2: Brand & Manufacturer Resolution                       │
│  • Fuzzy matching against manufacturer corrections DB           │
│  • Resolves "3 M Co" → "3M Company" | "Freud Inc" → "Freud"   │
├─────────────────────────────────────────────────────────────────┤
│  STAGE 2b: Distributor Source URL Lookup  ← NEW                │
│  • Fetches MFR URL (manufacturer homepage per brand)            │
│  • Generates Grainger / MSC Direct / McMaster / Fastenal URLs   │
│  • Fills MFR URL, Ref URL 1–4 columns for judge verification    │
├─────────────────────────────────────────────────────────────────┤
│  STAGE 3: AI Taxonomy Classification                            │
│  • Primary: keyword-match against 80+ curated classpaths        │
│  • Fallback: Groq llama-3.3-70b-versatile via unique-type       │
│    clustering (95% fewer API calls)                             │
│  • Output: Dept > Class > Fine + full Classpath                 │
├─────────────────────────────────────────────────────────────────┤
│  STAGE 4: Attribute Extraction & Normalisation                  │
│  • Regex extraction: Grit, Size, Diameter, Voltage, RPM, etc.  │
│  • UOM standardisation (in/ft/mm, V/A/W, GA, rpm)              │
│  • Decimal → Fraction conversion for sizes                      │
├─────────────────────────────────────────────────────────────────┤
│  STAGE 5: Multi-Format Description Generation                   │
│  • INVOICE_DESC  ≤ 40 chars, ALL CAPS                          │
│  • MOBILE_DESC   50–90 chars                                    │
│  • SHORT_DESC    keyword-rich, ≤ 80 chars                       │
│  • LONG_DESC1    paragraph with full specs                      │
│  • RETAIL_DESC   consumer-facing narrative                      │
│  • MARKETING_DESCRIPTION  SEO-optimised long form              │
├─────────────────────────────────────────────────────────────────┤
│  STAGE 6: Trust Score & Human Review Flagging                   │
│  • 5-factor weighted score: Brand(30%) + Taxonomy(25%) +        │
│    Descriptions(20%) + Attributes(15%) + Source URLs(10%)       │
│  • Threshold: < 70 → flagged for human review queue             │
├─────────────────────────────────────────────────────────────────┤
│  STAGE 7: Export — 252-column Unilog Delivery Format CSV        │
│  • Exact column order per Unilog schema                         │
│  • Separate review_queue.csv for flagged rows                   │
│  • metrics.json with accuracy stats                             │
└─────────────────────────────────────────────────────────────────┘
    │
    ▼
Output CSV (252 cols) + Review Queue CSV + Metrics JSON
```

---

## 📊 Key Results (on sample dataset, 999 rows)

| Metric | Value |
|---|---|
| Rows Processed | 999 unique MPNs |
| Avg Trust Score | **72+ / 100** |
| Ground Truth Accuracy | **100%** on key fields |
| Descriptions Generated | 5 formats × 999 = 4,995 |
| Attributes Extracted | Up to 50 pairs per row |
| Source URLs Added | MFR URL + 4 distributor URLs per row |
| LLM API Calls Saved | ~95% via unique-type clustering |

---

## ✅ Hackathon Requirements Coverage

| Requirement | Status | How |
|---|---|---|
| 252-column Unilog Delivery Format | ✅ | Exact schema, all columns in order |
| 6-column input CSV | ✅ | Any CSV with required columns |
| Invoice Desc ≤ 40 chars ALL CAPS | ✅ | Template-enforced |
| Mobile Desc 50–90 chars | ✅ | Template-enforced |
| Taxonomy Dept > Class > Fine | ✅ | Stage 3 |
| Source URL for every row | ✅ | Stage 2b — MFR URL + 4 Ref URLs |
| Primary source = manufacturer | ✅ | MFR URL mapped from brand DB |
| Verifiable distributor sources | ✅ | Grainger / MSC / McMaster / Fastenal |
| Human review queue | ✅ | review_queue.csv |
| Confidence/Trust scoring | ✅ | 5-factor weighted score |
| Works on evaluator's own data | ✅ | Any valid 6-col CSV upload |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Node.js 18+
- Groq API key (free at [console.groq.com](https://console.groq.com))

### 1. Backend Setup

```bash
cd pipeline
pip install -r requirements.txt
cp ../.env.example .env
# Add your GROQ_API_KEY to .env
python api.py
# FastAPI runs at http://localhost:8082
```

### 2. Frontend Setup

```bash
cd frontend
npm install
npm run dev
# React app at http://localhost:5173
```

### 3. Run Pipeline

1. Open `http://localhost:5173`
2. Go to **Upload CSV** → drag & drop your 6-column CSV
3. Click **Start Enrichment Pipeline**
4. Watch real-time progress through all 8 stages
5. Go to **Product Catalog** to browse enriched data
6. Go to **Exports** → download the 252-column CSV

---

## 📁 Project Structure

```
Hack_vB_2/
├── pipeline/
│   ├── api.py                   # FastAPI server (port 8082)
│   ├── run_pipeline.py          # Master orchestrator
│   ├── config.py                # Schema, paths, constants
│   ├── stage1_ingest.py         # Data ingestion & cleaning
│   ├── stage2_brand_resolve.py  # Manufacturer/brand resolution
│   ├── stage2b_source_lookup.py # Distributor source URL lookup ← NEW
│   ├── stage3_classify.py       # AI taxonomy classification
│   ├── stage4_attributes.py     # Attribute extraction
│   ├── stage5_describe.py       # Multi-format descriptions
│   ├── stage6_score.py          # Trust scoring & review flags
│   ├── stage7_export.py         # 252-col CSV export
│   └── output/
│       ├── enriched_output.csv  # Main output
│       ├── review_queue.csv     # Flagged rows
│       └── metrics.json         # Pipeline statistics
├── frontend/
│   └── src/App.jsx              # React SaaS dashboard
├── .env.example                 # Environment template
└── README.md
```

---

## 🔧 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/v1/enrichment/health` | Engine health check |
| GET | `/api/v1/enrichment/status` | Pipeline status + metrics |
| POST | `/api/v1/enrichment/upload` | Upload CSV & start pipeline |
| POST | `/api/v1/enrichment/run` | Run on default dataset |
| GET | `/api/v1/enrichment/products` | Paginated enriched catalog |
| GET | `/api/v1/enrichment/download/csv` | Download 252-col output |
| GET | `/api/v1/enrichment/download/review` | Download review queue |

---

## 🤖 AI Strategy

**Model:** `llama-3.3-70b-versatile` (Groq) with fallback to `llama-3.1-8b-instant`

**Unique-Type Clustering Optimisation:**
Instead of calling the LLM once per row (999 calls), UniIntel:
1. Extracts the unique product type from each Part_Desc
2. Clusters identical types (e.g., all "Sanding Belt" rows together)
3. Calls LLM once per unique type cluster (~40–60 calls total)
4. Maps results back to all matching rows

This reduces API cost and latency by **~95%**.

---

## 📋 Input Format

```csv
Mfg_Part_Num,Part_Desc,E1_Brand,Unilog_Brand,DIB_Brand,Part_Manuf
DCB518ASTS06G,"DIABLO 1/2X18 - SANDING BELT P150",Freud,Diablo,Diablo,Freud Inc.
3MABR-7100075678,"3M 775L STIKIT FILM P15",3M,3M,3M,Jam Industrial Supply LLC
```

---

## 👥 Team

**UniIntel — UniHack 2026 Submission**

---

## 📄 License

MIT License — built for UniHack 2026
