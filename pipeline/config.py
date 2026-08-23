"""
Pipeline Configuration
Paths, constants, and settings for the Unilog enrichment pipeline.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from pipeline directory
load_dotenv(Path(__file__).parent / ".env")

# ── Workspace root ──────────────────────────────────────────────────────────
# On Render: rootDir=pipeline, so __file__ parent IS the root
# Locally:   __file__ is pipeline/config.py, parent.parent is project root
_HERE = Path(__file__).parent          # always: the pipeline/ directory
_IS_RENDER = os.getenv("RENDER", "")   # Render sets this automatically

if _IS_RENDER:
    ROOT       = _HERE                  # pipeline/ IS the working dir on Render
    OUTPUT_DIR = _HERE / "output"
else:
    ROOT       = _HERE.parent           # local: project root is one level up
    OUTPUT_DIR = ROOT / "pipeline" / "output"

# ── Input / Output files ────────────────────────────────────────────────────
if _IS_RENDER:
    INPUT_CSV    = _HERE / "sample_input.csv"      # uploaded via API on Render
    GT_CSV       = _HERE / "sample_gt.csv"
else:
    INPUT_CSV    = ROOT / "Unihack_ Sample Dataset - Input.csv"
    GT_CSV       = ROOT / "Unihack_ Expected Output - Delivery Format.csv"

OUTPUT_CSV   = OUTPUT_DIR / "enriched_output.csv"
REVIEW_CSV   = OUTPUT_DIR / "review_queue.csv"
METRICS_JSON = OUTPUT_DIR / "metrics.json"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ── Groq API ─────────────────────────────────────────────────────────────────
GROQ_API_KEY   = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL     = os.getenv("GROQ_TEXT_MODEL_NAME", "qwen/qwen3.6-27b")
GROQ_FALLBACK  = os.getenv("GROQ_FALLBACK_MODEL_NAME", "openai/gpt-oss-20b")

# ── Pipeline behaviour ───────────────────────────────────────────────────────
BATCH_SIZE            = 20    # rows per Groq call
CONFIDENCE_THRESHOLD  = 70    # below this → review flag
MAX_RETRIES           = 2

# ── Placeholder values to treat as empty ────────────────────────────────────
PLACEHOLDERS = {
    "-- Unbranded --",
    "-- No Unilog Brand --",
    "-- No DIB Brand --",
    "-- Unbranded--",
    "--Unbranded--",
}

# ── Approved UOM abbreviations (subset of UOM Standards sheet) ───────────────
UOM_MAP = {
    "in":   ["inch", "inches", "IN", "IN.", "\"", "INCH", "Inch"],
    "ft":   ["feet", "foot", "FT", "FT.", "FEET", "Foot"],
    "mm":   ["MM", "millimeter", "millimetre", "millimeters"],
    "cm":   ["CM", "centimeter", "centimetre"],
    "m":    ["meter", "metre", "meters", "metres", "MTR"],
    "lb":   ["lbs", "LB", "LBS", "pound", "pounds", "Lb"],
    "oz":   ["OZ", "ounce", "ounces"],
    "kg":   ["KG", "kilogram", "kilograms"],
    "g":    ["GM", "gram", "grams", "GR"],
    "V":    ["volt", "volts", "VOLT", "Volt"],
    "A":    ["amp", "amps", "AMP", "AMPS", "ampere"],
    "W":    ["watt", "watts", "WATT"],
    "rpm":  ["RPM"],
    "dBA":  ["dba", "DBA", "db", "DB"],
    "GA":   ["ga", "gauge", "Ga", "gage"],
    "pc":   ["PC", "pcs", "PCS", "piece", "pieces"],
}

# ── Decimal → Fraction lookup (Decimal_Fraction.xlsx values) ─────────────────
DECIMAL_TO_FRACTION = {
    0.015625: "1/64",  0.03125: "1/32",  0.046875: "3/64",  0.0625: "1/16",
    0.078125: "5/64",  0.09375: "3/32",  0.109375: "7/64",  0.125: "1/8",
    0.140625: "9/64",  0.15625: "5/32",  0.171875: "11/64", 0.1875: "3/16",
    0.203125: "13/64", 0.21875: "7/32",  0.234375: "15/64", 0.25: "1/4",
    0.265625: "17/64", 0.28125: "9/32",  0.296875: "19/64", 0.3125: "5/16",
    0.328125: "21/64", 0.34375: "11/32", 0.359375: "23/64", 0.375: "3/8",
    0.390625: "25/64", 0.40625: "13/32", 0.421875: "27/64", 0.4375: "7/16",
    0.453125: "29/64", 0.46875: "15/32", 0.484375: "31/64", 0.5: "1/2",
    0.515625: "33/64", 0.53125: "17/32", 0.546875: "35/64", 0.5625: "9/16",
    0.578125: "37/64", 0.59375: "19/32", 0.609375: "39/64", 0.625: "5/8",
    0.640625: "41/64", 0.65625: "21/32", 0.671875: "43/64", 0.6875: "11/16",
    0.703125: "45/64", 0.71875: "23/32", 0.734375: "47/64", 0.75: "3/4",
    0.765625: "49/64", 0.78125: "25/32", 0.796875: "51/64", 0.8125: "13/16",
    0.828125: "53/64", 0.84375: "27/32", 0.859375: "55/64", 0.875: "7/8",
    0.890625: "57/64", 0.90625: "29/32", 0.921875: "59/64", 0.9375: "15/16",
    0.953125: "61/64", 0.96875: "31/32", 0.984375: "63/64",
}

# ── Known manufacturer name corrections ─────────────────────────────────────
MANUFACTURER_CORRECTIONS = {
    "freud inc":              ("Freud Inc.", "Diablo®"),
    "jam industrial supply":  ("Jam Industrial Supply LLC", "3M™"),
    "mirka abrasives inc":    ("Mirka Abrasives Inc.", "Mirka®"),
    "milwaukee accessory":    ("Milwaukee Tool", "Milwaukee®"),
    "black & decker/dewlt":   ("Stanley Black & Decker, Inc.", "DEWALT®"),
    "makita usa inc":         ("Makita U.S.A., Inc.", "Makita®"),
    "kreg tool company":      ("Kreg Tool Company", "Kreg®"),
    "king canada inc":        ("King Canada Inc.", "King Canada"),
    "national nail corp":     ("National Nail Corp.", "Paslode®"),
    "vessel tools usa inc":   ("Vessel Tools USA Inc.", "Vessel®"),
    "appliance dealers cooperative": ("Rheem Manufacturing", "FRIGIDAIRE®"),
    "3 m co":                 ("3M Company", "3M™"),
    "emseal joint systems ltd": ("Emseal Joint Systems Ltd.", "Emseal"),
    "v & v appliance parts inc": ("V & V Appliance Parts Inc.", "V & V"),
    "wera tools na inc":      ("Wera Tools NA Inc.", "Wera®"),
    "rees cast stone company": ("Rees Cast Stone Company", "Rees"),
}

# ── Category keyword → classpath mappings ───────────────────────────────────
CATEGORY_KEYWORDS = {
    "sanding belt":       "Abrasives & Finishing>Abrasive Rolls & Sheets>Sanding Belts",
    "sanding sponge":     "Abrasives & Finishing>Sponges & Pads>Sanding Sponges",
    "stikit film":        "Abrasives & Finishing>Abrasive Discs>Hook & Loop Discs",
    "cubitron":           "Abrasives & Finishing>Abrasive Discs>Hook & Loop Discs",
    "abranet":            "Abrasives & Finishing>Abrasive Discs>Hook & Loop Discs",
    "hiolit":             "Abrasives & Finishing>Abrasive Discs>Hook & Loop Discs",
    "cut-off disc":       "Abrasives & Finishing>Abrasive Wheels>Cut-Off Wheels",
    "cut off disc":       "Abrasives & Finishing>Abrasive Wheels>Cut-Off Wheels",
    "cut off wheel":      "Abrasives & Finishing>Abrasive Wheels>Cut-Off Wheels",
    "cut and grind":      "Abrasives & Finishing>Abrasive Wheels>Cut-Off Wheels",
    "cut n grind":        "Abrasives & Finishing>Abrasive Wheels>Cut-Off Wheels",
    "grinding disc":      "Abrasives & Finishing>Abrasive Wheels>Grinding Wheels",
    "grinding wheel":     "Abrasives & Finishing>Abrasive Wheels>Grinding Wheels",
    "flap disc":          "Abrasives & Finishing>Abrasive Wheels>Flap Discs",
    "wire wheel":         "Abrasives & Finishing>Abrasive Wheels>Wire Wheels",
    "sanding disc":       "Abrasives & Finishing>Abrasive Discs>Fiber Discs",
    "drill":              "Power Tools>Drills>Cordless Drills",
    "hammer drill":       "Power Tools>Drills>Hammer Drills",
    "impact driver":      "Power Tools>Impact Drivers & Wrenches>Cordless Impact Drivers",
    "impact wrench":      "Power Tools>Impact Drivers & Wrenches>Cordless Impact Wrenches",
    "circular saw":       "Power Tools>Saws>Circular Saws",
    "reciprocating saw":  "Power Tools>Saws>Reciprocating Saws",
    "jig saw":            "Power Tools>Saws>Jig Saws",
    "miter saw":          "Power Tools>Saws>Miter Saws",
    "table saw":          "Power Tools>Saws>Table Saws",
    "band saw":           "Power Tools>Saws>Band Saws",
    "track saw":          "Power Tools>Saws>Track Saws",
    "oscillating":        "Power Tools>Oscillating Tools>Cordless Oscillating Tools",
    "rotary tool":        "Power Tools>Rotary Tools>Rotary Tool Kits",
    "grinder":            "Power Tools>Grinders>Angle Grinders",
    "angle grinder":      "Power Tools>Grinders>Angle Grinders",
    "sander":             "Power Tools>Sanders>Random Orbit Sanders",
    "random orbit":       "Power Tools>Sanders>Random Orbit Sanders",
    "belt sander":        "Power Tools>Sanders>Belt Sanders",
    "detail sander":      "Power Tools>Sanders>Detail Sanders",
    "router":             "Power Tools>Routers>Plunge Routers",
    "planer":             "Power Tools>Planers>Handheld Planers",
    "nailer":             "Power Tools>Nailers & Staplers>Cordless Nailers",
    "brad nailer":        "Power Tools>Nailers & Staplers>Brad Nailers",
    "finish nailer":      "Power Tools>Nailers & Staplers>Finish Nailers",
    "framing nailer":     "Power Tools>Nailers & Staplers>Framing Nailers",
    "roofing nailer":     "Power Tools>Nailers & Staplers>Roofing Nailers",
    "stapler":            "Power Tools>Nailers & Staplers>Staplers",
    "blower":             "Power Tools>Outdoor Power Equipment>Blowers",
    "hedge trimmer":      "Power Tools>Outdoor Power Equipment>Hedge Trimmers",
    "trimmer":            "Power Tools>Trimmers>Cordless Trimmers",
    "chainsaw":           "Power Tools>Outdoor Power Equipment>Chainsaws",
    "vacuum":             "Power Tools>Vacuums>Wet/Dry Vacuums",
    "jobsite speaker":    "Power Tools>Accessories>Jobsite Speakers",
    "bluetooth speaker":  "Power Tools>Accessories>Jobsite Speakers",
    "drill press":        "Power Tools>Drills>Drill Presses",
    "screwdriver":        "Hand Tools>Screwdrivers>Bit Sets",
    "autofeed screwdriver": "Power Tools>Screwdrivers>Auto-Feed Screwdrivers",
    "drive bit":          "Power Tools>Accessories>Screwdriver Bits",
    "phillips":           "Power Tools>Accessories>Screwdriver Bits",
    "torx":               "Power Tools>Accessories>Screwdriver Bits",
    "square drive":       "Power Tools>Accessories>Screwdriver Bits",
    "saw blade":          "Power Tools>Accessories>Saw Blades",
    "hole saw":           "Power Tools>Accessories>Hole Saws",
    "drill bit":          "Power Tools>Accessories>Drill Bits",
    "router bit":         "Power Tools>Accessories>Router Bits",
    "blade":              "Power Tools>Accessories>Saw Blades",
    "battery":            "Power Tools>Batteries & Chargers>Batteries",
    "charger":            "Power Tools>Batteries & Chargers>Chargers",
    "worklight":          "Power Tools>Lighting>LED Work Lights",
    "work light":         "Power Tools>Lighting>LED Work Lights",
    "flashlight":         "Power Tools>Lighting>Flashlights",
    "tool bag":           "Power Tools>Storage>Tool Bags",
    "tool box":           "Power Tools>Storage>Tool Boxes",
    "combo kit":          "Power Tools>Combo Kits>Cordless Combo Kits",
    "dishwasher":         "Appliances & Consumer Electronics>Kitchen Appliances>Built-In Dishwashers",
    "dryer":              "Appliances & Consumer Electronics>Laundry Appliances>Dryers",
    "washer":             "Appliances & Consumer Electronics>Laundry Appliances>Washers",
    "refrigerator":       "Appliances & Consumer Electronics>Kitchen Appliances>Refrigerators",
    "laundry center":     "Appliances & Consumer Electronics>Laundry Appliances>Washers",
    "elect tape":         "Adhesives & Tapes>Tapes>Electrical Tapes",
    "tape":               "Adhesives & Tapes>Tapes>Specialty Tapes",
    "mortar":             "Building Materials>Concrete & Masonry>Mortar",
    "heater kit":         "Appliances & Consumer Electronics>Appliance Parts>Heater Kits",
    "kneeling pad":       "Safety & PPE>Ergonomics>Kneeling Pads",
    "gauge":              "Hand Tools>Measuring Tools>Gauges",
    "coupling":           "Plumbing>Pipe & Fittings>Couplings",
    "fitting":            "Plumbing>Pipe & Fittings>Fittings",
    "faucet":             "Plumbing>Faucets & Fixtures>Kitchen Faucets",
    "valve":              "Plumbing>Valves>Ball Valves",
}

# ── Output schema: 252-column header list ───────────────────────────────────
OUTPUT_COLUMNS = [
    "MFR URL","Ref URL 1","Ref URL 2","Ref URL 3","Ref URL 4","Ref URL 5",
    "PART_NUMBER","Dept","Class","Fine","SKU - MY_PART_NUMBER","Mfg_Part_Num",
    "Part_Desc","E1_Brand","Unilog_Brand","DIB_Brand","Part_Manuf",
    "MANUFACTURER_NAME","BRAND_NAME","TRADE_NAME","MANUFACTURER_PART_NUMBER",
    "ALTERNATE_PART_NUMBER","Classpath","MOBILE_DESC","INVOICE_DESC",
    "SHORT_DESC","LONG_DESC1","RETAIL_DESC","MARKETING_DESCRIPTION",
] + [f"ITEM_FEATURES_{i}" for i in range(1, 21)] + [
    "With","Standard/Approvals","Prop 65","Application","Includes","Product Name",
]
for i in range(1, 51):
    OUTPUT_COLUMNS += [f"ATTRIBUTE_LABEL {i}", f"ATTRIBUTE_VALUE {i}", f"ATTRIBUTE_UOM {i}"]

OUTPUT_COLUMNS += [
    "UPC","EAN","GTIN","UNSPSC","Warranty","List Price","Selling Qty","Selling UOM",
    "Standard Packaging Information","LENGTH","LENGTH_UOM","HEIGHT","HEIGHT_UOM",
    "WIDTH","WIDTH_UOM","WEIGHT","WEIGHT_UOM","VOLUME","VOLUME_UOM",
    "Product Image","Alternate Image 1","Alternate Image 2","Alternate Image 3",
    "Alternate Image 4","SDS","SDS_1","Warranty Information","Catalog",
    "Specification Sheet","Instruction/Installation Manual","Service Manual",
    "Owners/User Manual","Line Drawing","MTR","RoHS","Full Engineering Drawing",
    "Energy Star Guide","Technical Bulletin","Submittal","Compatibility Chart",
    "Size Chart","Product Label/Insert","Video Link","Video Link 1",
    "Country Of Origin","Discontinued","Actual Image (Yes/No)",
]
