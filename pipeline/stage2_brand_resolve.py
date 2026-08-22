"""
Stage 2 — Manufacturer & Brand Resolution
Fuzzy-matches raw manufacturer strings to canonical approved names.
"""
import re
import pandas as pd
try:
    from rapidfuzz import fuzz, process
except ImportError:
    try:
        from thefuzz import fuzz, process
    except ImportError:
        import difflib
        class process:
            @staticmethod
            def extractOne(query, choices, **kwargs):
                matches = difflib.get_close_matches(query, choices, n=1, cutoff=0.6)
                if matches:
                    ratio = int(difflib.SequenceMatcher(None, query, matches[0]).ratio() * 100)
                    return matches[0], ratio, 0
                return None, 0, 0
        class fuzz:
            token_set_ratio = None

from config import MANUFACTURER_CORRECTIONS, CONFIDENCE_THRESHOLD


# Build a normalised key → (canonical_name, brand) lookup
_NORM_MAP = {
    re.sub(r"[^a-z0-9 ]", "", k.lower()): v
    for k, v in MANUFACTURER_CORRECTIONS.items()
}

# Supplementary brand hint: keywords in Part_Desc that signal a brand
_DESC_BRAND_HINTS = {
    "diablo":      ("Freud Inc.", "Diablo®"),
    "cubitron":    ("3M Company", "3M™"),
    "abranet":     ("Mirka Abrasives Inc.", "Mirka®"),
    "hiolit":      ("Mirka Abrasives Inc.", "Mirka®"),
    "milw":        ("Milwaukee Tool", "Milwaukee®"),
    "milwaukee":   ("Milwaukee Tool", "Milwaukee®"),
    "dewalt":      ("Stanley Black & Decker, Inc.", "DEWALT®"),
    "makita":      ("Makita U.S.A., Inc.", "Makita®"),
    "kreg":        ("Kreg Tool Company", "Kreg®"),
    "paslode":     ("Illinois Tool Works Inc.", "Paslode®"),
    "vessel":      ("Vessel Tools USA Inc.", "Vessel®"),
    "bosch":       ("Robert Bosch Tool Corporation", "BOSCH®"),
    "ridgid":      ("Emerson Electric Co.", "RIDGID®"),
    "ryobi":       ("Techtronic Industries Co. Ltd.", "RYOBI®"),
    "metabo":      ("Metabo Corporation", "Metabo®"),
    "festool":     ("TTS Tooltechnic Systems AG & Co. KG", "Festool®"),
    "flex":        ("Flex Tools USA LLC", "Flex®"),
    "hilti":       ("Hilti, Inc.", "Hilti®"),
    "porter cable": ("Stanley Black & Decker, Inc.", "PORTER-CABLE®"),
    "craftsman":   ("Stanley Black & Decker, Inc.", "CRAFTSMAN®"),
    "stanley":     ("Stanley Black & Decker, Inc.", "Stanley®"),
    "irwin":       ("Irwin Industrial Tool Company", "IRWIN®"),
    "lenox":       ("Lenox Industrial Tools", "LENOX®"),
    "norton":      ("Saint-Gobain Abrasives, Inc.", "Norton®"),
    "3m":          ("3M Company", "3M™"),
    "mirka":       ("Mirka Abrasives Inc.", "Mirka®"),
    "freud":       ("Freud Inc.", "Freud®"),
}


def _normalise_key(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", s.lower().strip())


def resolve_brand(row: pd.Series) -> dict:
    """
    Given a DataFrame row, return dict with:
        manufacturer_name, brand_name, brand_confidence
    Resolution priority:
      1. Exact match in MANUFACTURER_CORRECTIONS (normalised key)
      2. Desc keyword hints
      3. Fuzzy match of manuf name
      4. Fallback: use raw manuf name as-is
    """
    manuf_raw = str(row.get("_manuf_name", "")).strip()
    desc      = str(row.get("Part_Desc", "")).lower()
    dib_brand = str(row.get("DIB_Brand", "")).strip()

    key = _normalise_key(manuf_raw)

    # 1. Exact correction table
    if key in _NORM_MAP:
        mname, bname = _NORM_MAP[key]
        return {"MANUFACTURER_NAME": mname, "BRAND_NAME": bname, "brand_confidence": 95}

    # 2. Fuzzy match against correction table keys
    candidates = list(_NORM_MAP.keys())
    if candidates:
        match, score, _ = process.extractOne(key, candidates, scorer=fuzz.token_set_ratio)
        if score >= 80:
            mname, bname = _NORM_MAP[match]
            return {"MANUFACTURER_NAME": mname, "BRAND_NAME": bname, "brand_confidence": int(score)}

    # 3. Description keyword hint
    for kw, (mname, bname) in _DESC_BRAND_HINTS.items():
        if kw in desc:
            return {"MANUFACTURER_NAME": mname, "BRAND_NAME": bname, "brand_confidence": 85}

    # 4. DIB_Brand hint
    if dib_brand:
        for kw, (mname, bname) in _DESC_BRAND_HINTS.items():
            if kw in dib_brand.lower():
                return {"MANUFACTURER_NAME": mname, "BRAND_NAME": bname, "brand_confidence": 75}

    # 5. Fallback
    fallback_name = manuf_raw if manuf_raw else "Unknown Manufacturer"
    return {
        "MANUFACTURER_NAME": fallback_name,
        "BRAND_NAME": dib_brand or fallback_name,
        "brand_confidence": 40,
    }


def resolve_all_brands(df: pd.DataFrame) -> pd.DataFrame:
    results = df.apply(resolve_brand, axis=1, result_type="expand")
    df = pd.concat([df, results], axis=1)
    avg = df["brand_confidence"].mean()
    low = (df["brand_confidence"] < CONFIDENCE_THRESHOLD).sum()
    print(f"[Stage 2] Brand resolved. Avg confidence: {avg:.1f}. Low-confidence rows: {low}")
    return df


if __name__ == "__main__":
    from stage1_ingest import load_and_clean
    df = load_and_clean()
    df = resolve_all_brands(df)
    print(df[["Mfg_Part_Num", "MANUFACTURER_NAME", "BRAND_NAME", "brand_confidence"]].head(15).to_string())
