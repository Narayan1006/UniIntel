"""
Stage 6 — Confidence Scoring & Human Review Flags
Computes a comprehensive Trust/Quality Score (0-100) per row and flags low-confidence items.
"""
import pandas as pd
from config import CONFIDENCE_THRESHOLD

def calculate_row_confidence(row: pd.Series) -> dict:
    """Calculate weighted overall confidence score (0-100) for an enriched row."""
    # 1. Brand Confidence (weight 30%)
    b_conf = float(row.get("brand_confidence", 50))
    
    # 2. Classpath Confidence (weight 30%)
    c_conf = float(row.get("classpath_confidence", 50))
    
    # 3. Attribute Completeness (weight 20%)
    attr1_lbl = str(row.get("ATTRIBUTE_LABEL 1", ""))
    attr_score = 90.0 if attr1_lbl else 40.0
    
    # 4. Description compliance (weight 20%)
    inv_len = len(str(row.get("INVOICE_DESC", "")))
    mob_len = len(str(row.get("MOBILE_DESC", "")))
    
    desc_score = 100.0
    if inv_len > 40:
        desc_score -= 40.0
    if mob_len < 50 or mob_len > 90:
        desc_score -= 20.0
        
    desc_score = max(0.0, desc_score)
    
    # Total Score
    total_score = (b_conf * 0.30) + (c_conf * 0.30) + (attr_score * 0.20) + (desc_score * 0.20)
    total_score = round(total_score, 1)
    
    needs_review = total_score < CONFIDENCE_THRESHOLD or b_conf < 70 or c_conf < 70
    
    return {
        "overall_confidence": total_score,
        "NEEDS_HUMAN_REVIEW": needs_review
    }


def score_all(df: pd.DataFrame) -> pd.DataFrame:
    scores = df.apply(calculate_row_confidence, axis=1, result_type="expand")
    df = pd.concat([df, scores], axis=1)
    
    avg_score = df["overall_confidence"].mean()
    flagged   = df["NEEDS_HUMAN_REVIEW"].sum()
    
    print(f"[Stage 6] Scoring complete. Average Overall Score: {avg_score:.1f}/100. Flagged for review: {flagged}/{len(df)}")
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
