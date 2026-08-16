"""
Stage 1 — Input Parsing & Cleaning
Reads the raw 1000-row CSV, strips placeholders, normalises manufacturer field.
"""
import re
import pandas as pd
from config import INPUT_CSV, PLACEHOLDERS


def clean_placeholder(val: str) -> str:
    """Return empty string if value is a known placeholder, else strip whitespace."""
    if pd.isna(val):
        return ""
    val = str(val).strip()
    return "" if val in PLACEHOLDERS else val


def parse_manufacturer(raw: str):
    """
    'Freud Inc (2435)'  →  name='Freud Inc', code='2435'
    'Jam Industrial Supply LLC (JAMIN)' → name='...', code='JAMIN'
    """
    if not raw:
        return "", ""
    m = re.match(r"^(.+?)\s*\(([^)]+)\)\s*$", raw.strip())
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return raw.strip(), ""


def load_and_clean(path=INPUT_CSV) -> pd.DataFrame:
    df = pd.read_csv(path, dtype=str, encoding="utf-8-sig")
    df.columns = df.columns.str.strip()

    # Strip placeholders
    for col in ["E1_Brand", "Unilog_Brand", "DIB_Brand"]:
        df[col] = df[col].apply(clean_placeholder)

    # Parse manufacturer
    df["_manuf_raw"] = df["Part_Manuf"].fillna("").str.strip()
    df[["_manuf_name", "_manuf_code"]] = df["_manuf_raw"].apply(
        lambda x: pd.Series(parse_manufacturer(x))
    )

    # Deduplicate on MPN (keep first occurrence)
    before = len(df)
    df = df.drop_duplicates(subset=["Mfg_Part_Num"], keep="first").reset_index(drop=True)
    after = len(df)
    dupes = before - after

    print(f"[Stage 1] Loaded {before} rows → {after} unique MPNs ({dupes} duplicates removed)")
    return df


if __name__ == "__main__":
    df = load_and_clean()
    print(df[["Mfg_Part_Num", "Part_Desc", "_manuf_name", "_manuf_code"]].head(10).to_string())
