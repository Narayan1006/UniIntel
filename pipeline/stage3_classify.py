"""
Stage 3 — Classification
Assigns a Unilog classpath to each product using keyword matching
then Groq LLM for unmatched items (SMART: unique-type clustering reduces API calls by 95%).
"""
import re
import json
import pandas as pd
from groq import Groq
from config import CATEGORY_KEYWORDS, GROQ_API_KEY, GROQ_MODEL, GROQ_FALLBACK

_client = None

def _get_client():
    global _client
    if _client is None and GROQ_API_KEY:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


def keyword_classify(desc: str) -> tuple:
    """Keyword-first fast classification. Longer match wins."""
    desc_lower = desc.lower()
    best_path, best_len = "", 0
    for kw, path in CATEGORY_KEYWORDS.items():
        if kw in desc_lower and len(kw) > best_len:
            best_path = path
            best_len  = len(kw)
    return (best_path, 90) if best_path else ("", 0)


def _extract_product_type(desc: str, mpn: str) -> str:
    """Strip MPN, dimensions, grit codes to get a clean product-type string."""
    if desc.upper().startswith(mpn.upper()):
        desc = desc[len(mpn):].strip(" -")
    desc = re.sub(r'[\d\/\.\-]+[""]', '', desc)
    desc = re.sub(r'\b\d+V\b|\bP\d{2,4}\b|\b\d+GA\b|\b\d+pc\b', '', desc, flags=re.IGNORECASE)
    desc = re.sub(r'\b(bare|tool only|kit|display only|\d+ disc/box)\b', '', desc, flags=re.IGNORECASE)
    desc = re.sub(r'\s+', ' ', desc).strip()
    return desc[:80]


def _build_type_mapping_prompt(batch_types: list) -> str:
    items = [{"idx": i, "product_type": t} for i, t in enumerate(batch_types)]
    return f"""You are a Unilog product taxonomy expert for industrial commerce.

Map each product type to the most specific Unilog classpath.
Format: Dept>Class>Fine (exactly 3 levels, > separator, no spaces around >).

Examples of good classpaths:
- Abrasives & Finishing>Abrasive Wheels>Cut-Off Wheels
- Power Tools>Drills>Cordless Drills
- Power Tools>Nailers & Staplers>Brad Nailers
- Appliances & Consumer Electronics>Kitchen Appliances>Built-In Dishwashers
- Power Tools>Accessories>Screwdriver Bits

Product Types to classify:
{json.dumps(items, indent=2)}

Return ONLY a JSON array with keys: "idx", "classpath", "confidence" (0-100). No other text."""


def _smart_llm_classify(unclassified_rows: list) -> dict:
    """
    SMART: Cluster 750+ rows into unique product types, call LLM just 2-3 times total.
    Returns dict: row_idx -> (classpath, confidence)
    """
    client = _get_client()
    if not client:
        return {}

    # Step 1: Cluster into unique product types
    type_to_indices = {}
    for row in unclassified_rows:
        ptype = _extract_product_type(row["desc"], row.get("mpn", ""))
        if ptype not in type_to_indices:
            type_to_indices[ptype] = []
        type_to_indices[ptype].append(row["idx"])

    unique_types = list(type_to_indices.keys())
    total_calls = -(-len(unique_types) // 50)  # ceiling division
    print(f"  [Stage 3 SMART] {len(unclassified_rows)} rows → {len(unique_types)} unique types → {total_calls} LLM call(s)")

    # Step 2: Send 50 unique types per call (way fewer calls vs 1 row at a time!)
    type_to_result = {}
    for batch_start in range(0, len(unique_types), 50):
        batch = unique_types[batch_start: batch_start + 50]
        call_num = batch_start // 50 + 1
        print(f"  [Stage 3] LLM call {call_num}/{total_calls} → {len(batch)} product types...")

        prompt = _build_type_mapping_prompt(batch)
        for model in [GROQ_MODEL, GROQ_FALLBACK]:
            try:
                resp = client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.1,
                    max_tokens=3000,
                )
                text = resp.choices[0].message.content.strip()
                m = re.search(r"\[.*\]", text, re.DOTALL)
                if m:
                    for r in json.loads(m.group()):
                        idx_in_batch = r.get("idx", -1)
                        if 0 <= idx_in_batch < len(batch):
                            ptype = batch[idx_in_batch]
                            type_to_result[ptype] = (r.get("classpath", "Unclassified"), int(r.get("confidence", 70)))
                    break
            except Exception as e:
                print(f"  [Groq {model}] Error: {e}")

    # Step 3: Expand back to all original row indices
    result = {}
    for ptype, indices in type_to_indices.items():
        classpath, conf = type_to_result.get(ptype, ("Unclassified", 0))
        for idx in indices:
            result[idx] = (classpath, conf)

    classified_count = sum(1 for c, _ in result.values() if c != "Unclassified")
    print(f"  [Stage 3 SMART] LLM classified {classified_count}/{len(unclassified_rows)} rows using {total_calls} API call(s).")
    return result


def classify_all(df: pd.DataFrame) -> pd.DataFrame:
    classpaths = [""] * len(df)
    class_conf = [0]  * len(df)
    to_llm     = []

    for i, row in df.iterrows():
        path, conf = keyword_classify(str(row.get("Part_Desc", "")))
        if path:
            classpaths[i] = path
            class_conf[i] = conf
        else:
            to_llm.append({"idx": i, "desc": row.get("Part_Desc", ""), "mpn": row.get("Mfg_Part_Num", ""), "manuf": row.get("_manuf_name", "")})

    print(f"[Stage 3] Keyword matched: {len(df) - len(to_llm)} rows. Sending {len(to_llm)} to smart LLM classifier...")

    if to_llm and _get_client():
        smart_results = _smart_llm_classify(to_llm)
        for idx, (classpath, conf) in smart_results.items():
            if idx < len(classpaths):
                classpaths[idx] = classpath or "Unclassified"
                class_conf[idx] = conf
        for item in to_llm:
            if not classpaths[item["idx"]]:
                classpaths[item["idx"]] = "Unclassified"
    elif to_llm:
        print("  [Stage 3] No Groq key — rows set to 'Unclassified'.")
        for item in to_llm:
            classpaths[item["idx"]] = "Unclassified"

    df["Classpath"]            = classpaths
    df["classpath_confidence"] = class_conf

    def split_path(p):
        parts = (p.split(">") if p and p != "Unclassified" else [])
        return (parts + ["", "", ""])[:3]

    df[["Dept", "Class", "Fine"]] = df["Classpath"].apply(lambda p: pd.Series(split_path(p)))

    classified = (df["Classpath"] != "Unclassified").sum()
    print(f"[Stage 3] Total classified: {classified}/{len(df)} rows.")
    return df


if __name__ == "__main__":
    from stage1_ingest import load_and_clean
    from stage2_brand_resolve import resolve_all_brands
    df = load_and_clean()
    df = resolve_all_brands(df)
    df = classify_all(df)
    print(df[["Mfg_Part_Num", "Dept", "Class", "Fine", "classpath_confidence"]].head(20).to_string())
