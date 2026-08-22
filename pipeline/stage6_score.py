"""
Stage 6 — Confidence Scoring & Human Review Flags
Computes a comprehensive Trust/Quality Score (0-100) per row and flags low-confidence items.

Scoring breakdown:
  30% Brand Resolution confidence
  25% Taxonomy Classpath confidence
  20% Description compliance (Invoice <=40 chars, Mobile length)
  15% Attribute completeness
  10% Source URL presence bonus
"""
import pandas as pd
from config import CONFIDENCE_THRESHOLD

def calculate_row_confidence(row: pd.Series) -> dict:
    """Calculate weighted overall confidence score (0-100) for an enriched row."""

    # 1. Brand Confidence (weight 30%) — default 65 if unknown
    b_conf = float(row.get("brand_confidence", 65))
    b_conf = max(0.0, min(100.0, b_conf))

    # 2. Classpath Confidence (weight 25%) — default 65 for keyword-matched rows
    c_conf = float(row.get("classpath_confidence", 65))
    c_conf = max(0.0, min(100.0, c_conf))

    # 3. Description compliance (weight 20%)
    inv_desc = str(row.get("INVOICE_DESC", ""))
    mob_desc = str(row.get("MOBILE_DESC", ""))
    inv_len  = len(inv_desc)
    mob_len  = len(mob_desc)

    desc_score = 100.0
    # Invoice desc must be <=40 chars, ALL CAPS
    if inv_len == 0:
        desc_score -= 50.0
    elif inv_len > 40:
        desc_score -= 30.0
    elif not inv_desc.isupper():
        desc_score -= 10.0

    # Mobile desc ideally 50-90 chars
    if mob_len == 0:
        desc_score -= 30.0
    elif mob_len < 30:
        desc_score -= 15.0
    elif mob_len > 100:
        desc_score -= 10.0

    desc_score = max(0.0, desc_score)

    # 4. Attribute completeness (weight 15%)
    attr1_lbl = str(row.get("ATTRIBUTE_LABEL 1", "")).strip()
    attr2_lbl = str(row.get("ATTRIBUTE_LABEL 2", "")).strip()
    attr3_lbl = str(row.get("ATTRIBUTE_LABEL 3", "")).strip()

    attr_count = sum([bool(attr1_lbl), bool(attr2_lbl), bool(attr3_lbl)])
    attr_score = min(100.0, attr_count * 33.0 + 10.0)  # 10 base + 33 per attr

    # 5. Source URL presence bonus (weight 10%)
    ref_url = str(row.get("Ref URL 1", "")).strip()
    mfr_url = str(row.get("MFR URL", "")).strip()
    src_score = 100.0 if (ref_url or mfr_url) else 40.0

    # Weighted total
    total_score = (
        b_conf     * 0.30 +
        c_conf     * 0.25 +
        desc_score * 0.20 +
        attr_score * 0.15 +
        src_score  * 0.10
    )
    total_score = round(min(100.0, max(0.0, total_score)), 1)

    # Flag for human review only if genuinely low quality
    needs_review = (
        total_score < CONFIDENCE_THRESHOLD or
        (b_conf < 50 and c_conf < 50) or   # both brand AND taxonomy uncertain
        inv_len > 40 or                      # invoice desc compliance fail
        inv_len == 0                         # no invoice desc at all
    )

    return {
        "overall_confidence": total_score,
        "NEEDS_HUMAN_REVIEW": needs_review
    }


def score_all(df: pd.DataFrame) -> pd.DataFrame:
    scores = df.apply(calculate_row_confidence, axis=1, result_type="expand")
    df = pd.concat([df, scores], axis=1)

    avg_score = df["overall_confidence"].mean()
    flagged   = int(df["NEEDS_HUMAN_REVIEW"].sum())

    print(f"[Stage 6] Scoring complete. Avg Score: {avg_score:.1f}/100. Review Queue: {flagged}/{len(df)}")
    return df


if __name__ == "__main__":
    from stage1_ingest import load_and_clean
    from stage2_brand_resolve import resolve_all_brands
    from stage3_classify import classify_all
    from stage4_attributes import extract_all_attributes
    from stage5_describe import generate_descriptions

    df = load_and_clean()
    df = resolve_all_brands(df)
    df = classify_all(df)
    df = extract_all_attributes(df)
    df = generate_descriptions(df)
    df = score_all(df)
    print(df[["Mfg_Part_Num", "overall_confidence", "NEEDS_HUMAN_REVIEW"]].head(15).to_string())
