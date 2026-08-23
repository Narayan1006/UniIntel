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
                # Strip <think>...</think> blocks from reasoning models (Qwen, o1, etc.)
                import re as _re
                text = _re.sub(r'<think>.*?</think>', '', text, flags=_re.DOTALL).strip()
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


# ── Unilog Dept > Class > Fine mapping ──────────────────────────────────────
# Maps our AI classpath strings to the official Unilog 3-level hierarchy.
# Format: classpath_substring -> (Dept, Class, Fine)
_UNILOG_DEPT_MAP = [
    # Appliances
    ("Dishwasher",                  ("Appliances",               "Large Appliances",   "Dishwashers")),
    ("Dryer",                       ("Appliances",               "Laundry Appliances",  "Dryers")),
    ("Washer",                      ("Appliances",               "Laundry Appliances",  "Washers")),
    ("Refrigerator",                ("Appliances",               "Large Appliances",   "Refrigerators")),
    ("Range",                       ("Appliances",               "Large Appliances",   "Ranges")),
    ("Oven",                        ("Appliances",               "Large Appliances",   "Ovens")),
    ("Microwave",                   ("Appliances",               "Small Appliances",   "Microwaves")),
    ("Laundry Appliance",           ("Appliances",               "Laundry Appliances",  "Laundry Centers")),
    ("Kitchen Appliance",           ("Appliances",               "Large Appliances",   "Kitchen Appliances")),
    ("Heater Kit",                  ("Appliances",               "Appliance Parts",    "Heater Kits")),
    ("Appliance",                   ("Appliances",               "Large Appliances",   "Appliances")),
    # Power Tools
    ("Cordless Drill",              ("Power Tools",              "Drills",             "Cordless Drills")),
    ("Hammer Drill",                ("Power Tools",              "Drills",             "Hammer Drills")),
    ("Drill Press",                 ("Power Tools",              "Drills",             "Drill Presses")),
    ("Drill",                       ("Power Tools",              "Drills",             "Cordless Drills")),
    ("Cordless Impact Driver",      ("Power Tools",              "Impact Drivers & Wrenches", "Cordless Impact Drivers")),
    ("Impact Driver",               ("Power Tools",              "Impact Drivers & Wrenches", "Cordless Impact Drivers")),
    ("Impact Wrench",               ("Power Tools",              "Impact Drivers & Wrenches", "Cordless Impact Wrenches")),
    ("Circular Saw",                ("Power Tools",              "Saws",               "Circular Saws")),
    ("Miter Saw",                   ("Power Tools",              "Saws",               "Miter Saws")),
    ("Reciprocating Saw",           ("Power Tools",              "Saws",               "Reciprocating Saws")),
    ("Jig Saw",                     ("Power Tools",              "Saws",               "Jig Saws")),
    ("Table Saw",                   ("Power Tools",              "Saws",               "Table Saws")),
    ("Track Saw",                   ("Power Tools",              "Saws",               "Track Saws")),
    ("Band Saw",                    ("Power Tools",              "Saws",               "Band Saws")),
    ("Angle Grinder",               ("Power Tools",              "Grinders",           "Angle Grinders")),
    ("Grinder",                     ("Power Tools",              "Grinders",           "Angle Grinders")),
    ("Random Orbit Sander",         ("Power Tools",              "Sanders",            "Random Orbit Sanders")),
    ("Belt Sander",                 ("Power Tools",              "Sanders",            "Belt Sanders")),
    ("Detail Sander",               ("Power Tools",              "Sanders",            "Detail Sanders")),
    ("Sander",                      ("Power Tools",              "Sanders",            "Sanders")),
    ("Brad Nailer",                 ("Power Tools",              "Nailers & Staplers", "Brad Nailers")),
    ("Finish Nailer",               ("Power Tools",              "Nailers & Staplers", "Finish Nailers")),
    ("Framing Nailer",              ("Power Tools",              "Nailers & Staplers", "Framing Nailers")),
    ("Roofing Nailer",              ("Power Tools",              "Nailers & Staplers", "Roofing Nailers")),
    ("Nailer",                      ("Power Tools",              "Nailers & Staplers", "Cordless Nailers")),
    ("Stapler",                     ("Power Tools",              "Nailers & Staplers", "Staplers")),
    ("Oscillating Tool",            ("Power Tools",              "Oscillating Tools",  "Cordless Oscillating Tools")),
    ("Router",                      ("Power Tools",              "Routers",            "Plunge Routers")),
    ("Planer",                      ("Power Tools",              "Planers",            "Handheld Planers")),
    ("Rotary Tool",                 ("Power Tools",              "Rotary Tools",       "Rotary Tool Kits")),
    ("Vacuum",                      ("Power Tools",              "Vacuums",            "Wet/Dry Vacuums")),
    ("Work Light",                  ("Power Tools",              "Lighting",           "LED Work Lights")),
    ("Flashlight",                  ("Power Tools",              "Lighting",           "Flashlights")),
    ("Combo Kit",                   ("Power Tools",              "Combo Kits",         "Cordless Combo Kits")),
    ("Battery",                     ("Power Tools",              "Batteries & Chargers","Batteries")),
    ("Charger",                     ("Power Tools",              "Batteries & Chargers","Chargers")),
    ("Screwdriver Bit",             ("Power Tools",              "Accessories",        "Screwdriver Bits")),
    ("Saw Blade",                   ("Power Tools",              "Accessories",        "Saw Blades")),
    ("Hole Saw",                    ("Power Tools",              "Accessories",        "Hole Saws")),
    ("Drill Bit",                   ("Power Tools",              "Accessories",        "Drill Bits")),
    ("Router Bit",                  ("Power Tools",              "Accessories",        "Router Bits")),
    ("Blade",                       ("Power Tools",              "Accessories",        "Saw Blades")),
    ("Tool Bag",                    ("Power Tools",              "Storage",            "Tool Bags")),
    ("Tool Box",                    ("Power Tools",              "Storage",            "Tool Boxes")),
    ("Jobsite Speaker",             ("Power Tools",              "Accessories",        "Jobsite Speakers")),
    ("Blower",                      ("Power Tools",              "Outdoor Power Equipment", "Blowers")),
    ("Hedge Trimmer",               ("Power Tools",              "Outdoor Power Equipment", "Hedge Trimmers")),
    ("Chainsaw",                    ("Power Tools",              "Outdoor Power Equipment", "Chainsaws")),
    ("Trimmer",                     ("Power Tools",              "Trimmers",           "Cordless Trimmers")),
    ("Auto-Feed Screwdriver",       ("Power Tools",              "Screwdrivers",       "Auto-Feed Screwdrivers")),
    # Abrasives
    ("Cut-Off Wheel",               ("Abrasives & Finishing",    "Abrasive Wheels",    "Cut-Off Wheels")),
    ("Grinding Wheel",              ("Abrasives & Finishing",    "Abrasive Wheels",    "Grinding Wheels")),
    ("Flap Disc",                   ("Abrasives & Finishing",    "Abrasive Wheels",    "Flap Discs")),
    ("Wire Wheel",                  ("Abrasives & Finishing",    "Abrasive Wheels",    "Wire Wheels")),
    ("Sanding Belt",                ("Abrasives & Finishing",    "Abrasive Rolls & Sheets", "Sanding Belts")),
    ("Hook & Loop Disc",            ("Abrasives & Finishing",    "Abrasive Discs",     "Hook & Loop Discs")),
    ("Fiber Disc",                  ("Abrasives & Finishing",    "Abrasive Discs",     "Fiber Discs")),
    ("Sanding Sponge",              ("Abrasives & Finishing",    "Sponges & Pads",     "Sanding Sponges")),
    ("Abrasive Disc",               ("Abrasives & Finishing",    "Abrasive Discs",     "Abrasive Discs")),
    ("Abrasive Roll",               ("Abrasives & Finishing",    "Abrasive Rolls & Sheets", "Abrasive Rolls")),
    ("Abrasive",                    ("Abrasives & Finishing",    "Abrasive Wheels",    "Abrasive Wheels")),
    # Hand Tools
    ("Screwdriver",                 ("Hand Tools",               "Screwdrivers",       "Bit Sets")),
    ("Gauge",                       ("Hand Tools",               "Measuring Tools",    "Gauges")),
    # Adhesives
    ("Electrical Tape",             ("Adhesives & Tapes",        "Tapes",              "Electrical Tapes")),
    ("Specialty Tape",              ("Adhesives & Tapes",        "Tapes",              "Specialty Tapes")),
    ("Tape",                        ("Adhesives & Tapes",        "Tapes",              "Specialty Tapes")),
    # Building
    ("Mortar",                      ("Building Materials",       "Concrete & Masonry", "Mortar")),
    # Plumbing
    ("Coupling",                    ("Plumbing",                 "Pipe & Fittings",    "Couplings")),
    ("Fitting",                     ("Plumbing",                 "Pipe & Fittings",    "Fittings")),
    ("Kitchen Faucet",              ("Plumbing",                 "Faucets & Fixtures", "Kitchen Faucets")),
    ("Ball Valve",                  ("Plumbing",                 "Valves",             "Ball Valves")),
    ("Valve",                       ("Plumbing",                 "Valves",             "Valves")),
    # Safety
    ("Kneeling Pad",                ("Safety & PPE",             "Ergonomics",         "Kneeling Pads")),
]


def _dept_class_fine(classpath: str) -> tuple:
    """Map a classpath string to (Dept, Class, Fine) using the Unilog taxonomy map."""
    if not classpath or classpath == "Unclassified":
        return "", "", ""
    # Try each keyword in order (longer/more specific first)
    for keyword, (dept, cls, fine) in _UNILOG_DEPT_MAP:
        if keyword.lower() in classpath.lower():
            return dept, cls, fine
    # Fallback: split the classpath directly
    parts = [p.strip() for p in classpath.split(">")]
    parts += ["", "", ""]
    return parts[0], parts[1], parts[2]


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
        print("  [Stage 3] No Groq key -- rows set to 'Unclassified'.")
        for item in to_llm:
            classpaths[item["idx"]] = "Unclassified"

    df["Classpath"]            = classpaths
    df["classpath_confidence"] = class_conf

    # Apply Unilog Dept > Class > Fine mapping
    dept_list, class_list, fine_list = [], [], []
    for cp in classpaths:
        d, c, f = _dept_class_fine(cp)
        dept_list.append(d)
        class_list.append(c)
        fine_list.append(f)

    df["Dept"]  = dept_list
    df["Class"] = class_list
    df["Fine"]  = fine_list

    classified = (df["Classpath"] != "Unclassified").sum()
    dept_filled = sum(1 for d in dept_list if d)
    print(f"[Stage 3] Total classified: {classified}/{len(df)} rows. Dept/Class/Fine filled: {dept_filled}/{len(df)}.")
    return df


if __name__ == "__main__":
    from stage1_ingest import load_and_clean
    from stage2_brand_resolve import resolve_all_brands
    df = load_and_clean()
    df = resolve_all_brands(df)
    df = classify_all(df)
    print(df[["Mfg_Part_Num", "Dept", "Class", "Fine", "classpath_confidence"]].head(20).to_string())
