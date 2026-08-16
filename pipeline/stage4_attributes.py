"""
Stage 4 — Attribute Extraction & Normalization
Extracts dimensions, grit, voltage, gauge, sound level, series, and key product attributes
from raw description and normalises values & UOMs against approved standards.
"""
import re
import pandas as pd
from config import DECIMAL_TO_FRACTION, UOM_MAP

def decimal_to_frac_str(dec_val: float) -> str:
    """Convert decimal inches to fractional inches if match found."""
    whole = int(dec_val)
    frac = dec_val - whole
    # find closest matching fraction key
    closest_key = None
    min_diff = 0.005
    for k, v in DECIMAL_TO_FRACTION.items():
        diff = abs(frac - k)
        if diff < min_diff:
            min_diff = diff
            closest_key = k
    
    if closest_key:
        frac_str = DECIMAL_TO_FRACTION[closest_key]
        return f"{whole}-{frac_str}" if whole > 0 else frac_str
    return str(dec_val)


def normalize_uom(uom: str) -> str:
    """Normalise UOM string to approved UOM abbreviation."""
    if not uom:
        return ""
    uom_clean = uom.strip()
    for canon, aliases in UOM_MAP.items():
        if uom_clean in aliases or uom_clean == canon:
            return canon
    return uom_clean


def extract_attributes_from_desc(desc: str, mpn: str = "") -> dict:
    """
    Extract structured key-value attributes from Part_Desc.
    Returns dict of attribute definitions and features.
    """
    attrs = []
    features = []
    
    # 1. Grit Extraction (e.g., P80, P120, P150, P180, P220, P320)
    grit_match = re.search(r"\b(P\d{2,4})\b", desc, re.IGNORECASE)
    if grit_match:
        attrs.append({"label": "Grit", "value": grit_match.group(1).upper(), "uom": ""})
    
    # 2. Voltage (e.g., 18V, 20V, 120V, 12V)
    volt_match = re.search(r"\b(\d+)\s*V\b", desc, re.IGNORECASE)
    if volt_match:
        attrs.append({"label": "Voltage Rating", "value": volt_match.group(1), "uom": "V"})
        
    # 3. Amperage (e.g., 15A, 10A)
    amp_match = re.search(r"\b(\d+)\s*A\b", desc, re.IGNORECASE)
    if amp_match:
        attrs.append({"label": "Amperage Rating", "value": amp_match.group(1), "uom": "A"})
        
    # 4. Gauge (e.g. 18GA, 16GA)
    ga_match = re.search(r"\b(\d+)\s*GA\b", desc, re.IGNORECASE)
    if ga_match:
        attrs.append({"label": "Fastener Gauge", "value": ga_match.group(1), "uom": "GA"})

    # 5. Sound level (e.g., 41 dBA, 47 dBA)
    sound_match = re.search(r"\b(\d+)\s*dBA\b", desc, re.IGNORECASE)
    if sound_match:
        attrs.append({"label": "Sound Level", "value": sound_match.group(1), "uom": "dBA"})

    # 6. Dimensions (e.g., 1/2"x18", 5", 2.75x30, 4x6x6, 12"x20mm, 7"x1/16"x7/8", 4-1/2"x.045"x7/8")
    dim_3_match = re.search(r'([\d\/\.\-]+)["″]?\s*x\s*([\d\/\.\-]+)["″]?\s*x\s*([\d\/\.\-]+(?:mm|in)?)', desc, re.IGNORECASE)
    if dim_3_match:
        val = f"{dim_3_match.group(1)} x {dim_3_match.group(2)} x {dim_3_match.group(3)}"
        attrs.append({"label": "Size", "value": val, "uom": ""})
    else:
        dim_2_match = re.search(r'([\d\/\.\-]+)["″]?\s*x\s*([\d\/\.\-]+(?:mm|in)?)', desc, re.IGNORECASE)
        if dim_2_match:
            val = f"{dim_2_match.group(1)} x {dim_2_match.group(2)}"
            attrs.append({"label": "Size", "value": val, "uom": ""})
        else:
            dim_1_match = re.search(r'(\b\d+(?:-\d+/\d+|\.\d+|/\d+)?)\s*(?:["″]|in\b|inch\b)', desc, re.IGNORECASE)
            if dim_1_match and not volt_match:
                attrs.append({"label": "Diameter / Size", "value": dim_1_match.group(1), "uom": "in"})

    # 7. Series identification
    series_names = [
        "Cubitron II", "Steel Demon", "Speed Demon", "Perform+", "Performance+",
        "Ceramic+", "Professional Series", "Eco Series", "Stikit", "Abranet", "HIOLIT"
    ]
    extracted_series = ""
    for sname in series_names:
        if sname.lower() in desc.lower():
            extracted_series = sname
            attrs.append({"label": "Series", "value": sname, "uom": ""})
            break

    # 8. Features & Keywords
    if "brushless" in desc.lower():
        features.append("Brushless Motor Technology")
    if "cordless" in desc.lower() or "bare" in desc.lower():
        features.append("Cordless Operation")
        attrs.append({"label": "Power Source", "value": "Battery", "uom": ""})
    if "bare" in desc.lower() or "tool - only" in desc.lower():
        features.append("Tool Only / Bare Tool")
    if "kit" in desc.lower():
        features.append("Includes Battery & Charger Kit")
    if "disc" in desc.lower() or "wheel" in desc.lower():
        features.append("High Performance Abrasive Disc")
    if "pack" in desc.lower() or "pc" in desc.lower():
        pc_m = re.search(r"(\d+)\s*(?:pc|pack|disc/box)", desc, re.IGNORECASE)
        if pc_m:
            attrs.append({"label": "Package Quantity", "value": pc_m.group(1), "uom": "pc"})

    return {
        "attributes": attrs,
        "features": features,
        "series": extracted_series
    }


def extract_all_attributes(df: pd.DataFrame) -> pd.DataFrame:
    """Extract and assign up to 50 ATTRIBUTE_LABEL/VALUE/UOM columns and ITEM_FEATURES."""
    all_extracted = []
    
    for _, row in df.iterrows():
        desc = str(row.get("Part_Desc", ""))
        mpn  = str(row.get("Mfg_Part_Num", ""))
        res  = extract_attributes_from_desc(desc, mpn)
        all_extracted.append(res)
        
    # Populate feature columns and attribute pairs
    for i in range(1, 21):
        feat_col = f"ITEM_FEATURES_{i}"
        df[feat_col] = [
            ext["features"][i-1] if len(ext["features"]) >= i else ""
            for ext in all_extracted
        ]
        
    for i in range(1, 51):
        lbl_col = f"ATTRIBUTE_LABEL {i}"
        val_col = f"ATTRIBUTE_VALUE {i}"
        uom_col = f"ATTRIBUTE_UOM {i}"
        
        lbl_vals = []
        val_vals = []
        uom_vals = []
        
        for ext in all_extracted:
            attrs = ext["attributes"]
            if len(attrs) >= i:
                item = attrs[i-1]
                lbl_vals.append(item["label"])
                val_vals.append(item["value"])
                uom_vals.append(normalize_uom(item["uom"]))
            else:
                lbl_vals.append("")
                val_vals.append("")
                uom_vals.append("")
                
        df[lbl_col] = lbl_vals
        df[val_col] = val_vals
        df[uom_col] = uom_vals
        
    df["Extracted_Series"] = [ext["series"] for ext in all_extracted]
    print(f"[Stage 4] Attribute extraction complete for {len(df)} rows.")
    return df


if __name__ == "__main__":
    from stage1_ingest import load_and_clean
    df = load_and_clean()
    df = extract_all_attributes(df)
    print(df[["Mfg_Part_Num", "ATTRIBUTE_LABEL 1", "ATTRIBUTE_VALUE 1", "ATTRIBUTE_UOM 1", "ITEM_FEATURES_1"]].head(10).to_string())
