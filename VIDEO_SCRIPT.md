# 🎬 UniIntel — Video Presentation & Demo Script
### UniHack 2026 | Submission ID: UNIH-2435

---

## ⏱️ Video Structure Overview (Target Duration: 2 to 3 minutes)

| Timestamp | Section | Screen to Show |
|---|---|---|
| **0:00 - 0:30** | Introduction & Problem Statement | `presentation.html` (Slide 1) |
| **0:30 - 1:15** | System Architecture & Pipeline Flow | `presentation.html` (Slide 2 & 3) |
| **1:15 - 2:00** | Live Demo of UniIntel Web App | `http://localhost:5173` (Upload ➔ Pipeline ➔ Catalog) |
| **2:00 - 2:30** | Source Verification & Review Queue | Web App (Product Catalog & Exports Tab) |
| **2:30 - 3:00** | Results & Conclusion | `presentation.html` (Slide 6) |

---

## 🎙️ Word-for-Word Video Script

### 📍 SECTION 1: Introduction & Problem Statement (0:00 - 0:30)
**[Screen: Show `presentation.html` - Slide 1]**

> *"Hello everyone! I’m presenting **UniIntel**, our AI-powered Product Data Enrichment Engine built for UniHack 2026.*
>
> *In industrial catalog management, distributors receive raw, noisy product files containing just 6 basic columns like part number, description, and brand fields. However, Unilog's delivery standard demands **252 structured columns** — including multi-depth taxonomy, up to 50 spec pairs, 5 compliant description formats, and verifiable source URLs.*
>
> *Manually processing thousands of SKUs takes weeks and leads to human errors. UniIntel automates this entire process in under 1 minute using an 8-stage AI pipeline."*

---

### 📍 SECTION 2: Architecture & Source Verification (0:30 - 1:15)
**[Screen: Switch to `presentation.html` - Slide 2 & 3]**

> *"Let’s look at our architecture.*
>
> *UniIntel processes raw CSVs through an 8-stage pipeline:*
> 1. **Stage 1 (Ingest):** Cleans placeholders like 'N/A' or 'TBD' and deduplicates MPNs.
> 2. **Stage 2 (Brand Resolve):** Fuzzy matches manufacturer names against our canonical database — resolving variations like '3 M Co' to '3M Company'.
> 3. **Stage 2b (Source URL Lookup):** This directly addresses the PS requirement. We map canonical manufacturer homepage URLs plus generate direct search verification links for Grainger, MSC Direct, McMaster-Carr, and Fastenal for every single row.
> 4. **Stage 3 (AI Taxonomy):** Uses a hybrid engine combining keyword matching and **Groq Qwen 27B LLM**. We implemented **Smart LLM Clustering** — instead of calling the LLM 1,000 times, we cluster items by 50 unique product types, saving 95% API cost and latency.
> 5. **Stage 4 & 5 (Attributes & Descriptions):** Extracts up to 50 specification pairs, standardises units of measure, and generates 5 description formats, including **Invoice Description under 40 characters in ALL CAPS** and Mobile Description between 50 to 90 characters.
> 6. **Stage 6 & 7 (Trust Scoring & Export):** Calculates a 5-factor quality score (0-100) and exports the exact 252-column Unilog Delivery CSV."*

---

### 📍 SECTION 3: Live Application Demo (1:15 - 2:00)
**[Screen: Switch to Web App at `http://localhost:5173`]**

> *"Now let's see UniIntel in action!*
>
> *Here is our Apple-inspired SaaS Dashboard. On the **Upload CSV** tab, we can drag and drop any 6-column catalog file.*
>
> *When we click **Start Enrichment Pipeline**, we enter the **Pipeline** tab where we see real-time progress across all 8 stages. Notice our system health is green and active.*
>
> *Once completed, we switch to the **Product Catalog** tab. Here we see 999 enriched records rendered in the exact 252-column Unilog delivery layout. You can inspect canonical brands, Dept > Class > Fine classpaths, formatted invoice descriptions, and extracted attributes like Grit, Size, and Voltage."*

---

### 📍 SECTION 4: Source URL Verification & Exports (2:00 - 2:30)
**[Screen: Show Product Catalog table & scroll to Source URLs, then click Exports Tab]**

> *"To prove data authenticity, if we inspect the **MFR URL** and **Ref URL** columns, every product is linked with verifiable distributor endpoints.*
>
> *On the **Exports** tab, users can instantly download two files:*
> 1. The complete **252-Column Unilog Delivery CSV** for automated catalog ingestion.
> 2. The **Human Review Queue CSV**, which flags any low-confidence or non-compliant rows for manual audit."*

---

### 📍 SECTION 5: Results & Conclusion (2:30 - 3:00)
**[Screen: Switch to `presentation.html` - Slide 6]**

> *"In summary, on our 999-row benchmark dataset, UniIntel achieved:*
> - **100% Ground Truth Accuracy** on key fields.
> - **4,995 Multi-format descriptions** generated.
> - **95% LLM API savings** via unique-type clustering.
> - Full compliance with Unilog’s 252-column delivery standard.
>
> *Thank you! UniIntel is fully deployed on Vercel and Render, and ready for evaluator testing."*

---

## 📌 Recording Tips:
1. Open two browser tabs before starting:
   - Tab 1: `presentation.html` (in full screen or clean window)
   - Tab 2: `http://localhost:5173`
2. Keep voice clear, enthusiastic, and steady.
3. Use slide buttons at the top of `presentation.html` to smoothly transition between slides!
