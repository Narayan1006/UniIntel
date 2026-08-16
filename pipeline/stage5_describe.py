"""
Stage 5 — Description Building
Generates 5 distinct description fields following strict Unilog character limits and formulas:
- INVOICE_DESC (<=40 chars, ALL CAPS)
- MOBILE_DESC (60-80 chars)
- SHORT_DESC (Product Title / Short Description formula)
- LONG_DESC1 (Comprehensive technical spec sentence)
- RETAIL_DESC (Marketing description)
"""
import re
import pandas as pd

def build_invoice_desc(brand: str, mpn: str, raw_desc: str) -> str:
    """Generate INVOICE_DESC: strictly <= 40 chars, ALL CAPS."""
    # Strip MPN if repeated at start of raw_desc
    clean_desc = raw_desc
    if raw_desc.startswith(mpn):
        clean_desc = raw_desc[len(mpn):].strip()
        
    # Replace standard abbreviations for space saving
    replacements = [
        (r"\bPerformance\+\b", "PERF+"),
        (r"\bSpeed Demon\b", "SPD DEMON"),
        (r"\bSteel Demon\b", "STL DEMON"),
        (r"\bCut-Off Disc\b", "CUT OFF DISC"),
        (r"\bCut Off Disc\b", "CUT OFF DISC"),
        (r"\bSanding Belt\b", "SAND BELT"),
        (r"\bStikit Film\b", "STIKIT FILM"),
        (r"\bBrushless\b", "BRSHLS"),
        (r"\bCompact\b", "CMPCT"),
        (r"\bScrew Driver\b", "SCRWDRVR"),
        (r"\bScrewdriver\b", "SCRWDRVR"),
        (r"\bHedge Trimmer\b", "HDG TRMR"),
        (r"\bTrimmer\b", "TRMR"),
        (r'\b"x\b', "IN X "),
        (r'\b"\b', "IN"),
    ]
    
    text = clean_desc.upper()
    for pattern, repl in replacements:
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
        
    # Combine MPN and key text
    res = f"{mpn} {text}".strip()
    res = re.sub(r"\s+", " ", res)
    
    if len(res) > 40:
        # Fallback short format
        res = f"{mpn} {clean_desc.upper()}"[:40].rstrip()
    return res.upper()


def build_mobile_desc(brand: str, series: str, mpn: str, fine_cat: str, raw_desc: str) -> str:
    """Generate MOBILE_DESC: targeted length 60-80 chars. Formula: Brand, Product Type, Series, MPN."""
    clean_brand = re.sub(r"[®™]", "", brand).strip()
    item_type = fine_cat if fine_cat else "Item"
    
    parts = [clean_brand, item_type]
    if series:
        parts.append(f"{series} Series")
    parts.append(mpn)
    
    res = ", ".join(parts)
    
    if len(res) < 60:
        # Add descriptive fragment from raw_desc
        extra = raw_desc.replace(mpn, "").strip(" -")
        if extra:
            res = f"{res}, {extra}"
            
    if len(res) > 80:
        res = res[:80].rsplit(" ", 1)[0]
    return res


def build_short_desc(brand: str, series: str, mpn: str, fine_cat: str, attrs_str: str, raw_desc: str) -> str:
    """Generate SHORT_DESC / Product Title formula = Brand + Series + MPN + Item Type + Key Attributes."""
    item_type = fine_cat if fine_cat else ""
    parts = [brand]
    if series:
        parts.append(f"{series} Series")
    parts.append(mpn)
    if item_type:
        parts.append(item_type)
        
    base = " ".join(parts)
    
    # Append key extracted details if present
    extra_details = raw_desc.replace(mpn, "").strip(" -")
    if extra_details and extra_details.lower() not in base.lower():
        res = f"{base} With {extra_details}"
    else:
        res = base
    return res


def build_long_desc(brand: str, series: str, mpn: str, fine_cat: str, raw_desc: str) -> str:
    """Generate LONG_DESC1: Full sentence technical specification."""
    parts = [brand]
    if fine_cat:
        parts.append(fine_cat)
    if series:
        parts.append(f"{series} Series")
        
    body = raw_desc.replace(mpn, "").strip(" -")
    if body:
        parts.append(body)
        
    return f"{' '.join(parts)}, MPN: {mpn}."


def generate_descriptions(df: pd.DataFrame) -> pd.DataFrame:
    invoices = []
    mobiles  = []
    shorts   = []
    longs    = []
    retails  = []
    
    for _, row in df.iterrows():
        brand     = str(row.get("BRAND_NAME", ""))
        mpn       = str(row.get("Mfg_Part_Num", ""))
        raw_desc  = str(row.get("Part_Desc", ""))
        fine      = str(row.get("Fine", ""))
        series    = str(row.get("Extracted_Series", ""))
        
        inv  = build_invoice_desc(brand, mpn, raw_desc)
        mob  = build_mobile_desc(brand, series, mpn, fine, raw_desc)
        sh   = build_short_desc(brand, series, mpn, fine, "", raw_desc)
        lg   = build_long_desc(brand, series, mpn, fine, raw_desc)
        ret  = f"{brand} {series} {mpn} {fine}".strip()
        
        invoices.append(inv)
        mobiles.append(mob)
        shorts.append(sh)
        longs.append(lg)
        retails.append(ret)
        
    df["INVOICE_DESC"] = invoices
    df["MOBILE_DESC"]  = mobiles
    df["SHORT_DESC"]   = shorts
    df["LONG_DESC1"]   = longs
    df["RETAIL_DESC"]  = retails
    df["MARKETING_DESCRIPTION"] = longs
    
    print(f"[Stage 5] Generated 5-format descriptions for {len(df)} rows.")
    return df


if __name__ == "__main__":
    from stage1_ingest import load_and_clean
    from stage2_brand_resolve import resolve_all_brands
    from stage3_classify import classify_all
    from stage4_attributes import extract_all_attributes
    
    df = load_and_clean()
    df = resolve_all_brands(df)
    df = classify_all(df)
    df = extract_all_attributes(df)
    df = generate_descriptions(df)
    print(df[["Mfg_Part_Num", "INVOICE_DESC", "MOBILE_DESC", "SHORT_DESC"]].head(10).to_string())
