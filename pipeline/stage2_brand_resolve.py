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

# ── Brand name → (canonical_manufacturer, canonical_brand) ──────────────────
# Used to resolve brand from E1_Brand / DIB_Brand / Part_Desc keywords.
_BRAND_CANONICAL = {
    # Tools
    "diablo":        ("Freud Inc.",                          "Diablo®"),
    "cubitron":      ("3M Company",                          "3M™"),
    "abranet":       ("Mirka Abrasives Inc.",                 "Mirka®"),
    "hiolit":        ("Mirka Abrasives Inc.",                 "Mirka®"),
    "milw":          ("Milwaukee Tool",                       "Milwaukee®"),
    "milwaukee":     ("Milwaukee Tool",                       "Milwaukee®"),
    "dewalt":        ("Stanley Black & Decker, Inc.",         "DEWALT®"),
    "makita":        ("Makita U.S.A., Inc.",                  "Makita®"),
    "kreg":          ("Kreg Tool Company",                    "Kreg®"),
    "paslode":       ("Illinois Tool Works Inc.",             "Paslode®"),
    "vessel":        ("Vessel Tools USA Inc.",                "Vessel®"),
    "bosch":         ("Robert Bosch Tool Corporation",        "BOSCH®"),
    "ridgid":        ("Emerson Electric Co.",                 "RIDGID®"),
    "ryobi":         ("Techtronic Industries Co. Ltd.",       "RYOBI®"),
    "metabo":        ("Metabo Corporation",                   "Metabo®"),
    "festool":       ("TTS Tooltechnic Systems AG & Co. KG",  "Festool®"),
    "flex":          ("Flex Tools USA LLC",                   "Flex®"),
    "hilti":         ("Hilti, Inc.",                          "Hilti®"),
    "porter cable":  ("Stanley Black & Decker, Inc.",         "PORTER-CABLE®"),
    "craftsman":     ("Stanley Black & Decker, Inc.",         "CRAFTSMAN®"),
    "stanley":       ("Stanley Black & Decker, Inc.",         "Stanley®"),
    "irwin":         ("Irwin Industrial Tool Company",        "IRWIN®"),
    "lenox":         ("Lenox Industrial Tools",               "LENOX®"),
    "norton":        ("Saint-Gobain Abrasives, Inc.",         "Norton®"),
    "3m":            ("3M Company",                           "3M™"),
    "mirka":         ("Mirka Abrasives Inc.",                 "Mirka®"),
    "freud":         ("Freud Inc.",                           "Freud®"),
    # Appliances
    "whirlpool":     ("Whirlpool Corporation",                "Whirlpool®"),
    "frigidaire":    ("Electrolux Home Products, Inc.",       "FRIGIDAIRE®"),
    "ge":            ("GE Appliances",                        "GE®"),
    "ge appliances": ("GE Appliances",                        "GE®"),
    "maytag":        ("Whirlpool Corporation",                "Maytag®"),
    "samsung":       ("Samsung Electronics America",          "Samsung®"),
    "lg":            ("LG Electronics USA, Inc.",             "LG®"),
    "bosch appliance":("BSH Home Appliances Corp.",           "BOSCH®"),
    "kitchenaid":    ("Whirlpool Corporation",                "KitchenAid®"),
    "amana":         ("Whirlpool Corporation",                "Amana®"),
    "electrolux":    ("Electrolux Home Products, Inc.",       "Electrolux®"),
    "speed queen":   ("Alliance Laundry Systems LLC",         "Speed Queen®"),
    "miele":         ("Miele, Inc.",                          "Miele®"),
    "thermador":     ("BSH Home Appliances Corp.",            "Thermador®"),
    "kenmore":       ("Transformco",                          "Kenmore®"),
    "rheem":         ("Rheem Manufacturing",                  "Rheem®"),
}
# Keep alias for desc-based hinting (backward compat)
_DESC_BRAND_HINTS = _BRAND_CANONICAL


def _normalise_key(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", s.lower().strip())


def _resolve_from_brand_string(brand_str: str) -> tuple:
    """Try to match a raw brand string against _BRAND_CANONICAL. Returns (mname, bname) or None."""
    if not brand_str:
        return None
    b = re.sub(r"[^a-z0-9 ]", "", brand_str.lower().strip())
    # Direct substring match
    for kw, (mname, bname) in _BRAND_CANONICAL.items():
        if kw in b:
            return mname, bname
    return None


def resolve_brand(row: pd.Series) -> dict:
    """
    Given a DataFrame row, return dict with:
        MANUFACTURER_NAME, BRAND_NAME, brand_confidence
    Resolution priority (highest → lowest):
      1. E1_Brand field (most specific, from input)
      2. DIB_Brand field
      3. Unilog_Brand field
      4. Exact match in MANUFACTURER_CORRECTIONS table
      5. Fuzzy match of manufacturer name
      6. Part_Desc keyword hints
      7. Fallback: raw manufacturer name
    """
    manuf_raw   = str(row.get("_manuf_name", "")).strip()
    desc        = str(row.get("Part_Desc", "")).lower()
    e1_brand    = str(row.get("E1_Brand",     "")).strip()
    dib_brand   = str(row.get("DIB_Brand",    "")).strip()
    unilog_brand= str(row.get("Unilog_Brand", "")).strip()

    # 1. E1_Brand — highest confidence source
    res = _resolve_from_brand_string(e1_brand)
    if res:
        return {"MANUFACTURER_NAME": res[0], "BRAND_NAME": res[1], "brand_confidence": 97}

    # 2. DIB_Brand
    res = _resolve_from_brand_string(dib_brand)
    if res:
        return {"MANUFACTURER_NAME": res[0], "BRAND_NAME": res[1], "brand_confidence": 92}

    # 3. Unilog_Brand
    res = _resolve_from_brand_string(unilog_brand)
    if res:
        return {"MANUFACTURER_NAME": res[0], "BRAND_NAME": res[1], "brand_confidence": 88}

    key = _normalise_key(manuf_raw)

    # 4. Exact match in correction table
    if key in _NORM_MAP:
        mname, bname = _NORM_MAP[key]
        return {"MANUFACTURER_NAME": mname, "BRAND_NAME": bname, "brand_confidence": 85}

    # 5. Fuzzy match of manufacturer name
    candidates = list(_NORM_MAP.keys())
    if candidates and fuzz.token_set_ratio is not None:
        match, score, _ = process.extractOne(key, candidates, scorer=fuzz.token_set_ratio)
        if score >= 80:
            mname, bname = _NORM_MAP[match]
            return {"MANUFACTURER_NAME": mname, "BRAND_NAME": bname, "brand_confidence": int(score)}

    # 6. Part_Desc keyword hint
    for kw, (mname, bname) in _DESC_BRAND_HINTS.items():
        if kw in desc:
            return {"MANUFACTURER_NAME": mname, "BRAND_NAME": bname, "brand_confidence": 75}

    # 7. Fallback
    fallback_brand = e1_brand or dib_brand or unilog_brand or manuf_raw or "Unknown"
    fallback_manuf = manuf_raw or "Unknown Manufacturer"
    return {
        "MANUFACTURER_NAME": fallback_manuf,
        "BRAND_NAME": fallback_brand,
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
