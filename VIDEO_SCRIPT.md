# 🎬 UniIntel — Official UniHack Video Demo & Presentation Script
### UniHack 2026 | Submission ID: UNIH-2435 | Team: UniIntel

---

## ⏱️ Video Structure & Slide Timing (Target: 3 Minutes / 180 Seconds)

| Timestamp | Slide / Screen | Content Focus |
|---|---|---|
| **0:00 - 0:20** | **Slide 1 & 2** (Title & Team) | Introduction, Team Details & Problem Statement Overview |
| **0:20 - 0:45** | **Slide 3 & 4** (Solution & Core Qs) | 6-Column Input ➔ 252-Column Unilog Transformation & Trust Strategy |
| **0:45 - 1:10** | **Slide 5 & 6** (USP & Features) | 95% LLM Rate Savings, Verifiable MFR + 4 Distributor Links |
| **1:10 - 2:00** | **Live Web App Demo** (`http://localhost:5173`) | Drag-Drop CSV ➔ Live 8-Stage Pipeline ➔ Enriched 252-Col Catalog Table |
| **2:00 - 2:30** | **Slide 7, 8, 9 & 10** (Architecture & Tech) | Process Flow, System Architecture Diagram & Tech Stack |
| **2:30 - 3:00** | **Slide 12 & 14** (Results & Links) | 100% Ground Truth Accuracy, Export CSVs & Live Submission Links |

---

## 🎙️ Word-for-Word Video Script

### 📍 SECTION 1: Intro, Team & Problem Statement (0:00 - 0:20)
**[Screen: Open `presentation.html` -> Slide 1 & 2]**

> *"Hello judges! I am Narayan Singh presenting **UniIntel** — our AI-powered Product Data Enrichment Engine built for UniHack 2026 under submission ID UNIH-2435.*
>
> *In industrial catalog management, distributors receive raw, unstandardised product CSVs with only 6 basic columns like part number, description, and brand fields. However, Unilog's delivery standard demands **252 structured columns** — including multi-depth taxonomy, up to 50 spec pairs, 5 compliant description formats, and verifiable source URLs.*
>
> *Manual processing takes weeks and leads to human errors. UniIntel automates this entire transformation in under 60 seconds."*

---

### 📍 SECTION 2: Solution, Core Questions & USP (0:20 - 1:10)
**[Screen: Click Slide 3, 4, 5 & 6]**

> *"Here is how UniIntel solves the problem:*
>
> *1. **Minimal Info Enrichment:** We transform limited 6-column inputs into 252 attributes using pattern regex, UOM standardisation, fraction conversion, and Groq LLM taxonomy classification.*
>
> *2. **Verifiable Data Sources & Accuracy:** To guarantee trust, every populated row includes primary manufacturer homepage links + 4 major distributor search verification links for Grainger, MSC Direct, McMaster-Carr, and Fastenal.*
>
> *3. **Our Key USP (Smart LLM Clustering):** Instead of making 1,000 individual LLM calls, UniIntel clusters raw items into 50 unique product types. This reduces API calls from 1,000 down to 14 — saving **95% in API costs and latency** while avoiding rate limits.*
>
> *4. **Quality & Trust Score:** We compute a 5-factor weighted confidence score (0-100) per row and automatically isolate low-confidence items into a separate Human Review Queue CSV."*

---

### 📍 SECTION 3: Live Application Demo (1:10 - 2:00)
**[Screen: Switch to Live Web App at `http://localhost:5173`]**

> *"Now let's see UniIntel running live!*
>
> *This is our Apple-inspired SaaS Web Application. On the **Upload CSV** tab, we can drag and drop any raw 6-column catalog CSV.*
>
> *When we click **Start Enrichment Pipeline**, the system processes through our **8 Parallel AI Stages** in real-time — cleaning data, resolving brand names, fetching distributor source links, classifying taxonomy via Groq Qwen 27B, extracting attributes, and generating descriptions like Invoice Description under 40 characters in ALL CAPS.*
>
> *Once done, we open the **Product Catalog** tab. Here we see 999 enriched records rendered in the exact 252-column Unilog delivery format. We can inspect canonical brands, Dept > Class > Fine classpaths, formatted descriptions, extracted spec pairs, and verified source URLs."*

---

### 📍 SECTION 4: Architecture, Tech & Cost (2:00 - 2:30)
**[Screen: Switch back to `presentation.html` -> Slide 7, 8, 9 & 10]**

> *"Looking at our technical architecture:*
>
> *- **Frontend:** React 18 & Vite SPA hosted on Vercel.*
> *- **Backend:** REST API built with FastAPI & Python hosted on Render.*
> *- **AI & Processing Engine:** Groq Qwen 27B reasoning LLM, RapidFuzz brand matching, and persistent web scraper caching.*
>
> *The entire system runs on free-tier cloud hosting with a cost of under $0.05 per 1,000 SKUs."*

---

### 📍 SECTION 5: Results & Final Submission Links (2:30 - 3:00)
**[Screen: Click Slide 12 & 14]**

> *"To summarize our benchmark results on 999 SKUs:*
> - **100% Ground Truth Accuracy** on key fields.
> - **4,995 Multi-format descriptions** generated.
> - **999 / 999 Source URLs** populated.
> - Delivery outputs ready: `enriched_output.csv` (252 columns) & `review_queue.csv`.
>
> *Our prototype is 100% live on Vercel and Render, and code is synced on GitHub.*
>
> *Thank you!"*

---

## 📌 Recording Checklist:
1. Keep two browser tabs ready:
   - **Tab 1:** `presentation.html` (Full screen)
   - **Tab 2:** `http://localhost:5173`
2. Use top navigation buttons in `presentation.html` to switch slides effortlessly!
